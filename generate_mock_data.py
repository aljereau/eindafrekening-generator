import sqlite3
import random
from datetime import datetime, timedelta
import os

DB_PATH = 'database/ryanrent_core.db'

def create_connection():
    return sqlite3.connect(DB_PATH)

def clear_data(conn):
    cursor = conn.cursor()
    tables = [
        'uitchecks', 'inchecks', 'inspecties', 'schades', 'meterstanden',
        'checkouts', 'checkins', 'borg_transacties', 'klant_parameters',
        'contract_regels', 'boekingen', 'verhuur_contracten', 'inhuur_contracten',
        'leveranciers', 'klanten', 'huizen'
    ]
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        except sqlite3.OperationalError:
            pass # Table might not exist
    conn.commit()
    print("🧹 Database cleared.")

def generate_data(conn):
    cursor = conn.cursor()
    
    # --- 1. Huizen (Properties) ---
    cities = ['Amsterdam', 'Rotterdam', 'Utrecht', 'Den Haag', 'Eindhoven', 'Nunspeet', 'Zwolle']
    types = ['Appartement', 'Eengezinswoning', 'Studio', 'Penthouse']
    streets = ['Hoofdstraat', 'Kerkstraat', 'Dorpsstraat', 'Stationsweg', 'Nieuwstraat', 'Molenweg']
    
    house_ids = []
    print("🏠 Generating Properties...")
    for i in range(1, 31): # 30 houses
        city = random.choice(cities)
        street = random.choice(streets)
        number = random.randint(1, 200)
        address = f"{street} {number}"
        object_id = f"{city[:3].upper()}{str(number).zfill(3)}"
        
        cursor.execute("""
            INSERT INTO huizen (object_id, adres, plaats, postcode, woning_type, aantal_sk, aantal_pers, status)
            VALUES (?, ?, ?, '1234 AB', ?, ?, ?, 'active')
        """, (object_id, address, city, random.choice(types), random.randint(1, 5), random.randint(2, 8)))
        house_ids.append(cursor.lastrowid)
        
    # --- 2. Leveranciers (Owners) ---
    owners = ['Vastgoed BV', 'Jansen Beheer', 'Stichting Wonen', 'Investico', 'Private Owner']
    owner_ids = []
    print("busts Generating Owners...")
    for owner in owners:
        cursor.execute("INSERT INTO leveranciers (naam, email) VALUES (?, ?)", (owner, f"info@{owner.lower().replace(' ', '')}.nl"))
        owner_ids.append(cursor.lastrowid)
        
    # --- 3. Klanten (Clients) ---
    clients = [
        'Tradiro', 'Axidus', 'Stipt', 'NL Jobs', 'Covebo', 'Tempo Team', 
        'Randstad', 'Olympia', 'Adecco', 'Manpower', 'YoungCapital', 'Timing'
    ]
    client_ids = []
    print("👥 Generating Clients...")
    for client in clients:
        cursor.execute("INSERT INTO klanten (naam, type, email) VALUES (?, 'zakelijk', ?)", (client, f"contact@{client.lower().replace(' ', '')}.nl"))
        client_ids.append(cursor.lastrowid)
        
    # --- 4. Contracts & Bookings ---
    print("📝 Generating Contracts & Bookings...")
    
    today = datetime.now().date()
    
    for house_id in house_ids:
        # Inhuur Contract (Owner -> RyanRent)
        owner_id = random.choice(owner_ids)
        start_date = today - timedelta(days=random.randint(300, 1000))
        rent = random.randint(800, 2500)
        
        cursor.execute("""
            INSERT INTO inhuur_contracten (property_id, leverancier_id, start_date, kale_huur, totale_huur)
            VALUES (?, ?, ?, ?, ?)
        """, (house_id, owner_id, start_date, rent, rent))
        
        # Verhuur Contract (RyanRent -> Client)
        client_id = random.choice(client_ids)
        client_rent = rent * random.uniform(1.1, 1.3)
        
        cursor.execute("""
            INSERT INTO verhuur_contracten (huis_id, klant_id, start_datum, kale_huur, status)
            VALUES (?, ?, ?, ?, 'active')
        """, (house_id, client_id, start_date, client_rent))
        contract_id = cursor.lastrowid
        
        # Bookings
        current_date = start_date
        last_checkout_id = None
        
        while current_date < today + timedelta(days=180):
            duration = random.randint(30, 180)
            checkin_date = current_date
            checkout_date = checkin_date + timedelta(days=duration)
            
            status = 'confirmed'
            if checkout_date < today:
                status = 'checked_out'
            elif checkin_date <= today <= checkout_date:
                status = 'checked_in'
            
            cursor.execute("""
                INSERT INTO boekingen (contract_id, huis_id, klant_id, checkin_datum, checkout_datum, status, totale_huur_factuur)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (contract_id, house_id, client_id, checkin_date, checkout_date, status, client_rent))
            booking_id = cursor.lastrowid
            
            # --- Uitchecks (Checkout Details) ---
            # Create entry for all bookings, filled if past or near future
            is_past = checkout_date < today
            is_near = abs((checkout_date - today).days) < 60
            
            uitcheck_id = None
            if is_past or is_near:
                cursor.execute("""
                    INSERT INTO uitchecks (
                        boeking_id, geplande_datum, werkelijke_datum, 
                        terug_naar_eigenaar, schoonmaak_vereist, meubilair_verwijderen, 
                        sleutels_ontvangen, schade_gemeld, afrekening_status, inspecteur
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    booking_id,
                    checkout_date,
                    checkout_date if is_past else None,
                    random.choice([0, 1]),
                    random.choice([0, 1]),
                    random.choice([0, 0, 1]),
                    1 if is_past else 0,
                    random.choice([0, 0, 0, 1]),
                    'voltooid' if is_past and random.random() > 0.5 else 'in_afwachting',
                    'Jan Jansen'
                ))
                uitcheck_id = cursor.lastrowid
                
                # Add Damages if reported
                if is_past and random.random() > 0.75:
                    cursor.execute("""
                        INSERT INTO schades (boeking_id, omschrijving, geschatte_kosten)
                        VALUES (?, ?, ?)
                    """, (booking_id, "Gebroken raam", 250.0))

            # --- Inchecks (Checkins) ---
            cursor.execute("""
                INSERT INTO inchecks (
                    boeking_id, gekoppelde_uitcheck_id, datum, 
                    incheck_voltooid, vis_referentie, status, uitgevoerd_door
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                booking_id,
                last_checkout_id, # Link to previous tenant's checkout
                checkin_date,
                1 if checkin_date <= today else 0,
                f"VIS-{random.randint(1000,9999)}",
                'voltooid' if checkin_date <= today else 'gepland',
                'Piet Pietersen'
            ))
            
            # --- Inspecties ---
            # Pre-inspection
            pre_date = checkout_date - timedelta(days=14)
            cursor.execute("""
                INSERT INTO inspecties (boeking_id, inspectie_type, geplande_datum, status)
                VALUES (?, 'voorinspectie', ?, ?)
            """, (booking_id, pre_date, 'voltooid' if pre_date < today else 'gepland'))
            
            # Eindinspectie
            cursor.execute("""
                INSERT INTO inspecties (boeking_id, inspectie_type, geplande_datum, status)
                VALUES (?, 'eindinspectie', ?, ?)
            """, (booking_id, checkout_date, 'voltooid' if checkout_date < today else 'gepland'))

            last_checkout_id = uitcheck_id
            current_date = checkout_date + timedelta(days=7)

    conn.commit()
    print("✅ Mock data generation completed (Dutch Schema)!")

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        exit(1)
        
    conn = create_connection()
    clear_data(conn)
    generate_data(conn)
    conn.close()
