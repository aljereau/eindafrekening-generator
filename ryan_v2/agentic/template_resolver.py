"""
RYAN-V2: Agentic Pipeline
Template Resolver Module

Maps classified intents to SQL queries using templates.
This is pure code - NO LLM calls.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import logging

from .intent_classifier import IntentDefinition, INTENTS, ClassificationResult

logger = logging.getLogger("ryan_resolver")


# =============================================================================
# COLUMN PROFILES
# =============================================================================

COLUMN_PROFILES: Dict[str, Dict[str, List[str]]] = {
    # Operations profiles
    "ops": {
        "v_alle_huizen": ["object_id", "adres", "postcode", "plaats", "woning_type", "status", "borg", "voorschot_gwe"],
        "v_bookings_extended": ["booking_id", "adres", "postcode", "klant_naam", "checkin_datum", "checkout_datum", "verblijf_dagen", "status"],
        "v_actieve_cycli": ["*"],  # All columns
        "v_open_acties": ["*"],
        "v_planning_inputs": ["*"],
        "v_inspections_pipeline": ["adres", "klant_naam", "inspection_type", "planned_date", "status", "urgentie", "inspector"],
        "v_occupancy_summary": ["object_id", "adres", "plaats", "huidige_huurder", "huidige_checkout", "volgende_checkin"],
        "v_schoonmaak_variance": ["*"],
        "v_contracts_overview": ["contract_type", "adres", "klant_naam", "start_datum", "eind_datum", "kale_huur", "status"],
        "view_latest_pricing": ["*"],
        "relaties": ["id", "naam", "email", "telefoonnummer"],
        "v_eindafrekeningen_extended": ["id", "client_name", "checkin_date", "checkout_date", "object_address", "totaal_eindafrekening", "created_at"],
    },
    # Finance profiles
    "finance": {
        "v_alle_huizen": ["object_id", "adres", "postcode", "borg", "voorschot_gwe", "internet", "meubilering", "tuinonderhoud"],
        "v_bookings_extended": ["booking_id", "adres", "klant_naam", "checkout_datum", "betaalde_borg", "voorschot_gwe", "voorschot_schoonmaak", "totale_huur_factuur"],
        "view_house_profitability": ["*"],
        "view_client_scorecard": ["*"],
        "v_contracts_overview": ["*"],
        "view_latest_pricing": ["*"],
        "v_eindafrekeningen_extended": ["*"],
        "relaties": ["id", "naam", "email"],
    },
}


# =============================================================================
# QUERY RESOLUTION
# =============================================================================

@dataclass
class ResolvedQuery:
    """Result of template resolution."""
    sql: str
    params: Dict[str, Any]
    columns: List[str]
    source_view: str
    is_fallback: bool = False


class TemplateResolver:
    """Resolves classified intents to SQL queries."""
    
    def resolve(self, classification: ClassificationResult) -> ResolvedQuery:
        """
        Convert a classification result into an executable SQL query.
        
        Args:
            classification: Result from IntentClassifier
            
        Returns:
            ResolvedQuery with SQL, params, and column info
        """
        intent_name = classification.intent
        params = classification.params
        profile = classification.column_profile
        
        # Get intent definition
        intent_def = INTENTS.get(intent_name)
        if not intent_def or intent_name == "general_query":
            return self._resolve_fallback(classification)
        
        # Get column list based on profile
        columns = self._get_columns(intent_def.view_or_table, profile)
        column_str = ", ".join(columns) if columns and "*" not in columns else "*"
        
        # Build WHERE clause
        where_parts, sql_params = self._build_where(intent_def, params)
        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        
        # Build ORDER BY
        order_by = self._get_default_order(intent_def.view_or_table)
        
        # Build LIMIT
        limit = params.get("limit", 1000)
        
        # Construct SQL
        sql = f"""SELECT {column_str}
