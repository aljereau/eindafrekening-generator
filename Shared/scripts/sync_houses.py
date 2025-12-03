import pandas as pd
import sqlite3
import os
import sys
import random

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'Sources', 'Houses List.xlsx')

def get_real_houses():
    df = pd.read_excel(EXCEL_PATH)
    houses = []
    for _, row in df.iterrows():
        # Clean object ID (ensure it's string)
        obj_id = str(row['OBJECT']).strip()
        if obj_id.endswith('.0'): obj_id = obj_id[:-2]
        
        # Format as HUIS-XXX for consistency with previous mock format if desired, 
        # OR keep as is. User said "Object id is the universal identifier".
        # Let's keep it as is but ensure it's a string.
        
        adres = row['Straat en huisnummer']
        if pd.isna(adres):
            continue
            
        houses.append({
            'object_id': obj_id,
            'adres': adres,
            'postcode': row['Postcode'],
            'plaats': row['Plaats']
        })
    return houses

def sync_database(db_path, real_houses):
    print(f"🔄 Syncing {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Get existing mock house IDs to re-map bookings
    cursor.execute("SELECT id FROM huizen")
    old_house_ids = [row[0] for row in cursor.fetchall()]
    
    # 2. Clear existing houses table
    # We need to be careful about foreign keys. 
    # Strategy: Insert new houses, then update bookings to point to new house IDs, then delete old houses?
    # Or: Delete everything and re-generate bookings? 
    # User wants to "update the tables with the information".
    # Since we have mock bookings pointing to mock houses, if we delete houses, we lose bookings.
    # BETTER STRATEGY: 
    # 1. Delete all mock houses.
    # 2. Insert real houses.
    # 3. Randomly assign existing bookings to the new real houses.
    
    # Disable FK checks temporarily
    cursor.execute("PRAGMA foreign_keys = OFF")
    
    cursor.execute("DELETE FROM huizen")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='huizen'")
    
    # Insert real houses
    new_house_ids = []
    for h in real_houses:
        cursor.execute("""
            INSERT INTO huizen (object_id, adres, postcode, plaats)
            VALUES (?, ?, ?, ?)
        """, (h['object_id'], h['adres'], h['postcode'], h['plaats']))
        new_house_ids.append(cursor.lastrowid)
        
    print(f"✅ Inserted {len(new_house_ids)} real houses.")
    
    # Re-map bookings to new houses
    if old_house_ids and new_house_ids:
        cursor.execute("SELECT id FROM boekingen")
        booking_ids = [row[0] for row in cursor.fetchall()]
        
        for b_id in booking_ids:
            new_house_id = random.choice(new_house_ids)
            cursor.execute("UPDATE boekingen SET huis_id = ? WHERE id = ?", (new_house_id, b_id))
            
        print(f"🔗 Re-linked {len(booking_ids)} bookings to real houses.")
        
    # Re-enable FK
    cursor.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    real_houses = get_real_houses()
    print(f"Found {len(real_houses)} houses in Excel.")
    
    # Sync both databases
    db_core = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_core.db')
    db_mock = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_mock.db')
    
    if os.path.exists(db_core):
        sync_database(db_core, real_houses)
    
    if os.path.exists(db_mock):
        sync_database(db_mock, real_houses)
        
    print("🎉 Done syncing houses.")
