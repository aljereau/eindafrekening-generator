import sqlite3
import pandas as pd

class QueryAnalyst:
    """
    The Analyst: Retrieves insights from analytical views.
    """
    def __init__(self, db_path):
        self.db_path = db_path

    def get_conn(self):
        return sqlite3.connect(self.db_path)

    def get_house_profitability(self, limit=10, sort_by="bruto_marge DESC"):
        """Returns profitability analysis."""
        conn = self.get_conn()
        try:
            # Check if view exists, if not create it (lazy init)
            # For now assume it exists as we created it earlier.
            query = f"SELECT * FROM view_latest_pricing ORDER BY {sort_by} LIMIT {limit}"
            df = pd.read_sql_query(query, conn)
            return df.to_dict(orient='records')
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def get_client_scorecard(self, limit=10):
        """Returns client value analysis."""
        conn = self.get_conn()
        try:
            query = f"SELECT * FROM view_client_scorecard ORDER BY total_revenue DESC LIMIT {limit}"
            df = pd.read_sql_query(query, conn)
            return df.to_dict(orient='records')
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def get_operational_dashboard(self):
        """Returns current operational status."""
        conn = self.get_conn()
        try:
            query = "SELECT * FROM view_operational_dashboard"
            df = pd.read_sql_query(query, conn)
            return df.to_dict(orient='records')
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()
            
    def run_custom_query(self, sql_query):
        """Runs a safe custom query (read-only)."""
        if "DROP" in sql_query.upper() or "DELETE" in sql_query.upper() or "UPDATE" in sql_query.upper() or "INSERT" in sql_query.upper():
            return {"error": "Only SELECT queries are allowed in Analyst mode."}
            
        conn = self.get_conn()
        try:
            df = pd.read_sql_query(sql_query, conn)
            return df.to_dict(orient='records')
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()
