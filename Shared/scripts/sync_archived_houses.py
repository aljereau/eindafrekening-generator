import pandas as pd
import sqlite3
import os
import sys
import re

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'Sources', 'huizen+ archief huizen.xlsx')

def get_houses_data():
    df = pd.read_excel(EXCEL_PATH)
    data = []
    for _, row in df.iterrows():
        code = str(row['Code']).strip()
        omschrijving = str(row['Omschrijving']).strip()
        
        if pd.isna(code) or pd.isna(omschrijving): continue
        
        is_archived = 'A' in code or 'a' in code # Case insensitive check for A- prefix or suffix
        # Actually looking at data: "A-00001", "A-0001". So 'A' is sufficient.
        
        # Parse Address/City
        # Strategy: Split by comma if present.
        if ',' in omschrijving:
            parts = omschrijving.rsplit(',', 1)
            adres = parts[0].strip()
            plaats = parts[1].strip()
            # Clean up potential trailing info like "(Opgezegd...)"
            if '(' in plaats:
                plaats = plaats.split('(')[0].strip()
        else:
            # Fallback: Assume last word is city if it looks like one? 
            # Or just put everything in address.
            # Let's try to be smart: "Street Number City"
            # Regex for "City" being the last part?
            # "Nunspeetlaan 14 Den Haag" -> Adres: Nunspeetlaan 14, Plaats: Den Haag
            # "Acacia 2 Hellevoetsluis"
            # "Ringbaan Oost 327 Tilburg"
            # "Arkelse onderweg 24a Gorichem"
            
            # Match: (Everything) (Number+Suffix) (City)
            # This is hard. Let's just put everything in address if no comma, 
            # OR try to split by last space if the last part is a known city or looks like one.
            # But "Den Haag" has a space.
            # Let's just default to Address = Full String, Plaats = None if no comma.
            # Better to have full address in one field than wrong split.
            adres = omschrijving
            plaats = None
            
            # Heuristic for space-separated city
            # If we match "Street Number City"
            match = re.search(r'^(.*?\d+[a-zA-Z]*)\s+(.*)$', omschrijving)
            if match:
                adres = match.group(1).strip()
                plaats = match.group(2).strip()
        
        data.append({
            'object_id': code,
            'adres': adres,
            'plaats': plaats,
            'status': 'archived' if is_archived else 'active'
        })
    return data

def sync_database(db_path, houses):
    print(f"🔄 Syncing houses to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    added = 0
    updated = 0
    
    for h in houses:
        cursor.execute("SELECT id, status FROM huizen WHERE object_id = ?", (h['object_id'],))
        row = cursor.fetchone()
        
        if row:
            # Update status if different
            current_status = row[1]
            if current_status != h['status']:
                cursor.execute("UPDATE huizen SET status = ? WHERE id = ?", (h['status'], row[0]))
                updated += 1
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO huizen (object_id, adres, plaats, status)
                VALUES (?, ?, ?, ?)
            """, (h['object_id'], h['adres'], h['plaats'], h['status']))
            added += 1
            
    conn.commit()
    conn.close()
    print(f"✅ Processed: {added} added, {updated} updated.")

if __name__ == "__main__":
    data = get_houses_data()
    print(f"Found {len(data)} houses in Excel.")
    
    db_core = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_core.db')
    db_mock = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_mock.db')
    
    if os.path.exists(db_core):
        sync_database(db_core, data)
        
    if os.path.exists(db_mock):
        sync_database(db_mock, data)
        
    print("🎉 Done syncing archived houses.")
