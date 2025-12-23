"""
RYAN-V2: RyanRent Intelligent Agent
SQL Tools Module

These are the 9 tools the agent uses to understand and query the database.
Each tool is self-contained and returns structured data for the LLM.

Core Tools (1-5): Database exploration and querying
In/Uit-Check Tools (6-9): Check-in/check-out lifecycle management
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
# TOOL 6: list_active_cycli
# =============================================================================
def list_active_cycli(limit: int = 20) -> str:
    """
    Returns all active check-in/check-out cycles with status and priorities.

    Use this to see which properties are currently in the check-out → cleaning → check-in process.

    Args:
        limit: Maximum number of cycles to return (default 20).

    Returns:
        Formatted table with active cycles, deadlines, and status.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Query v_actieve_cycli view
        cursor.execute(f"""
            SELECT
                adres,
                plaats,
                status,
                klant_type,
                bestemming,
                deadline_dagen,
                open_acties_count,
                startdatum_nieuwe_huurder,
                interne_opmerking
            FROM v_actieve_cycli
            LIMIT {limit}
        """)

        rows = cursor.fetchall()

        if not rows:
            return "📭 Geen actieve cycli gevonden."

        result = f"🏠 **Actieve In/Uit-Check Cycli ({len(rows)} van max {limit}):**\n\n"

        # Build markdown table
        result += "| Adres | Status | Klant | Deadline (dagen) | Open Acties | Opmerking |\n"
        result += "|-------|--------|-------|------------------|-------------|----------|\n"

        for row in rows:
            adres = f"{row[0]}, {row[1]}" if row[1] else row[0]
            status = row[2]
            klant = row[3]
            deadline = f"{int(row[5])}" if row[5] is not None else "-"
            open_acties = row[6]
            opmerking = (row[8][:30] + "...") if row[8] and len(row[8]) > 30 else (row[8] or "-")

            # Add urgency indicator
            urgency_icon = ""
            if row[5] is not None:
                if row[5] <= 2:
                    urgency_icon = "🚨"
                elif row[5] <= 5:
                    urgency_icon = "⚠️"

            result += f"| {adres} | {status} | {klant} | {urgency_icon} {deadline} | {open_acties} | {opmerking} |\n"

        conn.close()
        return result

    except Exception as e:
        conn.close()
        return f"❌ **Error:** {e}"


