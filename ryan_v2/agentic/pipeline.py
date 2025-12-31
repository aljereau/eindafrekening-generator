"""
RYAN-V2: Agentic Pipeline
Main Pipeline Orchestrator

This is the main entry point for the agentic export pipeline.
Orchestrates: Intent Classification → Template Resolution → Query → Export → Cache
"""

import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

from .intent_classifier import IntentClassifier, ClassificationResult
from .template_resolver import TemplateResolver, ResolvedQuery
from .exporter import smart_export, get_column_names
from .cache_manager import get_cache_key, get_cached_export, save_to_cache

# Import config for DB path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ryan_v2.config import DB_PATH

logger = logging.getLogger("ryan_pipeline")


# =============================================================================
# PIPELINE RESULT
# =============================================================================

@dataclass
class PipelineResult:
    """Result of the agentic pipeline."""
    success: bool
    intent: str
    export_path: Optional[str]
    download_url: Optional[str]
    row_count: int
    cache_hit: bool
    message: str
    sql_used: Optional[str] = None
    classification: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "intent": self.intent,
            "export_path": self.export_path,
            "download_url": self.download_url,
            "row_count": self.row_count,
            "cache_hit": self.cache_hit,
            "message": self.message,
            "sql_used": self.sql_used,
            "classification": self.classification
        }


# =============================================================================
# MAIN PIPELINE
# =============================================================================

