"""
RYAN-V2: RyanRent Intelligent Agent
SQL Tools Module

These are the 4 core tools the agent uses to understand and query the database.
Each tool is self-contained and returns structured data for the LLM.
"""
import sqlite3
import json
from typing import List, Dict, Any, Optional
from .config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory for dict results."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# TOOL 1: list_tables
# =============================================================================
def list_tables() -> str:
    """
    Returns all tables in the database with their row counts.
    
    Use this FIRST to understand what data is available.
    
    Returns:
        Formatted string listing tables and row counts.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    result = "📊 **Available Tables:**\n\n"
    result += "| Table | Rows |\n|-------|------|\n"
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
            count = cursor.fetchone()[0]
            result += f"| `{table}` | {count} |\n"
        except Exception as e:
            result += f"| `{table}` | Error: {e} |\n"
    
    conn.close()
    return result


# =============================================================================
# TOOL 2: describe_table
# =============================================================================
def describe_table(table_name: str) -> str:
    """
    Returns the schema of a specific table (columns, types, constraints).
    
    Use this to understand what data a table contains before querying.
    
    Args:
        table_name: Name of the table to describe.
        
    Returns:
        Formatted string with column definitions.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get column info using PRAGMA
        cursor.execute(f"PRAGMA table_info([{table_name}])")
        columns = cursor.fetchall()
        
        if not columns:
            return f"❌ Table `{table_name}` not found."
        
        result = f"📋 **Schema for `{table_name}`:**\n\n"
        result += "| Column | Type | Nullable | Default | Primary Key |\n"
        result += "|--------|------|----------|---------|-------------|\n"
        
        for col in columns:
            # col: (cid, name, type, notnull, dflt_value, pk)
            nullable = "No" if col[3] else "Yes"
            default = col[4] if col[4] else "-"
            pk = "✓" if col[5] else ""
            result += f"| `{col[1]}` | {col[2]} | {nullable} | {default} | {pk} |\n"
        
        # Also get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list([{table_name}])")
        fks = cursor.fetchall()
        
        if fks:
            result += "\n**Foreign Keys:**\n"
            for fk in fks:
                result += f"- `{fk[3]}` → `{fk[2]}.{fk[4]}`\n"
        
        conn.close()
        return result
        
    except Exception as e:
        conn.close()
        return f"❌ Error describing `{table_name}`: {e}"


# =============================================================================
# TOOL 3: sample_table
# =============================================================================
def sample_table(table_name: str, n: int = 3) -> str:
    """
    Returns sample rows from a table to understand its data format.
    
    Use this to see actual values before writing complex queries.
    
    Args:
        table_name: Name of the table to sample.
        n: Number of rows to return (default 3, max 10).
        
    Returns:
        Formatted markdown table with sample data.
    """
    n = min(n, 10)  # Safety limit
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT * FROM [{table_name}] LIMIT {n}")
        rows = cursor.fetchall()
        
        if not rows:
            return f"📭 Table `{table_name}` is empty."
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        result = f"🔍 **Sample from `{table_name}` ({n} rows):**\n\n"
        
        # Build markdown table header
        result += "| " + " | ".join(columns) + " |\n"
        result += "| " + " | ".join(["---"] * len(columns)) + " |\n"
        
        # Add rows
        for row in rows:
            values = [str(v) if v is not None else "-" for v in row]
            # Truncate long values
            values = [v[:50] + "..." if len(v) > 50 else v for v in values]
            result += "| " + " | ".join(values) + " |\n"
        
        conn.close()
        return result
        
    except Exception as e:
        conn.close()
        return f"❌ Error sampling `{table_name}`: {e}"