# =============================================================================
# TOOL 7: describe_cyclus
# =============================================================================
def describe_cyclus(object_id: str) -> str:
    """
    Returns full details of a property's active cycle including all actions.

    Use this to get complete information about a specific property's check-in/check-out status.

    Args:
        object_id: The property ID (object_id from huizen table).

    Returns:
        Detailed cycle information with action history.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get cycle details
        cursor.execute("""
            SELECT
                cyclus_id,
                object_id,
                status,
                klant_type,
                bestemming,
                einddatum_huurder,
                startdatum_nieuwe_huurder,
                interne_opmerking,
                aangemaakt_op,
                laatst_bijgewerkt_op
            FROM woning_cycli
            WHERE object_id = ? AND is_actief = 1
        """, (object_id,))

        cycle = cursor.fetchone()

        if not cycle:
            return f"❌ Geen actieve cyclus gevonden voor object_id: `{object_id}`"

        # Get property details
        cursor.execute("""
            SELECT adres, postcode, plaats, woning_type, aantal_sk, aantal_pers
            FROM huizen
            WHERE object_id = ?
        """, (object_id,))

        huis = cursor.fetchone()

        result = f"🏠 **Cyclus Details voor {huis[0] if huis else object_id}**\n\n"

        # Cycle info
        result += f"**Status:** {cycle[2]}\n"
        result += f"**Klant Type:** {cycle[3]}\n"
        result += f"**Bestemming:** {cycle[4]}\n"
        result += f"**Einddatum Huurder:** {cycle[5] or 'Onbekend'}\n"
        result += f"**Start Nieuwe Huurder:** {cycle[6] or 'Onbekend'}\n"

        if cycle[7]:
            result += f"**Opmerking:** {cycle[7]}\n"

        # Get actions
        cursor.execute("""
            SELECT
                actie_type,
                gepland_op,
                uitgevoerd_op,
                uitgevoerd_door,
                verwachte_schoonmaak_uren,
                werkelijke_schoonmaak_uren,
                opmerking
            FROM woning_acties
            WHERE cyclus_id = ?
            ORDER BY
                CASE
                    WHEN uitgevoerd_op IS NOT NULL THEN uitgevoerd_op
                    WHEN gepland_op IS NOT NULL THEN gepland_op
                    ELSE aangemaakt_op
                END ASC
        """, (cycle[0],))

        actions = cursor.fetchall()

        if actions:
            result += f"\n\n**Acties ({len(actions)}):**\n\n"
            result += "| Type | Gepland | Uitgevoerd | Door | Uren (V/W) |\n"
            result += "|------|---------|------------|------|------------|\n"

            for action in actions:
                actie_type = action[0]
                gepland = action[1][:10] if action[1] else "-"
                uitgevoerd = action[2][:10] if action[2] else "-"
                door = action[3] or "-"
                uren = f"{action[4]}/{action[5]}" if action[4] or action[5] else "-"

                icon = "✅" if action[2] else "📅"
                result += f"| {icon} {actie_type} | {gepland} | {uitgevoerd} | {door} | {uren} |\n"
        else:
            result += "\n\n**Acties:** Geen acties gevonden.\n"

        # Get status check
        cursor.execute("""
            SELECT status_severity, check_voorinspectie_gepland, check_uitcheck_uitgevoerd,
                   check_schoonmaak_nodig, check_klaar_voor_incheck, check_incheck_uitgevoerd
            FROM v_status_check
            WHERE object_id = ?
        """, (object_id,))

        status_check = cursor.fetchone()

        if status_check:
            severity = status_check[0]
            icon = "❌" if severity == "BLOCKER" else "⚠️" if severity == "WARNING" else "✅"
            result += f"\n\n**Status Validatie:** {icon} {severity}\n"

        conn.close()
        return result

    except Exception as e:
        conn.close()
        return f"❌ **Error:** {e}"


# =============================================================================
# TOOL 8: list_cycli_acties
# =============================================================================
def list_cycli_acties(actie_type: Optional[str] = None) -> str:
    """
    Returns action history across all active cycles, optionally filtered by action type.

    Use this to see planning overview or specific action types (e.g., all pending SCHOONMAAK actions).

    Args:
        actie_type: Filter by type (VOORINSPECTIE|UITCHECK|SCHOONMAAK|INCHECK|OVERDRACHT_EIGENAAR|REPARATIE).
                    If None, shows all actions.

    Returns:
        Formatted table of actions with property and cycle context.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Build query
        if actie_type:
            query = """
                SELECT
                    adres,
                    actie_type,
                    gepland_op,
                    uitgevoerd_op,
                    uitgevoerd_door,
                    deadline_dagen,
                    verwachte_schoonmaak_uren,
                    cyclus_status
                FROM v_open_acties
                WHERE actie_type = ?
                ORDER BY deadline_dagen ASC NULLS LAST, planning_dagen ASC
                LIMIT 30
            """
            cursor.execute(query, (actie_type,))
        else:
            query = """
                SELECT
                    adres,
                    actie_type,
                    gepland_op,
                    uitgevoerd_op,
                    uitgevoerd_door,
                    deadline_dagen,
                    verwachte_schoonmaak_uren,
                    cyclus_status
                FROM v_open_acties
                ORDER BY deadline_dagen ASC NULLS LAST, planning_dagen ASC
                LIMIT 30
            """
            cursor.execute(query)

        rows = cursor.fetchall()

        if not rows:
            filter_msg = f" van type `{actie_type}`" if actie_type else ""
            return f"📭 Geen open acties gevonden{filter_msg}."

        title = f"Open Acties: {actie_type}" if actie_type else "Alle Open Acties"
        result = f"📋 **{title} ({len(rows)}):**\n\n"

        # Build table
        result += "| Adres | Type | Gepland | Status | Deadline | Uren |\n"
        result += "|-------|------|---------|--------|----------|------|\n"

        for row in rows:
            adres = row[0][:25] + "..." if len(row[0]) > 25 else row[0]
            actie = row[1]
            gepland = row[2][:10] if row[2] else "-"
            status = row[7]
            deadline = f"{int(row[5])} dgn" if row[5] is not None else "-"
            uren = f"{row[6]}h" if row[6] else "-"

            # Urgency icon
            urgency = ""
            if row[5] is not None and row[5] <= 2:
                urgency = "🚨 "

            result += f"| {adres} | {actie} | {gepland} | {status} | {urgency}{deadline} | {uren} |\n"

        conn.close()
        return result

    except Exception as e:
        conn.close()
        return f"❌ **Error:** {e}"


