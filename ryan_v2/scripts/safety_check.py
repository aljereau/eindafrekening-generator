
import sqlite3
from pathlib import Path

DB_PATH = Path("/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/database/ryanrent_mock.db")

def check_remaining_dependencies():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("Checking for remaining Integer Foreign Keys to huizen...")
    found_dependencies = []
    
    for table in tables:
        if table in ['huizen', 'huizen_archief', 'sqlite_sequence', 'schema_versions']:
            continue
            
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        for col in columns:
            name = col[1]
            col_type = col[2]
            
            # Look for likely FK names
            if name in ['huis_id', 'property_id', 'woning_id'] and 'INT' in col_type.upper():
                found_dependencies.append(f"{table}.{name} ({col_type})")
            
            # Also check if they found 'object_id' yet
            has_object_id = any(c[1] == 'object_id' for c in columns)
            if name in ['huis_id', 'property_id'] and not has_object_id:
                 print(f"WARNING: {table} has {name} but NO object_id column yet!")

    if found_dependencies:
        print("\nFound remaining Integer FKs (Legacy):")
        for dep in found_dependencies:
            print(f"  - {dep}")
    else:
        print("\nNo obvious remaining Integer FKs found.")
        
    conn.close()

if __name__ == "__main__":
    check_remaining_dependencies()