# =============================================================================
# TOOL 4: execute_sql
# =============================================================================
def execute_sql(query: str) -> str:
    """
    Executes a SQL query and returns the results.
    
    ONLY use for SELECT queries. Never run UPDATE, DELETE, or DROP.
    
    Args:
        query: The SQL query to execute (SELECT only).
        
    Returns:
        Query results as a formatted markdown table, or error message.
    """
    # Safety check: only allow SELECT
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        return "❌ **Security Error:** Only SELECT queries are allowed."
    
    dangerous_keywords = ["UPDATE", "DELETE", "DROP", "INSERT", "ALTER", "TRUNCATE"]
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return f"❌ **Security Error:** `{keyword}` operations are not allowed."
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            return "📭 Query returned no results."
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        result = f"✅ **Query Results ({len(rows)} rows):**\n\n"
        
        # Limit display if too many rows
        display_rows = rows[:50]
        if len(rows) > 50:
            result = f"✅ **Query Results (showing 50 of {len(rows)} rows):**\n\n"
        
        # Build markdown table
        result += "| " + " | ".join(columns) + " |\n"
        result += "| " + " | ".join(["---"] * len(columns)) + " |\n"
        
        for row in display_rows:
            values = [str(v) if v is not None else "-" for v in row]
            values = [v[:50] + "..." if len(v) > 50 else v for v in values]
            result += "| " + " | ".join(values) + " |\n"
        
        conn.close()
        return result
        
    except Exception as e:
        conn.close()
        return f"❌ **SQL Error:** {e}\n\n**Query was:**\n```sql\n{query}\n```"


# =============================================================================
# TOOL 5: export_to_excel
# =============================================================================
def export_to_excel(query: str, filename: str = "export.xlsx") -> str:
    """
    Executes a SQL query and exports results to an Excel file.
    
    Use this when the user asks for a full export or when results exceed 10 rows.
    
    Args:
        query: The SQL query to execute (SELECT only).
        filename: Output filename (default: export.xlsx).
        
    Returns:
        Path to the created Excel file, or error message.
    """
    try:
        import pandas as pd
        from datetime import datetime
        from pathlib import Path
    except ImportError:
        return "❌ **Error:** pandas/openpyxl not installed. Run: `pip install pandas openpyxl`"
    
    # Safety check
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        return "❌ **Security Error:** Only SELECT queries are allowed."
    
    conn = get_connection()
    
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return "📭 Query returned no results to export."
        
        # Create exports folder inside ryan_v2
        exports_dir = Path(__file__).parent / "exports"
        exports_dir.mkdir(exist_ok=True)
        
        # Add timestamp to filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(filename).stem
        output_path = exports_dir / f"{base_name}_{timestamp}.xlsx"
        
        df.to_excel(output_path, index=False, engine='openpyxl')
        
        return f"✅ **Exported {len(df)} rows to:**\n`{output_path}`"
        
    except Exception as e:
        conn.close()
        return f"❌ **Export Error:** {e}"


# =============================================================================
# Tool Registry (for agent)
# =============================================================================
TOOLS = {
    "list_tables": {
        "function": list_tables,
        "description": "Returns all tables in the database with row counts. Use FIRST to explore.",
        "parameters": {}
    },
    "describe_table": {
        "function": describe_table,
        "description": "Returns the schema (columns, types) of a specific table.",
        "parameters": {
            "table_name": {"type": "string", "description": "Name of the table to describe"}
        }
    },
    "sample_table": {
        "function": sample_table,
        "description": "Returns sample rows from a table to understand data format.",
        "parameters": {
            "table_name": {"type": "string", "description": "Name of the table to sample"},
            "n": {"type": "integer", "description": "Number of rows (default 3, max 10)"}
        }
    },
    "execute_sql": {
        "function": execute_sql,
        "description": "Executes a SELECT query and returns results. Use after understanding schema.",
        "parameters": {
            "query": {"type": "string", "description": "The SQL query to execute (SELECT only)"}
        }
    },
    "export_to_excel": {
        "function": export_to_excel,
        "description": "Exports query results to Excel file. Use for large datasets or when user requests export.",
        "parameters": {
            "query": {"type": "string", "description": "The SQL query to execute"},
            "filename": {"type": "string", "description": "Output filename (default: export.xlsx)"}
        }
    }
}


def get_tool_definitions() -> List[Dict]:
    """Returns tool definitions in OpenAI function-calling format."""
    definitions = []
    for name, tool in TOOLS.items():
        definition = {
            "type": "function",
            "function": {
                "name": name,
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": tool["parameters"],
                    "required": [k for k in tool["parameters"].keys()]
                }
            }
        }
        definitions.append(definition)
    return definitions


def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    """Execute a tool by name with given arguments."""
    if name not in TOOLS:
        return f"❌ Unknown tool: `{name}`"
    
    try:
        func = TOOLS[name]["function"]
        return func(**arguments)
    except Exception as e:
        return f"❌ Tool execution error: {e}"
