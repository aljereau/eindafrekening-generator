"""
RYAN-V2: Agentic Pipeline
Intent Classifier Module

Uses a tiny LLM call to classify user questions into structured intents.
This is the ONLY layer that requires an LLM - everything else is deterministic.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import logging
from anthropic import Anthropic
from openai import OpenAI

logger = logging.getLogger("ryan_intent")


# =============================================================================
# INTENT DEFINITIONS
# =============================================================================

@dataclass
class IntentDefinition:
    """Definition of a queryable intent."""
    name: str
    description: str
    view_or_table: str
    default_filters: Optional[str] = None
    supports_date_range: bool = False
    supports_search: bool = False
    default_profile: str = "ops"


# All supported intents with their configurations
INTENTS: Dict[str, IntentDefinition] = {
    # Properties
    "house_list": IntentDefinition(
        name="house_list",
        description="List of properties/houses with specifications",
        view_or_table="v_alle_huizen",
        supports_search=True,
        default_profile="ops"
    ),
    "house_profitability": IntentDefinition(
        name="house_profitability",
        description="Property profitability and margin analysis",
        view_or_table="view_house_profitability",
        default_profile="finance"
    ),
    
    # Bookings & Lifecycle
    "booking_list": IntentDefinition(
        name="booking_list",
        description="List of bookings with house and client details",
        view_or_table="v_bookings_extended",
        supports_date_range=True,
        supports_search=True,
        default_profile="ops"
    ),
    "checkout_list": IntentDefinition(
        name="checkout_list",
        description="Upcoming checkouts/move-outs",
        view_or_table="v_bookings_extended",
        default_filters="checkout_datum >= date('now')",
        supports_date_range=True,
        default_profile="ops"
    ),
    "checkin_list": IntentDefinition(
        name="checkin_list",
        description="Upcoming check-ins/move-ins",
        view_or_table="v_bookings_extended",
        default_filters="checkin_datum >= date('now')",
        supports_date_range=True,
        default_profile="ops"
    ),
    
    # Operations / In-Uit-Check
    "active_cycles": IntentDefinition(
        name="active_cycles",
        description="Active check-out/cleaning/check-in cycles",
        view_or_table="v_actieve_cycli",
        default_profile="ops"
    ),
    "pending_actions": IntentDefinition(
        name="pending_actions",
        description="Pending actions (inspections, cleaning, handovers)",
        view_or_table="v_open_acties",
        default_profile="ops"
    ),
    "planning_priorities": IntentDefinition(
        name="planning_priorities",
        description="AI-recommended priority actions",
        view_or_table="v_planning_inputs",
        default_profile="ops"
    ),
    
    # Inspections
    "inspection_schedule": IntentDefinition(
        name="inspection_schedule",
        description="Upcoming and overdue inspections",
        view_or_table="v_inspections_pipeline",
        supports_date_range=True,
        default_profile="ops"
    ),
    
    # Finance
    "settlement_history": IntentDefinition(
        name="settlement_history",
        description="Eindafrekening/settlement history",
        view_or_table="v_eindafrekeningen_extended",
        supports_date_range=True,
        supports_search=True,
        default_profile="finance"
    ),
    "contract_overview": IntentDefinition(
        name="contract_overview",
        description="Active verhuur and inhuur contracts",
        view_or_table="v_contracts_overview",
        default_profile="finance"
    ),
    "pricing_overview": IntentDefinition(
        name="pricing_overview",
        description="Current rent prices and rates",
        view_or_table="view_latest_pricing",
        default_profile="finance"
    ),
    
    # Clients
    "client_list": IntentDefinition(
        name="client_list",
        description="List of clients/tenants",
        view_or_table="relaties",
        supports_search=True,
        default_profile="ops"
    ),
    "client_scorecard": IntentDefinition(
        name="client_scorecard",
        description="Client performance and payment history",
        view_or_table="view_client_scorecard",
        default_profile="finance"
    ),
    
    # Occupancy
    "occupancy_summary": IntentDefinition(
        name="occupancy_summary",
        description="Occupancy status per house",
        view_or_table="v_occupancy_summary",
        default_profile="ops"
    ),
    
    # Cleaning
    "cleaning_analysis": IntentDefinition(
        name="cleaning_analysis",
        description="Cleaning hours variance analysis",
        view_or_table="v_schoonmaak_variance",
        default_profile="ops"
    ),
    
    # FALLBACK: For questions that don't match any template
    "general_query": IntentDefinition(
        name="general_query",
        description="Ad-hoc/complex question requiring LLM SQL generation",
        view_or_table="",  # Will be determined by LLM
        default_profile="ops"
    ),
    
    # SYSTEM: For greetings/identity/chitchat
    "chitchat": IntentDefinition(
        name="chitchat",
        description="Greetings, identity questions, or non-data inputs",
        view_or_table="",
        default_profile="ops"
    ),
}


# =============================================================================
# CLASSIFICATION RESULT
# =============================================================================

@dataclass
class ClassificationResult:
    """Result of intent classification."""
    intent: str
    params: Dict[str, Any]
    column_profile: str
    confidence: float
    original_question: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "params": self.params,
            "column_profile": self.column_profile,
            "confidence": self.confidence
        }


# =============================================================================
# CLASSIFIER
# =============================================================================

# Improved prompt for intent classification (with examples)
CLASSIFICATION_PROMPT = """Je classificeert vragen over vastgoedbeheer naar gestructureerde intents.

