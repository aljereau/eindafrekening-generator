import sqlite3
import os
import sys
from datetime import datetime, timedelta, date
import random

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Default to mock, but allow override via CLI
if len(sys.argv) > 1:
    DB_PATH = sys.argv[1]
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_mock.db')

INSPECTORS = ['Alina', 'Kuba', 'Dion', 'Anna', 'Ricky']

POSITIVE_NOTES = [
    "Huis in perfecte staat achtergelaten.",
    "Huurder was erg behulpzaam.",
    "Alles schoon en netjes.",
    "Geen bijzonderheden, prima oplevering.",
    "Sleutels netjes op tafel, alles in orde.",
    "Keurig bewoond geweest.",
    "Tuin ligt er prachtig bij.",
    "Geen schade geconstateerd, top.",
    "Huis ruikt fris."
]

NEGATIVE_NOTES = [
    "Huis erg vies achtergelaten.",
    "Sterke rooklucht in de woonkamer.",
    "Veel afval in de tuin achtergelaten.",
    "Meubels verplaatst en krassen op de vloer.",
    "Badkamer heeft dieptereiniging nodig.",
    "Etensresten in de koelkast, niet schoongemaakt.",
    "Ramen staan open, regen naar binnen gekomen.",
    "Hondenharen op de bank.",
    "Vlekken in het tapijt.",
    "Afwasmachine niet uitgeruimd."
]

MAINTENANCE_NOTES = [
    "CV-ketel maakt een raar geluid, check nodig.",
    "Kraan in de keuken lekt.",
    "Gordijn in slaapkamer klemt.",
    "Verf bladdert af in de gang.",
    "Lamp in de hal is stuk.",
    "Slot van de voordeur gaat stroef.",
    "Doucheputje loopt slecht door.",
    "Raam sluit niet goed.",
    "Schimmelvorming in de badkamer."
]

def get_inspection_note(client_name, inspection_type):
    if random.random() < 0.3: return None
    
    if client_name == 'Tradiro' and inspection_type == 'uitcheck':
        if random.random() < 0.6: return random.choice(NEGATIVE_NOTES)
            
    if client_name == 'Expats Inc':
        if random.random() < 0.5: return random.choice(MAINTENANCE_NOTES)
            
    if 'Jansen' in client_name or 'Vries' in client_name:
        if random.random() < 0.7: return random.choice(POSITIVE_NOTES)
            
    category = random.choice(['pos', 'neg', 'maint', 'none'])
    if category == 'pos': return random.choice(POSITIVE_NOTES)
    if category == 'neg': return random.choice(NEGATIVE_NOTES)
    if category == 'maint': return random.choice(MAINTENANCE_NOTES)
    return None

def get_conn():
    return sqlite3.connect(DB_PATH)

def clear_transactional_data(conn):
    cursor = conn.cursor()
    # Only clear transactional tables, keep static data (houses, clients, contracts)
    tables = ['damages', 'meter_readings', 'inspections', 'uitcheck_details', 'checkins', 'checkouts', 'boekingen']
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    print("🧹 Cleared existing transactional data (kept houses/clients).")

def get_existing_data(conn):
    cursor = conn.cursor()
    
    # Get Houses
    cursor.execute("SELECT id, adres, postcode, plaats, object_id FROM huizen")
    houses = {row[0]: {'adres': row[1], 'postcode': row[2], 'plaats': row[3], 'object_id': row[4]} for row in cursor.fetchall()}
    
    # Get Clients
    cursor.execute("SELECT id, naam, type FROM klanten")
    clients = {row[0]: {'naam': row[1], 'type': row[2]} for row in cursor.fetchall()}
    
    # Get Contracts (to link correct client to house if exists)
    # Map house_id -> list of (client_id, start, end, price)
    cursor.execute("SELECT huis_id, klant_id, start_datum, eind_datum, kale_huur FROM verhuur_contracten")
    contracts = {}
    for row in cursor.fetchall():
        hid = row[0]
        if hid not in contracts: contracts[hid] = []
        contracts[hid].append({
            'klant_id': row[1],
            'start': row[2],
            'end': row[3],
            'price': row[4]
        })
        
    return houses, clients, contracts

