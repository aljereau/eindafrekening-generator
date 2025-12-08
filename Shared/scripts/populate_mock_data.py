import sqlite3
import random
from datetime import datetime
import sys
import os

# Add parent directory to path to import database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import init_database

def populate_mock_data():
    print("🚀 Starting Mock Data Population...")
    db = init_database()
    conn = db.get_connection()
    
    try:
        # 1. Update Properties (Huizen)
        print("\n🏠 Updating Properties...")
        cursor = conn.execute("SELECT id FROM huizen WHERE woning_type IS NULL OR oppervlakte IS NULL")
        rows = cursor.fetchall()
        
        updated_props = 0
        for row in rows:
            prop_id = row['id']
            
            woning_type = random.choice(['Appartement', 'Eengezinswoning', 'Studio', 'Penthouse'])
            oppervlakte = random.randint(45, 150)
            aantal_sk = random.randint(1, 4)
            aantal_pers = aantal_sk * 2 if oppervlakte > 60 else 2
            
            conn.execute("""
                UPDATE huizen 
                SET woning_type = ?, oppervlakte = ?, aantal_sk = ?, aantal_pers = ?
                WHERE id = ?
            """, (woning_type, oppervlakte, aantal_sk, aantal_pers, prop_id))
            updated_props += 1
            
        print(f"   ✓ Updated {updated_props} properties with mock data.")

        # 2. Update Bookings
        print("\n📅 Updating Bookings...")
        cursor = conn.execute("""
            SELECT id, checkin_datum, checkout_datum, totale_huur_factuur 
            FROM boekingen 
            WHERE betaalde_borg IS NULL OR betaalde_borg = 0
               OR voorschot_gwe IS NULL OR voorschot_gwe = 0
        """)
        rows = cursor.fetchall()
        
        updated_bookings = 0
        for row in rows:
            booking_id = row['id']
            checkin = datetime.strptime(row['checkin_datum'], '%Y-%m-%d')
            checkout = datetime.strptime(row['checkout_datum'], '%Y-%m-%d')
            total_rent = row['totale_huur_factuur'] or 0
            
            # Calculate duration in months (approx)
            days = (checkout - checkin).days
            months = max(1, round(days / 30))
            
            # Calculate monthly rent (Borg)
            if total_rent > 0:
                monthly_rent = total_rent / months
                borg = round(monthly_rent, 2)
            else:
                borg = 1500.00 # Fallback
                
            # Mock values
            voorschot_gwe = random.choice([150.00, 175.00, 200.00, 225.00, 250.00])
            voorschot_schoonmaak = 50.00
            schoonmaak_pakket = random.choice(['Basis Schoonmaak', 'Intensief Schoonmaak'])
            
            conn.execute("""
                UPDATE boekingen 
                SET betaalde_borg = ?, 
                    voorschot_gwe = ?, 
                    voorschot_schoonmaak = ?, 
                    schoonmaak_pakket = ?
                WHERE id = ?
            """, (borg, voorschot_gwe, voorschot_schoonmaak, schoonmaak_pakket, booking_id))
            updated_bookings += 1
            
        conn.commit()
        print(f"   ✓ Updated {updated_bookings} bookings with mock data.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\n✅ Done!")

if __name__ == "__main__":
    populate_mock_data()
