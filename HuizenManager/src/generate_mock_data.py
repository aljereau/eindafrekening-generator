import shutil
import sqlite3
import random
from datetime import date, timedelta, datetime
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.manager import HuizenManager
from Shared.entities import InhuurContract

# Determine paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
shared_db_dir = os.path.join(project_root, 'Shared', 'database')
local_db_dir = os.path.join(current_dir, 'database')

# Ensure local db dir exists
os.makedirs(local_db_dir, exist_ok=True)

DB_ORIGINAL = os.path.join(shared_db_dir, "ryanrent_core.db")
DB_MOCK = os.path.join(local_db_dir, "ryanrent_mock.db")

def setup_mock_db():
    print(f"📦 Copying {DB_ORIGINAL} to {DB_MOCK}...")
    if os.path.exists(DB_MOCK):
        os.remove(DB_MOCK)
    shutil.copy2(DB_ORIGINAL, DB_MOCK)
    
    conn = sqlite3.connect(DB_MOCK)
    cursor = conn.cursor()
    
    print("🧹 Clearing operational tables...")
    tables_to_clear = [
        "inhuur_contracten", "verhuur_contracten", "contract_regels",
        "boekingen", "borg_transacties", "checkins", "checkouts", 
        "eindafrekeningen"
    ]
    for table in tables_to_clear:
        cursor.execute(f"DELETE FROM {table}")
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        
    conn.commit()
    conn.close()
    print("✅ Mock DB ready for population.")

def generate_data():
    # Initialize Manager with Mock DB
    from Shared.database import Database
    db = Database(DB_MOCK)
    manager = HuizenManager(db)
    
    # 1. Fetch Static Entities (Read & Close)
    conn = db._get_connection()
    huizen = [dict(r) for r in conn.execute("SELECT * FROM huizen WHERE status='active'").fetchall()]
    leveranciers = [dict(r) for r in conn.execute("SELECT * FROM leveranciers").fetchall()]
    klanten = [dict(r) for r in conn.execute("SELECT * FROM klanten").fetchall()]
    parameters = [dict(r) for r in conn.execute("SELECT * FROM parameters WHERE is_actief=1").fetchall()]
    conn.close()
    
    if not huizen or not leveranciers or not klanten:
        print("❌ Missing static data (houses/suppliers/clients). Import real data first.")
        return

    print(f"ℹ️  Found {len(huizen)} houses, {len(leveranciers)} suppliers, {len(klanten)} clients.")
    
    start_date = date(2022, 1, 1)
    end_date = date(2025, 12, 31)
    today = date.today()
    
    print("🚀 Generating 3 years of history...")
    
    stats = {
        "contracts_in": 0,
        "contracts_out": 0,
        "bookings": 0,
        "settlements": 0
    }

    for huis in huizen:
        huis_id = huis['id']
        capacity = huis['aantal_pers'] or 4
        
        # A. Create Inhuur Contract (Owner)
        lev = random.choice(leveranciers)
        base_rent = random.randint(800, 1500)
        
        # 10% chance of expiring soon (for testing alerts)
        contract_end = None
        if random.random() < 0.1:
            contract_end = today + timedelta(days=random.randint(5, 60))
        
        inhuur = InhuurContract(
            id=None, property_id=huis_id, leverancier_id=lev['id'],
            start_date=start_date, end_date=contract_end,
            kale_huur=base_rent, servicekosten=50.0, voorschot_gwe=150.0,
            internet_kosten=40.0, inventaris_kosten=20.0, afval_kosten=15.0,
            schoonmaak_kosten=0.0
        )
        manager.add_contract(inhuur)
        stats["contracts_in"] += 1
        
        # B. Create Verhuur Contracts & Bookings
        current_date = start_date
        
        while current_date < end_date:
            gap = random.randint(0, 14)
            current_date += timedelta(days=gap)
            if current_date >= end_date: break
            
            duration_months = random.randint(1, 6)
            booking_end = current_date + timedelta(days=duration_months*30)
            if booking_end > end_date: booking_end = end_date
            
            klant = random.choice(klanten)
            is_tradiro = "Tradiro" in klant['naam']
            margin = 8.0 if is_tradiro else 15.0
            
            service_cost = 0
            param_ids = []
            for p in parameters:
                if "Internet" in p['naam'] or "Afval" in p['naam']:
                    service_cost += p['prijs_pp_pw'] * capacity * 4
                    param_ids.append(p['id'])
            
            total_cost = (base_rent + 275) + service_cost # 275 = sum of extras
            price = total_cost / (1 - (margin/100.0))
            price = round(price, 2)
            
            # Create Verhuur Contract
            contract_id = manager.create_verhuur_contract(
                huis_id=huis_id, klant_id=klant['id'], start_datum=current_date,
                kale_huur=price, parameter_ids=param_ids
            )
            stats["contracts_out"] += 1
            
            # Create Booking (Manual Insert)
            status = 'confirmed'
            if booking_end < today: status = 'checked_out'
            elif current_date <= today <= booking_end: status = 'checked_in'
            
            # CHAOS: 5% chance of missing checkout (Ghost booking)
            is_ghost = False
            if status == 'checked_out' and random.random() < 0.05:
                status = 'checked_in' # Still checked in despite date passed
                is_ghost = True

            # Open short-lived connection for booking insert
            conn = db._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO boekingen (contract_id, huis_id, klant_id, checkin_datum, checkout_datum, status, totale_huur_factuur)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (contract_id, huis_id, klant['id'], current_date, booking_end, status, price * duration_months))
            boeking_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            stats["bookings"] += 1
            
            # Operations
            if status in ['checked_in', 'checked_out']:
                manager.log_checkin(boeking_id, current_date, "Mock Bot", "Standard Set")
                
                # Deposit Receipt (Always)
                manager.add_borg_transactie(boeking_id, current_date, 'ontvangst', 500.0)
                
            if status == 'checked_out' and not is_ghost:
                damage = 0
                cleaning = 0
                if random.random() < 0.2:
                    damage = random.randint(50, 500)
                    cleaning = 50
                
                manager.log_checkout(boeking_id, booking_end, "Mock Bot", damage, cleaning)
                
                # CHAOS: 10% chance of forgetting to refund deposit
                if random.random() > 0.1:
                    if damage > 0 or cleaning > 0:
                        manager.add_borg_transactie(boeking_id, booking_end, 'inhouding', damage + cleaning, "Schade/Schoonmaak")
                    manager.add_borg_transactie(boeking_id, booking_end, 'terugbetaling', 500.0 - damage - cleaning)
                
                # Eindafrekening
                next_ver, is_new = manager.db.get_next_version(klant['naam'], current_date, booking_end)
                
                manager.db.save_eindafrekening(
                    client_name=klant['naam'],
                    checkin_date=current_date,
                    checkout_date=booking_end,
                    version=next_ver,
                    version_reason="Final" if is_new else "Correction",
                    data_json={"mock": True},
                    totaal_eindafrekening=price * duration_months
                )
                stats["settlements"] += 1

            current_date = booking_end
    print("\n🎉 Mock Data Generation Complete!")
    print(f"   - Inhuur Contracts: {stats['contracts_in']}")
    print(f"   - Verhuur Contracts: {stats['contracts_out']}")
    print(f"   - Bookings: {stats['bookings']}")
    print(f"   - Settlements: {stats['settlements']}")

if __name__ == "__main__":
    setup_mock_db()
    generate_data()