BESCHIKBARE INTENTS:
{intent_list}

KEYWORD HINTS (gebruik dit om de juiste intent te kiezen):
- "huizen", "woningen", "panden", "adressen" → house_list
- "checkouts", "uitcheck", "verhuizen uit", "einde huur" → checkout_list  
- "checkins", "incheck", "nieuwe huurder", "komt wonen" → checkin_list
- "boekingen", "reserveringen", "huurperiodes" → booking_list
- "winstgevend", "rendement", "marge", "omzet" → house_profitability
- "inspecties", "voorinspectie", "eindinspectie" → inspection_schedule
- "klanten", "huurders", "relaties" → client_list
- "contracten", "verhuur", "inhuur" → contract_overview
- "schoonmaak", "cleaning" → cleaning_analysis
- "bezetting", "leegstand", "occupancy" → occupancy_summary
- "eindafrekening", "settlement", "afrekening" → settlement_history
- "prijzen", "huur", "tarieven" → pricing_overview
- "cycli", "in-uit-check", "turnover" → active_cycles
- "acties", "taken", "to-do" → pending_actions

VOORBEELDEN:
- "Toon alle huizen" → {{"intent": "house_list", "params": {{}}, "column_profile": "ops"}}
- "Welke checkouts zijn er in Q1 2026?" → {{"intent": "checkout_list", "params": {{"date_from": "2026-01-01", "date_to": "2026-03-31"}}, "column_profile": "ops"}}
- "Huizen in Amsterdam" → {{"intent": "house_list", "params": {{"search": "Amsterdam"}}, "column_profile": "ops"}}
- "Wat zijn de winstgevende panden?" → {{"intent": "house_profitability", "params": {{}}, "column_profile": "finance"}}
- "Toon alle klanten" → {{"intent": "client_list", "params": {{}}, "column_profile": "ops"}}
- "Hallo, wie ben jij?" → {{"intent": "chitchat", "params": {{}}, "column_profile": "ops"}}
- "Bedankt!" → {{"intent": "chitchat", "params": {{}}, "column_profile": "ops"}}

OUTPUT (alleen JSON, geen uitleg):
{{"intent": "<intent_name>", "params": {{"date_from": "YYYY-MM-DD", "date_to": "YYYY-MM-DD", "search": "<term>"}}, "column_profile": "ops|finance"}}

REGELS:
1. Kies ALTIJD een specifieke intent als keywords matchen - NIET general_query
2. Datums: Q1=jan-mrt, Q2=apr-jun, Q3=jul-sep, Q4=okt-dec
3. column_profile: "finance" alleen voor winst/geld vragen, anders "ops"
4. general_query ALLEEN voor complexe vragen die geen enkele keyword matchen voor DATA.
5. Gebruik "chitchat" voor:
   - Begroetingen ("hallo", "hoi", "goedemorgen")
   - Bedankjes ("dankjewel", "thanks")
   - Vragen over identiteit ("wie ben je", "wat kun je")
   - Korte interacties zonder duidelijke datavraag
   - NIET SQL genereren voor deze inputs!