def generate_history(conn, houses, clients, contracts):
    cursor = conn.cursor()
    
    start_simulation = date(2023, 1, 1)
    end_simulation = date(2025, 12, 31) # Generate up to end of 2025
    today = date.today()
    
    total_bookings = 0
    client_ids = list(clients.keys())
    
    if not client_ids:
        print("⚠️ No clients found! Cannot generate bookings.")
        return

    for huis_id, house_info in houses.items():
        current_date = start_simulation
        
        meter_gas = random.randint(1000, 5000)
        meter_water = random.randint(500, 2000)
        meter_elec = random.randint(2000, 6000)
        
        # Check if this house has specific contracts
        house_contracts = contracts.get(huis_id, [])
        
        # Sort contracts by date if any
        # For now, we just use them as a pool of "preferred" clients/periods
        
        while current_date < end_simulation:
            vacancy = random.randint(0, 14) # Short vacancy
            current_date += timedelta(days=vacancy)
            
            if current_date > end_simulation: break
                
            duration_days = random.randint(30, 365) # Longer stays possible
            end_date = current_date + timedelta(days=duration_days)
            
            # Determine Client
            # If we have a contract covering this period, use that client
            # Otherwise random
            klant_id = None
            price = None
            
            # Simple contract matching
            for c in house_contracts:
                c_start = datetime.strptime(c['start'], '%Y-%m-%d').date() if c['start'] else date.min
                c_end = datetime.strptime(c['end'], '%Y-%m-%d').date() if c['end'] else date.max
                
                # Overlap?
                if (current_date <= c_end) and (end_date >= c_start):
                    klant_id = c['klant_id']
                    price = c['price']
                    break
            
            if not klant_id:
                klant_id = random.choice(client_ids)
                price = random.randint(800, 2500) # Fallback price
            
            # Status
            if end_date < today: status = 'completed'
            elif current_date <= today <= end_date: status = 'active'
            else: status = 'confirmed'
            
            # Insert Booking
            cursor.execute("""
                INSERT INTO boekingen (huis_id, klant_id, checkin_datum, checkout_datum, status, totale_huur_factuur)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (huis_id, klant_id, current_date, end_date, status, price))
            booking_id = cursor.lastrowid
            total_bookings += 1
            
            inspector = random.choice(INSPECTORS)
            if klant_id not in clients:
                # Fallback if client from contract is missing in clients table (shouldn't happen if DB is consistent)
                klant_id = random.choice(client_ids)
                
            client_name = clients[klant_id]['naam']
            
            # Checkin (if in past or near future)
            if current_date <= today + timedelta(days=30):
                cursor.execute("""
                    INSERT INTO checkins (boeking_id, datum, uitgevoerd_door, sleutelset)
                    VALUES (?, ?, ?, ?)
                """, (booking_id, current_date, inspector, f"Set {random.randint(1,3)}"))
                
                note = get_inspection_note(client_name, 'incheck')
                cursor.execute("""
                    INSERT INTO inspections (booking_id, inspection_type, planned_date, inspector, status, notes)
                    VALUES (?, 'incheck', ?, ?, 'completed', ?)
                """, (booking_id, current_date, inspector, note))
            
            # Meters (Generate usage)
            cons_factor = duration_days / 30.0
            gas_used = int(random.randint(50, 150) * cons_factor)
            water_used = int(random.randint(10, 30) * cons_factor)
            elec_used = int(random.randint(200, 400) * cons_factor)
            
            # Only record meters if checkin happened
            if current_date <= today + timedelta(days=30):
                cursor.execute("INSERT INTO meter_readings (booking_id, reading_type, start_value, end_value, tariff) VALUES (?, 'gas', ?, ?, 1.50)", (booking_id, meter_gas, meter_gas + gas_used))
                cursor.execute("INSERT INTO meter_readings (booking_id, reading_type, start_value, end_value, tariff) VALUES (?, 'water', ?, ?, 0.80)", (booking_id, meter_water, meter_water + water_used))
                cursor.execute("INSERT INTO meter_readings (booking_id, reading_type, start_value, end_value, tariff) VALUES (?, 'electricity', ?, ?, 0.40)", (booking_id, meter_elec, meter_elec + elec_used))
            
            meter_gas += gas_used
            meter_water += water_used
            meter_elec += elec_used
            
            # Checkout (if completed)
            if status == 'completed':
                schade_total = 0
                # Chance of damage
                if random.random() < 0.2: # 20% chance
                    schade_total = random.choice([150, 250, 500, 1200])
                
                cursor.execute("""
                    INSERT INTO checkouts (boeking_id, datum_gepland, datum_werkelijk, uitgevoerd_door, schoonmaak_kosten, schade_geschat)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (booking_id, end_date, end_date, inspector, random.choice([0, 150, 250]), schade_total))
                
                note = get_inspection_note(client_name, 'uitcheck')
                cursor.execute("""
                    INSERT INTO inspections (booking_id, inspection_type, planned_date, inspector, status, notes)
                    VALUES (?, 'uitcheck', ?, ?, 'completed', ?)
                """, (booking_id, end_date, inspector, note))
                
                cursor.execute("""
                    INSERT INTO uitcheck_details (booking_id, actual_date, damage_reported, settlement_status)
                    VALUES (?, ?, ?, ?)
                """, (booking_id, end_date, schade_total > 0, 'completed'))
                
                if schade_total > 0:
                    damage_items = [("Gebroken lamp", 50), ("Vlek in tapijt", 100), ("Gat in muur", 150), ("Kras op vloer", 200), ("Ontbrekende sleutel", 50), ("Beschadigde deur", 250)]
                    remaining = schade_total
                    while remaining > 0:
                        item, cost = random.choice(damage_items)
                        if cost > remaining: cost = remaining
                        cursor.execute("INSERT INTO damages (booking_id, description, estimated_cost) VALUES (?, ?, ?)", (booking_id, item, cost))
                        remaining -= cost
                        
            elif status == 'active' or status == 'confirmed':
                # Future checkout
                cursor.execute("INSERT INTO checkouts (boeking_id, datum_gepland) VALUES (?, ?)", (booking_id, end_date))
                cursor.execute("INSERT INTO inspections (booking_id, inspection_type, planned_date, inspector, status) VALUES (?, 'uitcheck', ?, ?, 'planned')", (booking_id, end_date, inspector))

            current_date = end_date
            
    conn.commit()
    print(f"📅 Generated history: {total_bookings} bookings from 2023 to 2025+.")

if __name__ == "__main__":
    conn = get_conn()
    clear_transactional_data(conn)
    
    # Load existing real data
    houses, clients, contracts = get_existing_data(conn)
    print(f"🏠 Loaded {len(houses)} houses, {len(clients)} clients, {len(contracts)} contracts.")
    
    if len(houses) == 0:
        print("⚠️ No houses found. Please run sync_houses.py first.")
    else:
        generate_history(conn, houses, clients, contracts)
        
    conn.close()
    print("✅ Robust mock data population complete.")