class AgenticPipeline:
    """
    The main agentic export pipeline.
    
    Layers:
    1. Intent Classifier (tiny LLM) - Classify question
    2. Template Resolver (code) - Map intent to SQL
    3. Cache Check (code) - Deduplicate
    4. Query Runner (code) - Execute SQL
    5. Exporter (code) - Stream to file
    6. Quality Checks (code) - Validate output
    """
    
    def __init__(self, 
                 db_path: str = DB_PATH,
                 llm_provider: str = None,
                 llm_model: str = None):
        self.db_path = db_path
        
        # Use user-selected model from settings if not explicitly provided
        if llm_model is None or llm_provider is None:
            from ryan_v2.settings_service import get_active_model
            active = get_active_model()
            model_id = active["id"]  # Format: "provider:model"
            if ":" in model_id:
                llm_provider, llm_model = model_id.split(":", 1)
            else:
                llm_provider = "anthropic"
                llm_model = model_id
        
        self.classifier = IntentClassifier(provider=llm_provider, model=llm_model)
        self.resolver = TemplateResolver()
    
    def process(self, question: str, export_format: str = "xlsx") -> PipelineResult:
        """
        Process a natural language question through the pipeline.
        
        Args:
            question: Natural language question in Dutch or English
            export_format: Output format ("xlsx" or "csv")
            
        Returns:
            PipelineResult with export info
        """
        try:
            # LAYER 1: Intent Classification (tiny LLM call)
            logger.info(f"Classifying: {question}")
            classification = self.classifier.classify(question)
            logger.info(f"Intent: {classification.intent}, Params: {classification.params}")
            
            # HANDLE CHITCHAT / SYSTEM INTENTS
            if classification.intent == "chitchat":
                return PipelineResult(
                    success=True,
                    intent="chitchat",
                    export_path=None,
                    download_url=None,
                    row_count=0,
                    cache_hit=False,
                    message="Conversational intent detected.",
                    sql_used=None,
                    classification=classification.to_dict()
                )
            
            # LAYER 2: Template Resolution (no LLM)
            resolved = self.resolver.resolve(classification)
            
            # Handle fallback (general_query)
            if resolved.is_fallback:
                return self._handle_fallback(question, classification, export_format)
            
            # LAYER 3: Cache Check
            cache_key = get_cache_key(
                classification.intent, 
                classification.params, 
                classification.column_profile
            )
            cached_path = get_cached_export(cache_key)
            
            if cached_path:
                # Cache hit - return immediately
                return PipelineResult(
                    success=True,
                    intent=classification.intent,
                    export_path=str(cached_path),
                    download_url=f"/exports/{cached_path.name}",
                    row_count=-1,  # Unknown from cache
                    cache_hit=True,
                    message=f"✓ Cache hit! Bestand: {cached_path.name}",
                    sql_used=resolved.sql,
                    classification=classification.to_dict()
                )
            
            # LAYER 4 & 5: Query + Export
            row_count = self._count_rows(resolved.sql, resolved.params)
            
            # LAYER 6: Quality Checks
            if row_count == 0:
                return PipelineResult(
                    success=True,
                    intent=classification.intent,
                    export_path=None,
                    download_url=None,
                    row_count=0,
                    cache_hit=False,
                    message="Geen resultaten gevonden voor deze zoekopdracht.",
                    sql_used=resolved.sql,
                    classification=classification.to_dict()
                )
            
            if row_count > 10000:
                logger.warning(f"Large export: {row_count} rows")
            
            # Generate filename based on intent
            base_filename = f"{classification.intent}_{cache_key[:8]}"
            
            # Export
            export_result = smart_export(
                db_path=self.db_path,
                sql=resolved.sql,
                params=resolved.params,
                format=export_format,
                base_filename=base_filename
            )
            
            # Save to cache
            export_path = Path(export_result["filepath"])
            save_to_cache(cache_key, export_path)
            
            return PipelineResult(
                success=True,
                intent=classification.intent,
                export_path=export_result["filepath"],
                download_url=export_result["download_url"],
                row_count=row_count,
                cache_hit=False,
                message=f"✓ Export klaar: {row_count} rijen → {export_path.name}",
                sql_used=resolved.sql,
                classification=classification.to_dict()
            )
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            return PipelineResult(
                success=False,
                intent="error",
                export_path=None,
                download_url=None,
                row_count=0,
                cache_hit=False,
                message=f"Fout: {str(e)}",
                sql_used=None,
                classification=None
            )
    
    def _count_rows(self, sql: str, params: Dict[str, Any]) -> int:
        """Count rows without fetching all data."""
        # Wrap in COUNT query
        count_sql = f"SELECT COUNT(*) FROM ({sql})"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(count_sql, params)
            else:
                cursor.execute(count_sql)
            return cursor.fetchone()[0]
        finally:
            cursor.close()
            conn.close()
    
    def _handle_fallback(self, question: str, classification: ClassificationResult, 
                        export_format: str) -> PipelineResult:
        """
        Handle general_query fallback using LLM SQL generation.
        
        This uses more tokens but still has guardrails:
        - Schema is cached (not sent every time)
        - SELECT only
        - LIMIT enforced
        """
        from ryan_v2.sql_service import SQLService
        
        sql_service = SQLService()
        
        # Generate SQL using LLM (with cached schema)
        sql = sql_service.generate_sql(question)
        
        if sql.startswith("--") or "Error" in sql:
            return PipelineResult(
                success=False,
                intent="general_query",
                export_path=None,
                download_url=None,
                row_count=0,
                cache_hit=False,
                message=f"Kon geen SQL genereren: {sql}",
                sql_used=sql,
                classification=classification.to_dict()
            )
        
        # Enforce LIMIT if not present
        if "LIMIT" not in sql.upper():
            sql = sql.rstrip(";") + " LIMIT 1000"
        
        # Execute and export
        cache_key = get_cache_key("general_query", {"q": question}, "ops")
        base_filename = f"query_{cache_key[:8]}"
        
        try:
            row_count = self._count_rows(sql, {})
            
            if row_count == 0:
                return PipelineResult(
                    success=True,
                    intent="general_query",
                    export_path=None,
                    download_url=None,
                    row_count=0,
                    cache_hit=False,
                    message="Geen resultaten gevonden.",
                    sql_used=sql,
                    classification=classification.to_dict()
                )
            
            export_result = smart_export(
                db_path=self.db_path,
                sql=sql,
                params={},
                format=export_format,
                base_filename=base_filename
            )
            
            export_path = Path(export_result["filepath"])
            save_to_cache(cache_key, export_path)
            
            return PipelineResult(
                success=True,
                intent="general_query",
                export_path=export_result["filepath"],
                download_url=export_result["download_url"],
                row_count=row_count,
                cache_hit=False,
                message=f"✓ Query uitgevoerd: {row_count} rijen → {export_path.name}",
                sql_used=sql,
                classification=classification.to_dict()
            )
            
        except Exception as e:
            return PipelineResult(
                success=False,
                intent="general_query",
                export_path=None,
                download_url=None,
                row_count=0,
                cache_hit=False,
                message=f"Query fout: {str(e)}",
                sql_used=sql,
                classification=classification.to_dict()
            )


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def ask(question: str, export_format: str = "xlsx") -> PipelineResult:
    """
    Convenience function to process a question.
    
    Args:
        question: Natural language question
        export_format: Output format
        
    Returns:
        PipelineResult
    """
    pipeline = AgenticPipeline()
    return pipeline.process(question, export_format)


# =============================================================================
# CLI TEST
# =============================================================================

if __name__ == "__main__":
    import sys
    
    # Test questions
    test_questions = [
        "Welke checkouts zijn er in januari 2026?",
        "Toon alle huizen in Den Haag",
        "Geef me de winstgevende huizen",
    ]
    
    pipeline = AgenticPipeline()
    
    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"❓ {q}")
        print("="*60)
        
        result = pipeline.process(q)
        
        print(f"✓ Intent: {result.intent}")
        print(f"✓ Success: {result.success}")
        print(f"✓ Rows: {result.row_count}")
        print(f"✓ Cache hit: {result.cache_hit}")
        print(f"✓ Message: {result.message}")
        if result.sql_used:
            print(f"✓ SQL: {result.sql_used[:100]}...")
