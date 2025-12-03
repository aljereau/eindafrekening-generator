import pandas as pd
import sqlite3
import os
import sys
import re
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# File Paths
FILE_BASE = os.path.join(os.path.dirname(__file__), '..', 'Sources', 'huizen+ archief huizen.xlsx')
FILE_ENRICH_1 = os.path.join(os.path.dirname(__file__), '..', 'Sources', 'Houses + Informationrelated.xlsx')
FILE_ENRICH_2 = os.path.join(os.path.dirname(__file__), '..', 'Sources', 'Houses List.xlsx')

def get_conn(db_path):
    return sqlite3.connect(db_path)

def standardize_object_id(raw_id):
    s = str(raw_id).strip()
    if s.endswith('.0'): s = s[:-2] # Remove float suffix
    
    if 'A' in s or 'a' in s:
        # Archive format: A-0001
        # Remove 'A' or 'A-' and pad number
        num_part = re.sub(r'[^\d]', '', s)
        if num_part:
            return f"A-{int(num_part):04d}"
        return s # Fallback
    elif s.isdigit():
        return f"{int(s):04d}"
    return s

def step_1_sync_base(conn):
    print("   Step 1: Syncing base houses...")
    df = pd.read_excel(FILE_BASE)
    cursor = conn.cursor()
    
    count = 0
    for _, row in df.iterrows():
        raw_code = row['Code']
        omschrijving = row['Omschrijving']
        
        if pd.isna(raw_code) or pd.isna(omschrijving): continue
        
        obj_id = standardize_object_id(raw_code)
        is_archived = 'A-' in obj_id
        status = 'archived' if is_archived else 'active'
        
        # Parse address (simple heuristic)
        adres = str(omschrijving).strip()
        plaats = None
        if ',' in adres:
            parts = adres.rsplit(',', 1)
            adres = parts[0].strip()
            plaats = parts[1].strip()
            if '(' in plaats: plaats = plaats.split('(')[0].strip()
            
        # Upsert
        cursor.execute("SELECT id FROM huizen WHERE object_id = ?", (obj_id,))
        row = cursor.fetchone()
        
        if row:
            # Update
            cursor.execute("UPDATE huizen SET status = ? WHERE id = ?", (status, row[0]))
        else:
            # Insert
            cursor.execute("INSERT INTO huizen (object_id, adres, plaats, status) VALUES (?, ?, ?, ?)", (obj_id, adres, plaats, status))
            count += 1
            
    conn.commit()
    print(f"   ✅ Base sync complete. Added {count} new houses.")

def step_2_deduplicate(conn):
    print("   Step 2: Deduplicating...")
    cursor = conn.cursor()
    
    # Find duplicates by address
    cursor.execute("SELECT adres, count(*) FROM huizen GROUP BY adres HAVING count(*) > 1")
    dupes = cursor.fetchall()
    
    merged = 0
    for row in dupes:
        adres = row[0]
        cursor.execute("SELECT id, object_id FROM huizen WHERE adres = ?", (adres,))
        houses = cursor.fetchall()
        
        # Prefer 4-digit ID or A- ID
        houses.sort(key=lambda x: (len(x[1]), x[1]), reverse=True)
        
        keep = houses[0]
        drops = houses[1:]
        
        for drop in drops:
            # Move bookings
            cursor.execute("UPDATE boekingen SET huis_id = ? WHERE huis_id = ?", (keep[0], drop[0]))
            # Delete
            cursor.execute("DELETE FROM huizen WHERE id = ?", (drop[0],))
            merged += 1
            
    conn.commit()
    print(f"   ✅ Deduplication complete. Merged {merged} duplicates.")

