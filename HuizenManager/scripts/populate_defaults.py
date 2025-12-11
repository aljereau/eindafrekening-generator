import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.manager import HuizenManager

def populate():
    manager = HuizenManager()
    
    print("--- Populating Parameters ---")
    
    # Define Parameters
    params = [
        ("RR Internet Kosten", 3.00),
        ("RR Inventaris & Inrichting", 7.50),
        ("RR Vuilcontainers/Afval", 3.00),
        ("Schades & Onderhoud Object", 3.00),
        ("RR Aanschaf inventaris", 1.60),
        ("Gemeentelijke heffingen Object", 2.60),
        ("RR Operationele Kosten", 4.00)
    ]
    
    for name, price in params:
        # Check if exists first to avoid duplicates if run multiple times
        # (Naive check by name)
        conn = manager.db._get_connection()
        exists = conn.execute("SELECT id FROM parameters WHERE naam = ?", (name,)).fetchone()
        conn.close()
        
        if not exists:
            manager.add_parameter(name, price)
            print(f"✅ Added Parameter: {name} (€{price:.2f})")
        else:
            print(f"ℹ️ Parameter already exists: {name}")

    print("\n--- Populating Clients ---")
    
    # 1. Tradiro (Max Marge 8%)
    conn = manager.db._get_connection()
    tradiro = conn.execute("SELECT id FROM klanten WHERE naam = 'Tradiro'").fetchone()
    conn.close()
    
    if not tradiro:
        manager.add_klant("Tradiro", type="zakelijk", max_marge=8.0)
        print("✅ Added Client: Tradiro (Max Marge: 8%)")
    else:
        print("ℹ️ Client already exists: Tradiro")
        
    # 2. Standaard Klant (Min Marge 15%)
    conn = manager.db._get_connection()
    std = conn.execute("SELECT id FROM klanten WHERE naam = 'Standaard Klant'").fetchone()
    conn.close()
    
    if not std:
        manager.add_klant("Standaard Klant", type="particulier", min_marge=15.0)
        print("✅ Added Client: Standaard Klant (Min Marge: 15%)")
    else:
        print("ℹ️ Client already exists: Standaard Klant")

if __name__ == "__main__":
    populate()
