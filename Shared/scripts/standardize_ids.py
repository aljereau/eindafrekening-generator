import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def standardize_and_merge(db_path):
    print(f"🔧 Standardizing IDs in {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all houses
    cursor.execute("SELECT id, object_id FROM huizen")
    houses = cursor.fetchall()
    
    updates = 0
    merges = 0
    
    # Map standardized_id -> existing_house_id
    id_map = {}
    
    # We need to process them. 
    # If we encounter a collision (e.g. we have '0011' and we find '11' which becomes '0011'),
    # we merge '11' into '0011'.
    
    # First, let's build a map of what exists to avoid unique constraint errors during update
    # Actually, we can't just update blindly.
    
    # Let's iterate and decide actions.
    # To do this safely, we might need to do it in memory first?
    # Or just process one by one.
    
    # Let's sort houses so we process "good" IDs first? 
    # e.g. '0011' comes before '11' if we sort by length desc? No.
    # We want to keep the one that is ALREADY correct if possible.
    
    # Sort by: is_correct_format (len=4 and digits), then id
    def sort_key(h):
        oid = h[1]
        is_good = len(oid) == 4 and oid.isdigit()
        return (not is_good, h[0]) # False < True, so Good comes first
        
    houses.sort(key=sort_key)
    
    for house_id, raw_oid in houses:
        # Determine standard ID
        if raw_oid.startswith('A-') or raw_oid.startswith('a-'):
            # Archive format. User didn't explicitly say pad these, but "numbers should all be reported with 4 digits".
            # Let's assume A-1 -> A-0001
            # Extract number
            parts = raw_oid.split('-')
            if len(parts) == 2 and parts[1].isdigit():
                std_oid = f"A-{int(parts[1]):04d}" # A-0001
            else:
                std_oid = raw_oid # Keep as is if weird
        elif raw_oid.isdigit():
            std_oid = f"{int(raw_oid):04d}" # 0011
        else:
            std_oid = raw_oid # Keep non-numeric as is (e.g. HUIS-001 if any left)
            
        # Check if this std_oid is already "claimed" by another house in this run
        if std_oid in id_map:
            target_house_id = id_map[std_oid]
            
            if target_house_id != house_id:
                # MERGE: Move bookings from house_id to target_house_id
                cursor.execute("UPDATE boekingen SET huis_id = ? WHERE huis_id = ?", (target_house_id, house_id))
                
                # Delete this duplicate house
                cursor.execute("DELETE FROM huizen WHERE id = ?", (house_id,))
                merges += 1
                # print(f"   Merged {raw_oid} (id {house_id}) -> {std_oid} (id {target_house_id})")
        else:
            # Claim it
            id_map[std_oid] = house_id
            
            # Update the DB if it changed
            if std_oid != raw_oid:
                try:
                    cursor.execute("UPDATE huizen SET object_id = ? WHERE id = ?", (std_oid, house_id))
                    updates += 1
                except sqlite3.IntegrityError:
                    # This happens if '0011' already exists in DB but wasn't in our sorted list yet?
                    # Or if we have a collision we didn't anticipate.
                    # But we sorted 'good' ones first, so '0011' should be in id_map already.
                    # Wait, if '0011' was in DB, it was processed first and put in id_map.
                    # Then '11' comes, becomes '0011', finds it in id_map, and merges.
                    # So update shouldn't happen for '11'.
                    # What if '11' is the first one? (e.g. no '0011' exists).
                    # Then we update '11' to '0011'. 
                    # If '0011' existed, it would have been first.
                    print(f"   ⚠️ Error updating {raw_oid} to {std_oid}")
                    
    conn.commit()
    conn.close()
    print(f"✅ Standardized: {updates} updated, {merges} merged.")

if __name__ == "__main__":
    db_core = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_core.db')
    db_mock = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_mock.db')
    
    if os.path.exists(db_core):
        standardize_and_merge(db_core)
        
    if os.path.exists(db_mock):
        standardize_and_merge(db_mock)
        
    print("🎉 Done standardizing IDs.")
