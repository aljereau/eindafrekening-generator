
import sys
import os
from pathlib import Path
import sqlite3

# Define database path
DB_PATH = Path("/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/database/ryanrent_mock.db")

def analyze_keys():
    if not DB_PATH.exists():
        print(f"Error: DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Analyzing {len(tables)} tables for property references...\n")
    
    potential_keys = ['huis', 'property', 'object', 'woning']
    
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        
        # Look for columns that might refer to a house
        relevant_cols = []
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            
            # Check if column name contains key terms
            if any(key in col_name.lower() for key in potential_keys):
                relevant_cols.append(f"{col_name} ({col_type})")
        
        if relevant_cols:
            print(f"Table: {table}")
            for rc in relevant_cols:
                print(f"  - {rc}")
            print("")
            
    conn.close()

if __name__ == "__main__":
    analyze_keys()
