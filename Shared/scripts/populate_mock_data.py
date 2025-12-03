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

CITIES = ['Amsterdam', 'Rotterdam', 'Den Haag', 'Utrecht', 'Eindhoven', 'Tilburg', 'Groningen', 'Almere', 'Breda', 'Nijmegen']
STREETS = ['Kerkstraat', 'Dorpsstraat', 'Stationsweg', 'Hoofdstraat', 'Schoolstraat', 'Molenweg', 'Julianastraat', 'Wilhelminastraat', 'Nieuwstraat', 'Bergweg']

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

def clear_tables(conn):
    cursor = conn.cursor()
    tables = ['damages', 'meter_readings', 'inspections', 'uitcheck_details', 'checkins', 'checkouts', 'boekingen', 'klanten', 'huizen', 'leveranciers']
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    print("🧹 Cleared existing data.")

def populate_leveranciers(conn):
    leveranciers = [
        ('Eneco', 'klantenservice@eneco.nl', '010-1234567'),
        ('Vattenfall', 'info@vattenfall.nl', '020-7654321'),
        ('Ziggo', 'zakelijk@ziggo.nl', '088-1234567'),
        ('KPN', 'service@kpn.com', '0800-0402'),
        ('Schoonmaakbedrijf Frisse Start', 'info@frissestart.nl', '06-12345678'),
        ('Aannemer Bouwman', 'jan@bouwman.nl', '06-87654321'),
        ('Loodgieter Pietersen', 'info@pietersen.nl', '06-11223344'),
        ('IKEA Zakelijk', 'b2b@ikea.nl', '0900-2354532'),
        ('Coolblue', 'zakelijk@coolblue.nl', '010-7988999'),
        ('Gemeente Amsterdam', 'belastingen@amsterdam.nl', '14020')
    ]
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO leveranciers (naam, email, telefoonnummer) VALUES (?, ?, ?)", leveranciers)
    conn.commit()
    print(f"🚚 Inserted {len(leveranciers)} suppliers.")

def populate_huizen(conn):
    huizen = []
    # Generate 50 houses
    for i in range(1, 51):
        stad = random.choice(CITIES)
        straat = random.choice(STREETS)
        nummer = random.randint(1, 200)
        postcode = f"{random.randint(1000, 9999)} {random.choice(['AA', 'BB', 'CC', 'DD', 'EE', 'AB', 'XZ'])}"
        adres = f"{straat} {nummer}"
        obj_id = f"HUIS-{i:03d}"
        huizen.append((adres, stad, postcode, obj_id))
        
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO huizen (adres, plaats, postcode, object_id) VALUES (?, ?, ?, ?)", huizen)
    conn.commit()
    print(f"🏠 Inserted {len(huizen)} houses.")
    
    cursor.execute("SELECT id, adres FROM huizen")
    return {row[0]: row[1] for row in cursor.fetchall()}

def populate_klanten(conn):
    base_clients = [
        ('Tradiro', 'bureau', 'planning@tradiro.nl'),
        ('Strukton', 'bureau', 'info@strukton.com'),
        ('BAM Wonen', 'bureau', 'contact@bam.nl'),
        ('Expats Inc', 'bureau', 'housing@expats.com'),
        ('Randstad Wonen', 'bureau', 'info@randstadwonen.nl'),
        ('TechCorp', 'zakelijk', 'hr@techcorp.com'),
        ('Shell Expats', 'zakelijk', 'housing@shell.com'),
        ('ASML Housing', 'zakelijk', 'relocation@asml.com')
    ]
    
    # Add 12 private clients
    first_names = ['Jan', 'Piet', 'Klaas', 'Anna', 'Sophie', 'Emma', 'Daan', 'Lucas', 'Sem', 'Julia', 'Mila', 'Tess']
    last_names = ['Jansen', 'de Vries', 'Bakker', 'Visser', 'Smit', 'Meijer', 'de Jong', 'Mulder', 'Groot', 'Bos', 'Vos', 'Peters']
    
    for i in range(12):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = f"{name.lower().replace(' ', '.')}@example.com"
        base_clients.append((name, 'particulier', email))
        
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO klanten (naam, type, email) VALUES (?, ?, ?)", base_clients)
    conn.commit()
    print(f"👥 Inserted {len(base_clients)} clients.")
    
    cursor.execute("SELECT id FROM klanten")
    return [row[0] for row in cursor.fetchall()]