FROM {intent_def.view_or_table}
{where_clause}
{order_by}
LIMIT {limit}"""
        
        return ResolvedQuery(
            sql=sql.strip(),
            params=sql_params,
            columns=columns,
            source_view=intent_def.view_or_table,
            is_fallback=False
        )
    
    def _get_columns(self, view_name: str, profile: str) -> List[str]:
        """Get column list for a view based on profile."""
        profile_columns = COLUMN_PROFILES.get(profile, COLUMN_PROFILES["ops"])
        return profile_columns.get(view_name, ["*"])
    
    def _build_where(self, intent_def: IntentDefinition, params: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
        """Build WHERE clause from intent definition and params."""
        where_parts = []
        sql_params = {}
        
        # Add default filters from intent definition
        if intent_def.default_filters:
            where_parts.append(intent_def.default_filters)
        
        # Handle date range
        if intent_def.supports_date_range:
            if params.get("date_from"):
                # Determine date column based on intent
                date_col = self._get_date_column(intent_def.name)
                where_parts.append(f"{date_col} >= :date_from")
                sql_params["date_from"] = params["date_from"]
            if params.get("date_to"):
                date_col = self._get_date_column(intent_def.name)
                where_parts.append(f"{date_col} <= :date_to")
                sql_params["date_to"] = params["date_to"]
        
        # Handle search
        if intent_def.supports_search and params.get("search"):
            search_col = self._get_search_column(intent_def.view_or_table)
            where_parts.append(f"{search_col} LIKE :search")
            sql_params["search"] = f"%{params['search']}%"
        
        return where_parts, sql_params
    
    def _get_date_column(self, intent_name: str) -> str:
        """Get the appropriate date column for an intent."""
        date_columns = {
            "checkout_list": "checkout_datum",
            "checkin_list": "checkin_datum",
            "booking_list": "checkin_datum",
            "inspection_schedule": "planned_date",
            "settlement_history": "created_at",
        }
        return date_columns.get(intent_name, "created_at")
    
    def _get_search_column(self, view_name: str) -> str:
        """Get the default search column for a view."""
        search_columns = {
            "v_alle_huizen": "adres",
            "v_bookings_extended": "klant_naam",
            "relaties": "naam",
            "v_eindafrekeningen_extended": "client_name",
        }
        return search_columns.get(view_name, "adres")
    
    def _get_default_order(self, view_name: str) -> str:
        """Get default ORDER BY for a view."""
        orders = {
            "v_bookings_extended": "ORDER BY checkout_datum DESC",
            "v_inspections_pipeline": "ORDER BY planned_date ASC",
            "v_eindafrekeningen_extended": "ORDER BY created_at DESC",
            "v_alle_huizen": "ORDER BY adres",
            "v_actieve_cycli": "ORDER BY einddatum_huurder ASC",
        }
        return orders.get(view_name, "")
    
    def _resolve_fallback(self, classification: ClassificationResult) -> ResolvedQuery:
        """
        Create a fallback result for general_query intent.
        This will trigger LLM SQL generation in the pipeline.
        """
        return ResolvedQuery(
            sql="",  # Empty - pipeline will use LLM
            params={},
            columns=[],
            source_view="",
            is_fallback=True
        )


# =============================================================================
# CONVENIENCE
# =============================================================================

def resolve_intent(classification: ClassificationResult) -> ResolvedQuery:
    """Convenience function to resolve an intent."""
    resolver = TemplateResolver()
    return resolver.resolve(classification)


# =============================================================================
# CLI TEST
# =============================================================================

if __name__ == "__main__":
    from .intent_classifier import ClassificationResult
    
    # Test with mock classification results
    test_cases = [
        ClassificationResult(
            intent="checkout_list",
            params={"date_from": "2026-01-01", "date_to": "2026-03-31"},
            column_profile="ops",
            confidence=0.9,
            original_question="Checkouts Q1 2026"
        ),
        ClassificationResult(
            intent="house_list",
            params={"search": "Amsterdam"},
            column_profile="ops",
            confidence=0.9,
            original_question="Huizen in Amsterdam"
        ),
        ClassificationResult(
            intent="general_query",
            params={},
            column_profile="ops",
            confidence=0.5,
            original_question="Complex question"
        ),
    ]
    
    resolver = TemplateResolver()
    
    for tc in test_cases:
        print(f"\n❓ {tc.original_question}")
        result = resolver.resolve(tc)
        print(f"   → SQL: {result.sql}")
        print(f"   → Params: {result.params}")
        print(f"   → Fallback: {result.is_fallback}")
