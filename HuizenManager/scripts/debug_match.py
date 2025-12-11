import sys
import os
import pandas as pd
import sqlite3

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from HuizenManager.src.manager import HuizenManager

def debug_match():
    manager = HuizenManager()
    conn = manager.db._get_connection()
    
    # Check House IDs
    print("--- Checking House IDs ---")
    ids = conn.execute("SELECT object_id FROM huizen LIMIT 5").fetchall()
    print("DB House IDs:", [r['object_id'] for r in ids])
    
    # Check Tradiro
    print("\n--- Checking Tradiro ---")
    klant = conn.execute("SELECT id, naam FROM klanten WHERE naam LIKE '%Tradiro%'").fetchone()
    print(f"DB Tradiro: {dict(klant) if klant else 'Not Found'}")
    
    # Check CSV Row 2 (Tradiro)
    df = pd.read_csv('Archive/Huizenlijst.csv', sep=';')
    row = df.iloc[1] # Should be 0022, Tradiro
    print(f"\nCSV Row 1 (Index 1):")
    print(f"Object ID: '{row['Object_ID']}'")
    print(f"Huurder: '{row['Huurder']}'")
    
    # Simulate Match
    obj_id = str(row['Object_ID']).zfill(4)
    print(f"Formatted ID: '{obj_id}'")
    
    huis = conn.execute("SELECT id FROM huizen WHERE object_id = ?", (obj_id,)).fetchone()
    print(f"Found House: {dict(huis) if huis else 'No'}")
    
    huurder = row['Huurder']
    klant_match = conn.execute("SELECT id FROM klanten WHERE naam LIKE ?", (f"%{huurder}%",)).fetchone()
    print(f"Found Client Match: {dict(klant_match) if klant_match else 'No'}")

    conn.close()

if __name__ == "__main__":
    debug_match()
