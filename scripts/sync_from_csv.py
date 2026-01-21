#!/usr/bin/env python3
"""
Sync database with woningoverzicht CSV
Updates:
- huizen: facturatie_type, capaciteit_personen, aantal_slaapkamers
- verhuur_contracten: huurder, huur_excl_btw, voorschot_gwe
- inhuur_contracten: eigenaar, inhuur_excl_btw, kale_huur, hovk
"""

import csv
import sqlite3
from datetime import datetime
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CSV_PATH = PROJECT_ROOT / "Shared/Sources/excel_data/woningoverzichtdata_20012026.csv"
DB_PATH = PROJECT_ROOT / "database/ryanrent_v2.db"

def parse_date(date_str):
    """Parse Dutch date format (dd/mm/yyyy) to ISO format"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        parts = date_str.strip().split('/')
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
    except:
        pass
    return None

def parse_euro(euro_str):
    """Parse Dutch euro format (€ 1.234,56) to float"""
    if not euro_str or euro_str.strip() == '':
        return None
    try:
        cleaned = euro_str.replace('€', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        if cleaned == '-' or cleaned == '':
            return 0.0
        return float(cleaned)
    except:
        return None

def parse_int(val_str):
    """Parse integer from string"""
    if not val_str or val_str.strip() == '':
        return None
    try:
        return int(val_str.strip())
    except:
        return None

def sync_database():
    # Read CSV
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        csv_data = list(reader)
    
    print(f"📊 Read {len(csv_data)} properties from CSV")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Get house_id mapping
    house_ids = {}
    for row in conn.execute("SELECT id, object_id FROM huizen"):
        house_ids[row['object_id']] = row['id']
    
    # Stats
    huizen_updated = 0
    verhuur_updated = 0
    verhuur_created = 0
    inhuur_updated = 0
    inhuur_created = 0
    errors = []
    
    for row in csv_data:
        object_id = row.get('object_id', '').strip()
        if not object_id or object_id not in house_ids:
            if object_id and not object_id.startswith('A-') and not ',' in object_id:
                errors.append(f"Object {object_id} not in huizen table")
            continue
        
        house_id = house_ids[object_id]
        
        # --- HUIZEN (Property details) ---
        facturatie = row.get('Facturatie', '').strip()
        aant_pers = parse_int(row.get('Aant. pers.', ''))
        aant_sk = parse_int(row.get('Aant. SK', ''))
        
        if facturatie or aant_pers or aant_sk:
            conn.execute("""
                UPDATE huizen 
                SET facturatie_type = COALESCE(NULLIF(?, ''), facturatie_type),
                    capaciteit_personen = COALESCE(?, capaciteit_personen),
                    aantal_slaapkamers = COALESCE(?, aantal_slaapkamers)
                WHERE id = ?
            """, (facturatie, aant_pers, aant_sk, house_id))
            huizen_updated += 1
        
        # --- VERHUUR (Huurder) ---
        huurder_id = row.get('relatie_id_huurder', '').strip()
        if huurder_id and huurder_id.isdigit():
            huurder_id = int(huurder_id)
            
            verhuur_start = parse_date(row.get('Startdatum', ''))
            verhuur_end = parse_date(row.get('Einddatum Min. Per.', ''))
            verhuur_excl = parse_euro(row.get('Verhuur EXCL. BTW', ''))
            voorschot_gwe = parse_euro(row.get('Voorschot GWE', ''))
            
            # Check if contract exists for this house+huurder
            existing = conn.execute("""
                SELECT id FROM verhuur_contracten 
                WHERE house_id = ? AND relatie_id = ?
            """, (house_id, huurder_id)).fetchone()
            
            if existing:
                conn.execute("""
                    UPDATE verhuur_contracten 
                    SET start_date = COALESCE(?, start_date),
                        end_date = COALESCE(?, end_date),
                        huur_excl_btw = COALESCE(?, huur_excl_btw),
                        voorschot_gwe_excl_btw = COALESCE(?, voorschot_gwe_excl_btw)
                    WHERE id = ?
                """, (verhuur_start, verhuur_end, verhuur_excl, voorschot_gwe, existing['id']))
                verhuur_updated += 1
            else:
                if verhuur_start is None:
                    verhuur_start = datetime.now().strftime('%Y-%m-%d')
                conn.execute("""
                    INSERT INTO verhuur_contracten 
                    (house_id, relatie_id, start_date, end_date, huur_excl_btw, voorschot_gwe_excl_btw, huur_btw_pct)
                    VALUES (?, ?, ?, ?, ?, ?, 0.09)
                """, (house_id, huurder_id, verhuur_start, verhuur_end, verhuur_excl or 0, voorschot_gwe or 0))
                verhuur_created += 1
        
        # --- INHUUR (Eigenaar) ---
        eigenaar_id = row.get('relatie_id_eigenaar', '').strip()
        if eigenaar_id and eigenaar_id.isdigit():
            eigenaar_id = int(eigenaar_id)
            
            inhuur_excl = parse_euro(row.get('Inhuur EXCL BTW', ''))
            kale_inhuur = parse_euro(row.get('Kale inhuurprijs', ''))
            hovk = row.get('HOVK', '').strip()  # Contract type: bepaalde tijd / onbepaalde tijd
            
            existing = conn.execute("""
                SELECT id FROM inhuur_contracten WHERE house_id = ?
            """, (house_id,)).fetchone()
            
            if existing:
                conn.execute("""
                    UPDATE inhuur_contracten 
                    SET relatie_id = ?,
                        inhuur_excl_btw = COALESCE(?, inhuur_excl_btw),
                        kale_huur = COALESCE(?, kale_huur),
                        hovk = COALESCE(NULLIF(?, ''), hovk)
                    WHERE id = ?
                """, (eigenaar_id, inhuur_excl, kale_inhuur, hovk, existing['id']))
                inhuur_updated += 1
            else:
                conn.execute("""
                    INSERT INTO inhuur_contracten 
                    (house_id, relatie_id, inhuur_excl_btw, kale_huur, hovk)
                    VALUES (?, ?, ?, ?, ?)
                """, (house_id, eigenaar_id, inhuur_excl or 0, kale_inhuur or 0, hovk or None))
                inhuur_created += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Sync complete!")
    print(f"   Huizen:  {huizen_updated} updated (facturatie, pers, sk)")
    print(f"   Verhuur: {verhuur_updated} updated, {verhuur_created} created")
    print(f"   Inhuur:  {inhuur_updated} updated, {inhuur_created} created")
    
    if errors:
        print(f"\n⚠️  {len(errors)} errors:")
        for e in errors[:5]:
            print(f"   {e}")

if __name__ == '__main__':
    print("🔄 Syncing database from woningoverzicht CSV...")
    sync_database()
