
import sqlite3
import json
import math
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from openai import OpenAI

from .config import DB_PATH, MODEL_IDS

logger = logging.getLogger("ryan_sql")

class SQLService:
    def __init__(self):
        self.db_path = DB_PATH
        self.schema_cache = None
        self.last_refreshed = None
        self._load_schema()

    def _load_schema(self):
        """Loads and caches the database schema."""
        import datetime
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            schema = ""
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [f"{row[1]} ({row[2]})" for row in cursor.fetchall()]
                schema += f"Table: {table}\nColumns: {', '.join(columns)}\n\n"
                
            self.schema_cache = schema
            self.last_refreshed = datetime.datetime.now().isoformat()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            self.schema_cache = "Error loading schema."

    def refresh_schema(self):
        """Public method to trigger schema reload."""
        self._load_schema()
        return self.last_refreshed


    def get_tables(self) -> List[str]:
        """Returns list of table names."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tables
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []

    def get_schema_details(self) -> Dict[str, List[Dict[str, str]]]:
        """Returns detailed schema: {table: [{name: col, type: type}, ...]}"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            details = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                # row structure: (cid, name, type, notnull, dflt_value, pk)
                columns = []
                for row in cursor.fetchall():
                    col_name = row[1]
                    col_type = row[2].lower()
                    columns.append({"name": col_name, "type": col_type})
                details[table] = columns
                
            conn.close()
            return details
        except Exception as e:
            logger.error(f"Error getting schema details: {e}")
            return {}

    def generate_sql(self, prompt: str, model_id: str = "anthropic:claude-sonnet-4-5-20250929") -> str:
        """Generates SQL from natural language using the cached schema."""
        
        system_prompt = f"""You are a high-performance SQL generator for SQLite.
Your only job is to write valid SQL queries based on the user's request and the provided schema.

DATABASE SCHEMA:
{self.schema_cache}

RULES:
1. Return ONLY the SQL query. No markdown, no explanations.
2. If the request is impossible, select 'Error: Impossible' as a string.
3. Use modern SQLite syntax.
4. Do NOT use DELETES or UPDATES unless explicitly requested (this is mostly for analysis).
"""
        
        # Determine provider
        provider = model_id.split(":")[0] if ":" in model_id else "anthropic"
        actual_model = model_id.split(":")[1] if ":" in model_id else model_id
        
        try:
            if provider == "anthropic":
                client = Anthropic() # Assumes env var ANTHROPIC_API_KEY is set
                response = client.messages.create(
                    model=actual_model,
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
                
            elif provider == "openai":
                client = OpenAI() # Assumes env var OPENAI_API_KEY is set
                response = client.chat.completions.create(
                    model=actual_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content.strip()
            
            else:
                return f"-- Unsupported provider: {provider}"
                
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return f"-- Error generating SQL: {str(e)}"

    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """Executes raw SQL and returns results + export path."""
        # Simple safety check
        if "DROP" in sql.upper() or "DELETE" in sql.upper():
             # Basic safety, though user asked for power. Let's allow but log warn?
             # For a "Beekeeper" clone, users usually CAN delete.
             pass

        try:
            import pandas as pd
            import datetime
            
            conn = sqlite3.connect(self.db_path)
            
            # Use pandas for easy export
            df = pd.read_sql_query(sql, conn)
            conn.close()
            
            # Export to Excel
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"query_result_{timestamp}.xlsx"
            export_path = Path(__file__).parent / "exports" / filename
            
            # Create exports dir if not exists (redundant but safe)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            df.to_excel(export_path, index=False)
            
            # Return JSON friendly data
            # Limit to 100 rows for preview to keep JSON light
            preview_df = df.head(100)
            
            # Convert to dict first
            preview_data = preview_df.to_dict(orient='records')
            
            # Manually clean data to ensure JSON compliance
            for row in preview_data:
                for key, value in row.items():
                    if isinstance(value, float):
                        if math.isnan(value) or math.isinf(value):
                            row[key] = None
            columns = list(df.columns)
            
            return {
                "status": "success",
                "columns": columns,
                "rows": preview_data,
                "total_rows": len(df),
                "export_url": f"http://localhost:8000/exports/{filename}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