VRAAG: {question}"""


class IntentClassifier:
    """Classifies user questions into structured intents using minimal LLM."""
    
    def __init__(self, provider: str = None, model: str = None):
        # Use user-selected model from settings if not explicitly provided
        if provider is None or model is None:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from ryan_v2.settings_service import get_active_model
            active = get_active_model()
            model_id = active["id"]  # Format: "provider:model"
            if ":" in model_id:
                provider, model = model_id.split(":", 1)
            else:
                provider = "anthropic"
                model = model_id
        
        self.provider = provider
        self.model = model
        self._intent_list_cache = None
    
    def _get_intent_list(self) -> str:
        """Get formatted list of intents for the prompt."""
        if self._intent_list_cache:
            return self._intent_list_cache
        
        lines = []
        for name, defn in INTENTS.items():
            if name != "general_query":
                lines.append(f"- {name}: {defn.description}")
        lines.append("- general_query: Complex/custom question not matching above")
        
        self._intent_list_cache = "\n".join(lines)
        return self._intent_list_cache
    
    def _try_keyword_match(self, q: str) -> Optional[ClassificationResult]:
        """Deterministic keyword matching - no LLM needed."""
        q_lower = q.lower()
        
        # 1. Check for Chitchat FIRST
        chitchat_keywords = ["hallo", "hoi", "goedemorgen", "goedenavond", "thanks", "bedankt", "dankjewel", "wie ben je", "wat ben jij", "wat kun je", "sup", "yo", "hey"]
        if any(kw in q_lower for kw in chitchat_keywords) and len(q.split()) < 5:
            # Short greeting/thanks = chitchat
            return ClassificationResult(
                intent="chitchat",
                params={},
                column_profile="ops",
                confidence=1.0,
                original_question=q
            )

        # 2. Check for Data Intents
        rules = [
            (["checkout", "uitcheck", "verhuizen uit", "vertrekken"], "checkout_list"),
            (["checkin", "incheck", "komt wonen", "nieuwe huurder"], "checkin_list"),
            (["winstgevend", "rendement", "marge", "profit", "winst"], "house_profitability"),
            (["inspectie", "voorinspectie", "eindinspectie"], "inspection_schedule"),
            (["huizen", "woningen", "panden", "properties"], "house_list"),
            (["klant", "huurder", "relatie", "tenants"], "client_list"),
            (["contract", "huurovereenkomst"], "contract_overview"),
            (["schoonmaak", "cleaning", "poetsen"], "cleaning_analysis"),
            (["bezetting", "leegstand", "occupancy"], "occupancy_summary"),
            (["eindafrekening", "settlement", "borg terug"], "settlement_history"),
            (["prijs", "huurprijs", "tarief"], "pricing_overview"),
            (["cyclus", "cycli", "turnover"], "active_cycles"),
            (["actie", "taak", "todo", "te doen"], "pending_actions"),
        ]
        
        best_intent = None
        
        for keywords, intent in rules:
            if any(kw in q_lower for kw in keywords):
                # Simple rule: if specific keywords found, pick that intent
                # Note: This is greedy. The LLM is smarter for ambiguity.
                # But for unambiguous words like "checkout", it's safe.
                best_intent = intent
                break
        
        if best_intent:
            # Try to extract date params deterministically
            params = self._extract_date_params(q)
            
            # Check for specific entity names (simple heuristic mainly for search param)
            # If quotes are used, extract them as search term
            import re
            search_match = re.search(r'["\'](.*?)["\']', q)
            if search_match:
                params["search"] = search_match.group(1)
            
            return ClassificationResult(
                intent=best_intent,
                params=params,
                column_profile=INTENTS[best_intent].default_profile,
                confidence=0.95,
                original_question=q
            )
            
        return None

    def _extract_date_params(self, question: str) -> Dict[str, str]:
        """Parse dates deterministically."""
        import re
        from datetime import datetime, timedelta
        
        q = question.lower()
        now = datetime.now()
        year = now.year
        
        # Explicit Year
        if match := re.search(r'202[0-9]', q):
            year = int(match.group(0))

        # Q1-Q4
        if match := re.search(r'q([1-4])', q):
            quarter = int(match.group(1))
            months = [(1,3), (4,6), (7,9), (10,12)][quarter-1]
            
            # Check if user specified a year after Qx (e.g. Q1 2026)
            # Already set 'year' above if present globally
            
            from calendar import monthrange
            last_day = monthrange(year, months[1])[1]
            return {
                "date_from": f"{year}-{months[0]:02d}-01",
                "date_to": f"{year}-{months[1]:02d}-{last_day}"
            }
        
        # "Volgende maand"
        if "volgende maand" in q:
            next_month = now.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            from calendar import monthrange
            last_day = monthrange(next_month.year, next_month.month)[1]
            return {
                "date_from": next_month.strftime("%Y-%m-%01"),
                "date_to": next_month.strftime(f"%Y-%m-{last_day}")
            }

        # "Deze maand"
        if "deze maand" in q:
            from calendar import monthrange
            last_day = monthrange(now.year, now.month)[1]
            return {
                "date_from": now.strftime("%Y-%m-01"),
                "date_to": now.strftime(f"%Y-%m-{last_day}")
            }
            
        return {}

    def classify(self, question: str) -> ClassificationResult:
        """
        Classify a user question into an intent.
        
        Strategy:
        1. Fast Path: Keyword matching (0 tokens, <10ms)
        2. Slow Path: LLM call (~200 tokens, ~1s)
        """
        # 1. Fast Path
        quick_match = self._try_keyword_match(question)
        if quick_match:
            logger.info(f"⚡ Fast-path intent match: {quick_match.intent}")
            return quick_match
            
        # 2. Slow Path (LLM)
        logger.info("🧠 LLM fallback for classification...")
        prompt = CLASSIFICATION_PROMPT.format(
            intent_list=self._get_intent_list(),
            question=question
        )
        
        try:
            if self.provider == "anthropic":
                result = self._call_anthropic(prompt)
            elif self.provider == "openai":
                result = self._call_openai(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # Parse JSON response
            parsed = json.loads(result)
            
            return ClassificationResult(
                intent=parsed.get("intent", "general_query"),
                params=parsed.get("params", {}),
                column_profile=parsed.get("column_profile", "ops"),
                confidence=0.9,
                original_question=question
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Classification parse error: {e}, falling back to general_query")
            return ClassificationResult(
                intent="general_query",
                params={},
                column_profile="ops",
                confidence=0.5,
                original_question=question
            )
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return ClassificationResult(
                intent="general_query",
                params={},
                column_profile="ops",
                confidence=0.3,
                original_question=question
            )
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API with minimal tokens."""
        client = Anthropic()
        response = client.messages.create(
            model=self.model,
            max_tokens=256,  # Tiny response expected
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API with minimal tokens."""
        client = OpenAI()
        response = client.chat.completions.create(
            model=self.model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_intent_definition(intent_name: str) -> Optional[IntentDefinition]:
    """Get the definition for an intent."""
    return INTENTS.get(intent_name)


def list_available_intents() -> List[str]:
    """List all available intent names."""
    return list(INTENTS.keys())


# =============================================================================
# CLI TEST
# =============================================================================

if __name__ == "__main__":
    import sys
    
    classifier = IntentClassifier()
    
    test_questions = [
        "Welke checkouts zijn er in januari 2026?",
        "Toon alle huizen in Amsterdam",
        "Wat is de bezettingsgraad?",
        "Geef me een overzicht van de winstgevende huizen",
        "Hoeveel inspecties staan er gepland voor volgende week?", 
        "Wat is het gemiddelde aantal dagen tussen schoonmaak en checkout?",
        "Hallo wie ben jij?",
        "Thanks!",
        "Sup"
    ]
    
    for q in test_questions:
        print(f"\n❓ {q}")
        result = classifier.classify(q)
        print(f"   → Intent: {result.intent}")
        print(f"   → Params: {result.params}")
        print(f"   → Profile: {result.column_profile}")
        if result.confidence > 0.94:
            print("   ⚡ (Fast Path)")
        else:
             print("   🧠 (LLM Path)")
