import sqlite3
from pathlib import Path

# DB Path
DB_PATH = Path("database/ryanrent_mock.db")

def update_stoffering():
    print(f"🔧 Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Update Parameter Price
        PRICE_PPPW = 2.0
        print(f"📝 Updating 'Stoffering' parameter to €{PRICE_PPPW} pppw...")
        
        cursor.execute("UPDATE parameters SET prijs_pp_pw = ? WHERE naam = 'Stoffering'", (PRICE_PPPW,))
        if cursor.rowcount == 0:
            print("   - 'Stoffering' not found in parameters! Inserting it.")
            cursor.execute("INSERT INTO parameters (naam, prijs_pp_pw, eenheid) VALUES ('Stoffering', ?, 'per_persoon_per_week')", (PRICE_PPPW,))
        
        conn.commit()
        
        # 2. Recalculate Houses
        print("🧮 Recalculating 'stoffering' column for all active houses...")
        
        cursor.execute("SELECT id, aantal_pers FROM huizen WHERE status='active' AND aantal_pers > 0")
        houses = cursor.fetchall()
        
        monthly_factor = (52 / 12)
        update_count = 0
        
        for h_id, people in houses:
            # Cost = Price * People * 4.333
            cost = round(PRICE_PPPW * people * monthly_factor, 2)
            
            cursor.execute("UPDATE huizen SET stoffering = ? WHERE id = ?", (cost, h_id))
            update_count += 1
            
        print(f"   - Updated {update_count} houses with new Stoffering cost.")

        conn.commit()
        print("\n✅ Stoffering Update completed successfully!")
        
        # 3. Verify
        cursor.execute("SELECT id, aantal_pers, stoffering FROM huizen WHERE aantal_pers=5 LIMIT 1")
        row = cursor.fetchone()
        if row:
            print(f"\nExample for 5 people: Capacity={row[1]}, Cost={row[2]}")
            print(f"Expected: 2.0 * 5 * 4.333 = {round(2.0*5*monthly_factor, 2)}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Update failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_stoffering()
