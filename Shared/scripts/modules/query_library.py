import sqlite3
import json
import pandas as pd

class QueryLibrary:
    """
    Manages a library of reusable SQL queries.
    """
    def __init__(self, db_path):
        self.db_path = db_path

    def get_conn(self):
        return sqlite3.connect(self.db_path)

    def add_query(self, name, description, sql_template, parameters=None):
        """Saves a new query to the library."""
        conn = self.get_conn()
        cursor = conn.cursor()
        try:
            params_json = json.dumps(parameters) if parameters else "[]"
            cursor.execute("""
                INSERT INTO saved_queries (name, description, sql_template, parameters)
                VALUES (?, ?, ?, ?)
            """, (name, description, sql_template, params_json))
            conn.commit()
            return {"success": True, "id": cursor.lastrowid}
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def find_queries(self, search_term):
        """Searches queries by name or description."""
        conn = self.get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            term = f"%{search_term}%"
            cursor.execute("""
                SELECT id, name, description, parameters 
                FROM saved_queries 
                WHERE name LIKE ? OR description LIKE ?
            """, (term, term))
            rows = [dict(row) for row in cursor.fetchall()]
            return rows
        finally:
            conn.close()

    def execute_query(self, query_id, param_values=None):
        """Executes a saved query with provided values."""
        conn = self.get_conn()
        cursor = conn.cursor()
        try:
            # Fetch query
            cursor.execute("SELECT sql_template, parameters FROM saved_queries WHERE id = ?", (query_id,))
            row = cursor.fetchone()
            if not row:
                return {"error": "Query not found"}
            
            sql_template = row[0]
            # stored_params = json.loads(row[1]) # Not strictly needed for execution if values are passed in order
            
            # If param_values is a dict, we might need to be careful if SQL uses ? placeholders.
            # SQLite uses ? for positional args.
            # If the user provides a list, we use it directly.
            # If the user provides a dict, we might need to map it (but that requires named params in SQL like :name).
            # For simplicity, let's assume the AI generates the SQL with ? and provides a LIST of values.
            
            values = param_values if param_values else []
            
            df = pd.read_sql_query(sql_template, conn, params=values)
            return df.to_dict(orient='records')
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()
