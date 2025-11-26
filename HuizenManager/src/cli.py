import sys
import os
import argparse
from datetime import datetime, date

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.manager import HuizenManager
from Shared.entities import Huis, Eigenaar, InhuurContract

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("==========================================")
    print("      🏠 HUIZENINVENTARIS MANAGER 🏠      ")
    print("==========================================")

def list_houses(manager, filter_str=None):
    conn = manager.db._get_connection()
    query = "SELECT id, object_id, adres, plaats, status FROM huizen"
    params = []
    
    if filter_str:
        query += " WHERE object_id LIKE ? OR adres LIKE ? OR plaats LIKE ?"
        f = f"%{filter_str}%"
        params = [f, f, f]
        
    query += " ORDER BY object_id LIMIT 50"
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    print("\n--- Huizen Lijst ---")
    print(f"{'ID':<6} {'Adres':<30} {'Plaats':<15} {'Status':<10}")
    print("-" * 65)
    for row in rows:
        print(f"{row['object_id']:<6} {row['adres']:<30} {row['plaats']:<15} {row['status']:<10}")
    print("-" * 65)
    if len(rows) == 50:
        print("(Toont eerste 50 resultaten)")

def view_house_details(manager):
    obj_id = input("Voer Object ID in (bijv. 0011): ").strip()
    
    # Find ID from Object ID
    conn = manager.db._get_connection()
    row = conn.execute("SELECT id FROM huizen WHERE object_id = ?", (obj_id,)).fetchone()
    conn.close()
    
    if not row:
        print("❌ Huis niet gevonden.")
        return

    huis_id = row['id']
    huis = manager.get_huis(huis_id)
    contract = manager.get_active_contract(huis_id)
    
    print("\n--- Huis Details ---")
    print(f"Object ID:   {huis.object_id}")
    print(f"Adres:       {huis.adres}")
    print(f"Postcode:    {huis.postcode}")
    print(f"Plaats:      {huis.plaats}")
    print(f"Type:        {huis.woning_type}")
    print(f"Status:      {huis.status}")
    print(f"Slaapkamers: {huis.aantal_sk}")
    print(f"Personen:    {huis.aantal_pers}")
    
    if contract:
        print("\n--- Actief Contract ---")
        print(f"Start Datum: {contract.start_date}")
        print(f"Kale Huur:   €{contract.kale_huur:.2f}")
        print(f"Totale Huur: €{contract.totale_huur:.2f}")
        
        # Get Owner Name
        if contract.eigenaar_id:
            conn = manager.db._get_connection()
            owner = conn.execute("SELECT naam FROM eigenaren WHERE id = ?", (contract.eigenaar_id,)).fetchone()
            conn.close()
            if owner:
                print(f"Eigenaar:    {owner['naam']}")
    else:
        print("\n⚠️ Geen actief contract gevonden.")

    input("\nDruk op Enter om door te gaan...")

def add_new_house(manager):
    print("\n--- Nieuw Huis Toevoegen ---")
    
    # Auto-generate Object ID
    object_id = manager.get_next_object_id()
    print(f"Nieuw Object ID: {object_id} (Automatisch gegenereerd)")
    
    adres = input("Adres: ").strip()
    postcode = input("Postcode: ").strip()
    plaats = input("Plaats: ").strip()
    
    try:
        huis = Huis(
            id=None,
            object_id=object_id,
            adres=adres,
            postcode=postcode,
            plaats=plaats,
            status='active'
        )
        manager.add_huis(huis)
        print(f"✅ Huis succesvol toegevoegd met ID {object_id}!")
    except Exception as e:
        print(f"❌ Fout bij toevoegen huis: {e}")
    
    input("\nDruk op Enter om door te gaan...")

def main_menu():
    manager = HuizenManager()
    
    while True:
        clear_screen()
        print_header()
        print("1. Toon Alle Huizen")
        print("2. Zoek Huis")
        print("3. Bekijk Huis Details")
        print("4. Nieuw Huis Toevoegen")
        print("5. Exporteer naar Excel")
        print("q. Afsluiten")
        
        choice = input("\nKies een optie: ").strip().lower()
        
        if choice == '1':
            list_houses(manager)
            input("\nDruk op Enter om door te gaan...")
        elif choice == '2':
            term = input("Zoekterm (ID/Adres/Plaats): ")
            list_houses(manager, term)
            input("\nDruk op Enter om door te gaan...")
        elif choice == '3':
            view_house_details(manager)
        elif choice == '4':
            add_new_house(manager)
        elif choice == '5':
            print("\n--- Exporteer naar Excel ---")
            print("Beschikbare tabellen: huizen, eigenaren, inhuur_contracten, clients, contracts, bookings")
            table_name = input("Welke tabel wil je exporteren? (standaard: huizen): ").strip()
            if not table_name:
                table_name = "huizen"
            
            print(f"Export tool wordt uitgevoerd voor '{table_name}'...")
            # Use default output path logic in db_export_tool.py
            os.system(f"{sys.executable} HuizenManager/src/db_export_tool.py {table_name}")
            input("\nDruk op Enter om door te gaan...")
        elif choice == 'q':
            print("Tot ziens!")
            break

if __name__ == "__main__":
    main_menu()