# =============================================================================
# TOOL 9: get_planning_priorities
# =============================================================================
def get_planning_priorities(top_n: int = 10) -> str:
    """
    Returns AI-ready planning data with priority recommendations.

    Use this to get intelligent recommendations for what to work on next.

    Args:
        top_n: Number of top priority items to return (default 10).

    Returns:
        Prioritized list with suggested next actions and reasoning.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"""
            SELECT
                adres,
                status,
                volgende_actie,
                deadline_dagen,
                urgency_band,
                verwachte_schoonmaak_uren,
                open_acties_count,
                status_severity,
                klant_type,
                bestemming,
                laatst_toegewezen_team
            FROM v_planning_inputs
            LIMIT {top_n}
        """)

        rows = cursor.fetchall()

        if not rows:
            return "📭 Geen actieve cycli voor planning."

        result = f"🎯 **Planning Prioriteiten (Top {len(rows)}):**\n\n"

        for idx, row in enumerate(rows, 1):
            adres = row[0]
            status = row[1]
            volgende_actie = row[2]
            deadline_dagen = row[3]
            urgency = row[4]
            uren = row[5]
            open_acties = row[6]
            severity = row[7]
            klant_type = row[8]
            bestemming = row[9]
            team = row[10]

            # Priority icon
            if urgency == "CRITICAL":
                priority_icon = "🚨"
            elif urgency == "HIGH":
                priority_icon = "⚠️"
            elif severity == "BLOCKER":
                priority_icon = "❌"
            else:
                priority_icon = "📌"

            result += f"### {priority_icon} {idx}. {adres}\n\n"
            result += f"**Volgende Actie:** {volgende_actie}\n"
            result += f"**Status:** {status} ({severity})\n"
            result += f"**Urgentie:** {urgency}"

            if deadline_dagen is not None:
                result += f" ({int(deadline_dagen)} dagen)\n"
            else:
                result += "\n"

            if uren:
                result += f"**Verwachte Uren:** {uren}h\n"

            if open_acties > 0:
                result += f"**Open Acties:** {open_acties}\n"

            if team:
                result += f"**Laatste Team:** {team}\n"

            result += f"**Klant:** {klant_type} → {bestemming}\n\n"

        result += "\n💡 **Aanbeveling:** Begin met items met 🚨 CRITICAL urgency of ❌ BLOCKER status.\n"

        conn.close()
        return result

    except Exception as e:
        conn.close()
        return f"❌ **Error:** {e}"


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
    },
    "list_active_cycli": {
        "function": list_active_cycli,
        "description": "Returns all active check-in/check-out cycles with status and deadlines. Use to see which properties are in the checkout→cleaning→checkin process.",
        "parameters": {
            "limit": {"type": "integer", "description": "Maximum number of cycles to return (default 20)"}
        }
    },
    "describe_cyclus": {
        "function": describe_cyclus,
        "description": "Returns full details of a specific property's active cycle including all actions. Use to get complete information about a property's check-in/check-out status.",
        "parameters": {
            "object_id": {"type": "string", "description": "The property ID (object_id from huizen table)"}
        }
    },
    "list_cycli_acties": {
        "function": list_cycli_acties,
        "description": "Returns action history across all active cycles, optionally filtered by action type. Use to see planning overview or specific actions (e.g., all pending SCHOONMAAK).",
        "parameters": {
            "actie_type": {"type": "string", "description": "Filter by type: VOORINSPECTIE|UITCHECK|SCHOONMAAK|INCHECK|OVERDRACHT_EIGENAAR|REPARATIE (optional)"}
        }
    },
    "get_planning_priorities": {
        "function": get_planning_priorities,
        "description": "Returns AI-ready planning data with priority recommendations. Use to get intelligent suggestions for what to work on next.",
        "parameters": {
            "top_n": {"type": "integer", "description": "Number of top priority items to return (default 10)"}
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
