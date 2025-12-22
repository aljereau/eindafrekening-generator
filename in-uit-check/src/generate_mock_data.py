import sqlite3
import os
import sys
from datetime import date, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

DB_PATH = "database/ryanrent_mock.db"

def get_db():
    return sqlite3.connect(DB_PATH)

def create_house(cursor, object_id, adres, plaats):
    cursor.execute("SELECT id FROM huizen WHERE object_id = ?", (object_id,))
    res = cursor.fetchone()
    if res:
        return res[0]
    
    cursor.execute("INSERT INTO huizen (object_id, adres, plaats, status) VALUES (?, ?, ?, 'active')", 
                   (object_id, adres, plaats))
    return cursor.lastrowid

def create_client(cursor, name):
    cursor.execute("SELECT id FROM klanten WHERE naam = ?", (name,))
    res = cursor.fetchone()
    if res:
        return res[0]
    
    cursor.execute("INSERT INTO klanten (naam) VALUES (?)", (name,))
    return cursor.lastrowid

def create_booking(cursor, huis_id, client_id, checkin, checkout):
    # Check overlap? Nah, just insert for mock
    cursor.execute("""
        INSERT INTO boekingen (huis_id, klant_id, checkin_datum, checkout_datum, status)
        VALUES (?, ?, ?, ?, 'confirmed')
    """, (huis_id, client_id, checkin, checkout))
    return cursor.lastrowid

def create_inspection(cursor, booking_id, type, date, status):
    cursor.execute("""
        INSERT INTO inspections (booking_id, inspection_type, planned_date, status)
        VALUES (?, ?, ?, ?)
    """, (booking_id, type, date, status))

def generate_mock_data():
    conn = get_db()
    cursor = conn.cursor()
    
    print("🚀 Generating Mock Data Scenarios...")
    
    today = date.today()
    
    # Scenario 1: Critical (Gap 2 days)
    print("1. Creating Critical Scenario (Spoorsingel 45)")
    h1 = create_house(cursor, "MOCK-001", "Spoorsingel 45", "Rotterdam")
    c1_old = create_client(cursor, "Vertrekkende Jan")
    c1_new = create_client(cursor, "Nieuwe Piet")
    
    # Old booking ends in 5 days
    b1_old = create_booking(cursor, h1, c1_old, today - timedelta(days=360), today + timedelta(days=5))
    # New booking starts in 7 days
    b1_new = create_booking(cursor, h1, c1_new, today + timedelta(days=7), today + timedelta(days=372))
    
    create_inspection(cursor, b1_old, 'pre_inspection', today - timedelta(days=10), 'completed')
    create_inspection(cursor, b1_old, 'uitcheck', today + timedelta(days=5), 'planned')
    create_inspection(cursor, b1_new, 'vis', today + timedelta(days=6), 'planned')
    create_inspection(cursor, b1_new, 'incheck', today + timedelta(days=7), 'planned')

    # Scenario 2: High Priority (Gap 5 days)
    print("2. Creating High Priority Scenario (Kerkstraat 10)")
    h2 = create_house(cursor, "MOCK-002", "Kerkstraat 10", "Amsterdam")
    c2_old = create_client(cursor, "Vertrekkende Klaas")
    c2_new = create_client(cursor, "Nieuwe Marie")
    
    # Old booking ends in 20 days
    b2_old = create_booking(cursor, h2, c2_old, today - timedelta(days=300), today + timedelta(days=20))
    # New booking starts in 25 days
    b2_new = create_booking(cursor, h2, c2_new, today + timedelta(days=25), today + timedelta(days=390))
    
    create_inspection(cursor, b2_old, 'pre_inspection', today + timedelta(days=5), 'planned')
    
    # Scenario 3: Normal Priority (Back to Owner)
    print("3. Creating Normal Scenario (Dorpstraat 1)")
    h3 = create_house(cursor, "MOCK-003", "Dorpstraat 1", "Utrecht")
    c3_old = create_client(cursor, "Vertrekkende Henk")
    
    # Old booking ends in 10 days
    b3_old = create_booking(cursor, h3, c3_old, today - timedelta(days=100), today + timedelta(days=10))
    # No new booking
    
    create_inspection(cursor, b3_old, 'pre_inspection', today - timedelta(days=2), 'needed')

    # Scenario 4: Renovation Gap (Normal Priority, big gap)
    print("4. Creating Renovation Gap Scenario (Stationsweg 99)")
    h4 = create_house(cursor, "MOCK-004", "Stationsweg 99", "Den Haag")
    c4_old = create_client(cursor, "Vertrekkende Truus")
    c4_new = create_client(cursor, "Nieuwe Bouwers BV")
    
    # Old booking ends in 5 days
    b4_old = create_booking(cursor, h4, c4_old, today - timedelta(days=200), today + timedelta(days=5))
    # New booking starts in 60 days
    b4_new = create_booking(cursor, h4, c4_new, today + timedelta(days=60), today + timedelta(days=400))
    
    create_inspection(cursor, b4_old, 'uitcheck', today + timedelta(days=5), 'planned')

    conn.commit()
    conn.close()
    print("✅ Mock Data Generated Successfully!")

if __name__ == "__main__":
    generate_mock_data()
