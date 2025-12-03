import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def cleanup_database(db_path):
    print(f"🧹 Cleaning duplicates in {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find duplicates by address
    # We want to keep the one that looks like '0001' or 'A-...' over '1'
    # Heuristic: Keep the one with longer object_id (assuming padding) or containing 'A'
    
    cursor.execute("""
        SELECT adres, count(*) 
        FROM huizen 
        GROUP BY adres 
        HAVING count(*) > 1
    """)
    duplicates = cursor.fetchall()
    
    merged_count = 0
    
    for row in duplicates:
        adres = row[0]
        cursor.execute("SELECT id, object_id FROM huizen WHERE adres = ?", (adres,))
        houses = cursor.fetchall()
        
        # Sort by object_id length descending, so '0001' comes before '1'
        # Also prefer 'A-'
        houses.sort(key=lambda x: (len(x[1]), x[1]), reverse=True)
        
        keep = houses[0]
        drops = houses[1:]
        
        keep_id = keep[0]
        keep_obj = keep[1]
        
        for drop in drops:
            drop_id = drop[0]
            drop_obj = drop[1]
            
            # Move bookings
            cursor.execute("UPDATE boekingen SET huis_id = ? WHERE huis_id = ?", (keep_id, drop_id))
            
            # Delete dropped house
            cursor.execute("DELETE FROM huizen WHERE id = ?", (drop_id,))
            
            # print(f"   Merged {drop_obj} -> {keep_obj} ({adres})")
            merged_count += 1
            
    conn.commit()
    conn.close()
    print(f"✅ Merged {merged_count} duplicate houses.")

if __name__ == "__main__":
    db_core = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_core.db')
    db_mock = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_mock.db')
    
    if os.path.exists(db_core):
        cleanup_database(db_core)
        
    if os.path.exists(db_mock):
        cleanup_database(db_mock)
        
    print("🎉 Done cleaning duplicates.")