def generate_history(conn, huizen_map, klant_ids):
    cursor = conn.cursor()
    
    start_simulation = date(2022, 1, 1)
    end_simulation = date(2025, 12, 31)
    today = date.today()
    
    total_bookings = 0
    
    for huis_id, adres in huizen_map.items():
        current_date = start_simulation
        
        meter_gas = random.randint(1000, 5000)
        meter_water = random.randint(500, 2000)
        meter_elec = random.randint(2000, 6000)
        
        while current_date < end_simulation:
            vacancy = random.randint(0, 20)
            current_date += timedelta(days=vacancy)
            
            if current_date > end_simulation: break
                
            duration_days = random.randint(30, 180)
            end_date = current_date + timedelta(days=duration_days)
            
            klant_id = random.choice(klant_ids)
            
            if end_date < today: status = 'completed'
            elif current_date <= today <= end_date: status = 'active'
            else: status = 'confirmed'
                
            cursor.execute("""
                INSERT INTO boekingen (huis_id, klant_id, checkin_datum, checkout_datum, status)
                VALUES (?, ?, ?, ?, ?)
            """, (huis_id, klant_id, current_date, end_date, status))
            booking_id = cursor.lastrowid
            total_bookings += 1
            
            inspector = random.choice(INSPECTORS)
            
            # Checkin
            if current_date <= today + timedelta(days=7):
                cursor.execute("""
                    INSERT INTO checkins (boeking_id, datum, uitgevoerd_door, sleutelset)
                    VALUES (?, ?, ?, ?)
                """, (booking_id, current_date, inspector, f"Set {random.randint(1,3)}"))
                
                cursor.execute("SELECT naam FROM klanten WHERE id = ?", (klant_id,))
                client_name = cursor.fetchone()[0]
                note = get_inspection_note(client_name, 'incheck')
                
                cursor.execute("""
                    INSERT INTO inspections (booking_id, inspection_type, planned_date, inspector, status, notes)
                    VALUES (?, 'incheck', ?, ?, 'completed', ?)
                """, (booking_id, current_date, inspector, note))
            
            # Meters
            cons_factor = duration_days / 30.0
            gas_used = int(random.randint(50, 150) * cons_factor)
            water_used = int(random.randint(10, 30) * cons_factor)
            elec_used = int(random.randint(200, 400) * cons_factor)
            
            cursor.execute("INSERT INTO meter_readings (booking_id, reading_type, start_value, end_value, tariff) VALUES (?, 'gas', ?, ?, 1.50)", (booking_id, meter_gas, meter_gas + gas_used))
            meter_gas += gas_used
            
            cursor.execute("INSERT INTO meter_readings (booking_id, reading_type, start_value, end_value, tariff) VALUES (?, 'water', ?, ?, 0.80)", (booking_id, meter_water, meter_water + water_used))
            meter_water += water_used
            
            cursor.execute("INSERT INTO meter_readings (booking_id, reading_type, start_value, end_value, tariff) VALUES (?, 'electricity', ?, ?, 0.40)", (booking_id, meter_elec, meter_elec + elec_used))
            meter_elec += elec_used
            
            # Checkout
            if status == 'completed':
                schade_total = random.choice([0, 0, 0, 0, 150, 250, 500])
                
                cursor.execute("""
                    INSERT INTO checkouts (boeking_id, datum_gepland, datum_werkelijk, uitgevoerd_door, schoonmaak_kosten, schade_geschat)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (booking_id, end_date, end_date, inspector, random.choice([0, 150, 250]), schade_total))
                
                cursor.execute("SELECT naam FROM klanten WHERE id = ?", (klant_id,))
                client_name = cursor.fetchone()[0]
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
                        
            elif status == 'active':
                cursor.execute("INSERT INTO checkouts (boeking_id, datum_gepland) VALUES (?, ?)", (booking_id, end_date))
                cursor.execute("INSERT INTO inspections (booking_id, inspection_type, planned_date, inspector, status) VALUES (?, 'uitcheck', ?, ?, 'planned')", (booking_id, end_date, inspector))

            current_date = end_date
            
    conn.commit()
    print(f"📅 Generated history: {total_bookings} bookings from 2022 to 2025.")

if __name__ == "__main__":
    conn = get_conn()
    clear_tables(conn)
    populate_leveranciers(conn)
    huizen_map = populate_huizen(conn)
    klant_ids = populate_klanten(conn)
    generate_history(conn, huizen_map, klant_ids)
    conn.close()
    print("✅ Comprehensive mock data population complete.")
