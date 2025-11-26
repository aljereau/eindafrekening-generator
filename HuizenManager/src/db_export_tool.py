import pandas as pd
import sqlite3
import os
import sys
import argparse
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from HuizenManager.src.manager import HuizenManager

def export_table(table_name, output_file=None):
    manager = HuizenManager()
    db_path = manager.db.db_path
    
    print(f"--- Exporting Table: {table_name} ---")
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Check if table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            print(f"❌ Table '{table_name}' not found in database.")
            print("Available tables:")
            tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            for t in tables:
                print(f" - {t[0]}")
            return

        # Read table
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        
        if df.empty:
            print(f"⚠️ Table '{table_name}' is empty.")
        else:
            print(f"✅ Fetched {len(df)} rows.")
            
        # Determine output file
        if not output_file:
            # Default to HuizenManager/outputs directory
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs'))
            os.makedirs(base_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(base_dir, f"{table_name}_export_{timestamp}.xlsx")
            
        # Save to Excel
        print(f"Saving to: {output_file}...")
        df.to_excel(output_file, index=False)
        print("✅ Export successful!")
        
    except Exception as e:
        print(f"❌ Error exporting table: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export database table to Excel")
    parser.add_argument("table", nargs="?", default="huizen", help="Name of the table to export (default: huizen)")
    parser.add_argument("--output", "-o", help="Output Excel file path")
    
    args = parser.parse_args()
    
    export_table(args.table, args.output)
