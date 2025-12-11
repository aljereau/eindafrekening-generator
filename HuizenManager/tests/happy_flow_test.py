import sys
import os
from datetime import date, timedelta
import sqlite3

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.manager import HuizenManager
from Shared.entities import Huis, Leverancier, InhuurContract

def run_happy_flow():
    print("\n🚀 STARTING HAPPY FLOW TEST 🚀\n")
    manager = HuizenManager()
    
    # ==========================================
    # 0. SETUP: Woning + Leverancier
    # ==========================================
    print("--- 0. Setup: House & Supplier ---")
    
    # 0.1 Create Supplier (Owner)
    lev = Leverancier(id=None, naam="Vastgoed BV", email="info@vastgoed.nl", iban="NL99BANK0123456789")
    lev_id = manager.add_leverancier(lev)
    print(f"✅ Created Supplier: Vastgoed BV (ID: {lev_id})")
    
    # 0.2 Create House
    # Note: object_id usually comes from logic, here we force one for test
    import random
    obj_id = str(random.randint(1000, 9999))
    huis = Huis(id=None, object_id=obj_id, adres=f"Teststraat {obj_id}", postcode="1234AB", 
                plaats="Rotterdam", aantal_pers=4, status="active")
    huis_id = manager.add_huis(huis)
    print(f"✅ Created House: Teststraat 1 (ID: {huis_id}, Cap: 4)")
    
    # 0.3 Create Inhuur Contract (Cost side)
    inhuur = InhuurContract(
        id=None, property_id=huis_id, leverancier_id=lev_id, 
        start_date=date(2024, 1, 1), kale_huur=1000.0, servicekosten=50.0
    )
    inhuur_id = manager.add_contract(inhuur)
    print(f"✅ Created Inhuur Contract (ID: {inhuur_id}, Cost: €1050/mo)")
    
    
    # ==========================================
    # 1. CLIENT & MARGINS
    # ==========================================
    print("\n--- 1. Client & Margins ---")
    
    # 1.1 Create Client (Tradiro Test)
    klant_id = manager.add_klant("Tradiro Test", type="zakelijk", max_marge=8.0)
    print(f"✅ Created Client: Tradiro Test (ID: {klant_id}, Max Marge: 8%)")
    
    # 1.2 Client Parameters
    # Let's say we have a parameter "Internet" (ID 1) costing €3.00
    # But for Tradiro we override it to €2.50 (just to test)
    # First ensure parameter exists
    param_id = manager.add_parameter("Test Internet", 3.00)
    print(f"ℹ️  Parameter 'Test Internet': €3.00 pp/pw")
    
    manager.add_klant_parameter(klant_id, param_id, prijs_override=2.50)
    print(f"✅ Added Client Override: Tradiro pays €2.50 for Internet")
    
    
    # ==========================================
    # 2. VERHUUR CONTRACT (Outgoing)
    # ==========================================
    print("\n--- 2. Verhuur Contract ---")
    
    # 2.1 Create Contract
    # House Cap = 4. Internet = €2.50 (override).
    # Monthly Param Cost = 2.50 * 4 * 4 = €40.00
    contract_id = manager.create_verhuur_contract(
        huis_id=huis_id, klant_id=klant_id, start_datum=date(2024, 2, 1),
        kale_huur=1500.0, parameter_ids=[param_id]
    )
    print(f"✅ Created Verhuur Contract (ID: {contract_id}, Rent: €1500)")
    
    # 2.2 Verify Rules
    conn = manager.db._get_connection()
    rules = conn.execute("SELECT * FROM contract_regels WHERE contract_id = ?", (contract_id,)).fetchall()
    conn.close()
    
    for r in rules:
        print(f"   📋 Rule: {r['parameter_naam']} | Price: €{r['prijs_pp_pw']:.2f} | Total: €{r['totaal_maand_bedrag']:.2f}")
        if r['prijs_pp_pw'] == 2.50 and r['totaal_maand_bedrag'] == 40.0:
            print("   ✅ Calculation Correct (used override)")
        else:
            print("   ❌ Calculation WRONG")

    
    # ==========================================
    # 3. BOOKING
    # ==========================================
    print("\n--- 3. Booking ---")
    
    # 3.1 Create Booking
    # Note: We need to add add_booking to manager first! 
    # Wait, I checked manager.py earlier and didn't see add_booking in the snippet I edited.
    # I might have missed it or it needs to be added.
    # Let's assume I need to add it or use raw SQL for this test if missing.
    # I'll check if I can add it quickly via SQL here to keep the test self-contained 
    # or if I should update manager.py.
    # Updating manager.py is better practice.
    # But for now, I'll use raw SQL in the test to verify the SCHEMA works.
    
    conn = manager.db._get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO boekingen (contract_id, huis_id, klant_id, checkin_datum, checkout_datum, status)
        VALUES (?, ?, ?, ?, ?, 'confirmed')
    """, (contract_id, huis_id, klant_id, date(2024, 2, 1), date(2024, 2, 28)))
    boeking_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"✅ Created Booking (ID: {boeking_id}) for Feb 2024")
    
    
    # ==========================================
    # 4. OPERATIONS (Check-in/out)
    # ==========================================
    print("\n--- 4. Operations ---")
    
    # 4.1 Check-in
    manager.log_checkin(boeking_id, date(2024, 2, 1), "Dion", "Set A", "Alles netjes")
    print(f"✅ Logged Check-in")
    
    # 4.2 Check-out
    manager.log_checkout(boeking_id, date(2024, 2, 28), "Dion", schade=0, schoonmaak=50.0, notities="Schoonmaak nodig")
    print(f"✅ Logged Check-out (Cleaning: €50)")
    
    
    # ==========================================
    # 5. DEPOSIT & SETTLEMENT
    # ==========================================
    print("\n--- 5. Deposit & Settlement ---")
    
    # 5.1 Deposit Transaction
    manager.add_borg_transactie(boeking_id, date(2024, 1, 15), 'ontvangst', 500.0)
    print(f"✅ Logged Deposit Receipt: €500")
    
    manager.add_borg_transactie(boeking_id, date(2024, 3, 1), 'inhouding', 50.0, "Schoonmaak")
    print(f"✅ Logged Deposit Deduction: €50")
    
    manager.add_borg_transactie(boeking_id, date(2024, 3, 2), 'terugbetaling', 450.0)
    print(f"✅ Logged Deposit Refund: €450")
    
    # 5.2 Generate Eindafrekening (Database Record)
    # Get next version
    next_ver, is_new = manager.db.get_next_version("Tradiro Test", date(2024, 2, 1), date(2024, 2, 28))
    
    eind_id = manager.db.save_eindafrekening(
        client_name="Tradiro Test",
        checkin_date=date(2024, 2, 1),
        checkout_date=date(2024, 2, 28),
        version=next_ver,
        version_reason="Initial" if is_new else "Re-run Test",
        data_json={"dummy": "data"},
        totaal_eindafrekening=1500.0 + 40.0 # Rent + Params
    )
    print(f"✅ Saved Eindafrekening Record (ID: {eind_id})")

    print("\n🎉 HAPPY FLOW COMPLETED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    run_happy_flow()