def step_3_enrich_financials(conn):
    print("   Step 3: Enriching financials & details...")
    df = pd.read_excel(FILE_ENRICH_1)
    cursor = conn.cursor()
    
    updated = 0
    
    # Need to match by object_id. But this file doesn't have explicit object_id column named 'Code' or 'Object'.
    # Wait, previous inspection showed: 
    # Columns: ['Unnamed: 0', 'Unnamed: 1', 'Facturatie', 'Adres', ...]
    # Row 0: 1.0, 22.0, Factuur, Nunspeetlaan 14...
    # Row 1: 2.0, 3.0, Factuur, Acacia 2...
    # It seems 'Unnamed: 0' might be the ID? Or 'Unnamed: 1'?
    # Let's check the values.
    # Row 0: Unnamed:0 = 1.0. House is Nunspeetlaan 14 (Code 0001).
    # Row 1: Unnamed:0 = 3.0. House is Acacia 2 (Code 0003).
    # Row 2: Unnamed:0 = 5.0. House is Ringbaan Oost 327 (Code 0005).
    # So 'Unnamed: 0' seems to correspond to the integer part of Object ID!
    
    for _, row in df.iterrows():
        raw_id = row.iloc[0] # First column
        if pd.isna(raw_id): continue
        
        try:
            obj_id = f"{int(raw_id):04d}"
        except:
            continue
            
        # Find house by object_id
        cursor.execute("SELECT id FROM huizen WHERE object_id = ?", (obj_id,))
        house_row = cursor.fetchone()
        if not house_row: continue
        house_id = house_row[0]
        
        # Extract Data
        sk = row['Aant. SK'] if not pd.isna(row['Aant. SK']) else None
        pers = row['Aant. pers.'] if not pd.isna(row['Aant. pers.']) else None
        postcode = row['Postcode'] if not pd.isna(row['Postcode']) else None
        plaats = row['Plaats'] if not pd.isna(row['Plaats']) else None
        
        # Update House
        fields = []
        vals = []
        if sk: fields.append("aantal_sk = ?"); vals.append(sk)
        if pers: fields.append("aantal_pers = ?"); vals.append(pers)
        if postcode: fields.append("postcode = ?"); vals.append(postcode)
        if plaats: fields.append("plaats = ?"); vals.append(plaats)
        
        if fields:
            query = f"UPDATE huizen SET {', '.join(fields)} WHERE id = ?"
            vals.append(house_id)
            cursor.execute(query, vals)
            updated += 1
            
        # Update Contracts (Simplified logic from previous script)
        # ... (We can reuse the logic if needed, but let's focus on the house fields first as requested)
        # User said: "pull the information of the rent, inhuur, verhuur,m kamer and what not"
        
        # Verhuur
        vp = row['Kale verhuurprijs'] if not pd.isna(row['Kale verhuurprijs']) else None
        if not vp: vp = row['Verhuur EXCL. BTW'] if not pd.isna(row['Verhuur EXCL. BTW']) else None
        
        # Inhuur
        ip = row['Kale inhuurprijs'] if not pd.isna(row['Kale inhuurprijs']) else None
        if not ip: ip = row['Inhuur EXCL BTW'] if not pd.isna(row['Inhuur EXCL BTW']) else None
        
        # Client/Supplier
        huurder = row['Huurder'] if not pd.isna(row['Huurder']) else None
        eigenaar = row['Eigenaar'] if not pd.isna(row['Eigenaar']) else None
        
        # We need client/supplier IDs
        cid = None
        sid = None
        
        if huurder:
            cursor.execute("SELECT id FROM klanten WHERE naam = ?", (huurder,))
            r = cursor.fetchone()
            if r: cid = r[0]
            else: 
                cursor.execute("INSERT INTO klanten (naam, type) VALUES (?, 'zakelijk')", (huurder,))
                cid = cursor.lastrowid
                
        if eigenaar:
            cursor.execute("SELECT id FROM leveranciers WHERE naam = ?", (eigenaar,))
            r = cursor.fetchone()
            if r: sid = r[0]
            else:
                cursor.execute("INSERT INTO leveranciers (naam) VALUES (?)", (eigenaar,))
                sid = cursor.lastrowid
                
        # Upsert Contracts
        if cid and vp:
            cursor.execute("SELECT id FROM verhuur_contracten WHERE huis_id = ? AND klant_id = ?", (house_id, cid))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO verhuur_contracten (huis_id, klant_id, kale_huur, start_datum) VALUES (?, ?, ?, ?)", (house_id, cid, vp, '2023-01-01'))
                
        if sid and ip:
            cursor.execute("SELECT id FROM inhuur_contracten WHERE property_id = ? AND leverancier_id = ?", (house_id, sid))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO inhuur_contracten (property_id, leverancier_id, kale_huur, start_date) VALUES (?, ?, ?, ?)", (house_id, sid, ip, '2023-01-01'))

    conn.commit()
    print(f"   ✅ Financials enrich complete. Updated {updated} houses.")

def step_4_enrich_safe(conn):
    print("   Step 4: Enriching safe/key info...")
    df = pd.read_excel(FILE_ENRICH_2)
    cursor = conn.cursor()
    
    updated = 0
    
    for _, row in df.iterrows():
        raw_obj = row['OBJECT']
        if pd.isna(raw_obj): continue
        
        obj_id = standardize_object_id(raw_obj)
        
        kluis1 = row['Kluis 1'] if not pd.isna(row['Kluis 1']) else None
        kluis2 = row['Kluis 2'] if not pd.isna(row['Kluis 2']) else None
        
        if kluis1 or kluis2:
            cursor.execute("UPDATE huizen SET kluis_code_1 = ?, kluis_code_2 = ? WHERE object_id = ?", (str(kluis1), str(kluis2), obj_id))
            if cursor.rowcount > 0:
                updated += 1
                
    conn.commit()
    print(f"   ✅ Safe info enrich complete. Updated {updated} houses.")

def run_master_sync(db_path):
    print(f"🚀 Starting Master Sync for {db_path}...")
    conn = get_conn(db_path)
    
    step_1_sync_base(conn)
    step_2_deduplicate(conn)
    step_3_enrich_financials(conn)
    step_4_enrich_safe(conn)
    
    conn.close()
    print("🎉 Master Sync Finished!")

if __name__ == "__main__":
    db_core = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_core.db')
    db_mock = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_mock.db')
    
    if os.path.exists(db_core):
        run_master_sync(db_core)
        
    if os.path.exists(db_mock):
        run_master_sync(db_mock)
