#!/usr/bin/env python3
"""
Compare the corrected CSV with the database and identify differences.
Then update the database to match the CSV for changed entries only.
"""
import csv
import sqlite3
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
DB_PATH = PROJECT_ROOT / "database" / "ryanrent_v2.db"
CSV_PATH = PROJECT_ROOT / "Shared/Sources/csv_data/correcting_kpls/overzicht-26januarie2026-corrections-kpls.csv"

def parse_euro(val):
    """Parse euro value like '€ 1.234,56' to float"""
    if not val or val.strip() == '' or val.strip() == '-':
        return None
    val = val.replace('€', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(val)
    except:
        return None

def parse_date(val):
    """Parse date like '01/02/2023' to 'YYYY-MM-DD'"""
    if not val or val.strip() == '' or val.strip() == '-' or 'obt' in val.lower():
        return None
    val = val.strip()
    # Try various formats
    for fmt in ['%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y']:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime('%Y-%m-%d')
        except:
            pass
    return None

def load_csv():
    """Load the corrected CSV"""
    data = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            obj_id = row.get('object_id', '').strip()
            if not obj_id or obj_id == '':
                continue
            data.append({
                'object_id': obj_id,
                'adres': row.get('Adres', '').strip(),
                'postcode': row.get('Postcode', '').strip(),
                'plaats': row.get('Plaats', '').strip(),
                'capaciteit': int(row.get('Aant. pers.', '0') or 0) if row.get('Aant. pers.', '').strip().isdigit() else None,
                'slaapkamers': int(row.get('Aant. SK', '0') or 0) if row.get('Aant. SK', '').strip().isdigit() else None,
                'facturatie': row.get('Facturatie', '').strip(),
                # Verhuur
                'verhuur_start': parse_date(row.get('Startdatum', '')),
                'verhuur_eind': parse_date(row.get('Einddatum Min. Per.', '')),
                'verhuur_relatie_id': row.get('relatie_id', '').strip() if 'relatie_id' in row else None,
                'verhuur_excl': parse_euro(row.get('Verhuur EXCL. BTW', '')),
                'kale_verhuur': parse_euro(row.get('Kale verhuurprijs', '')),
                'voorschot_gwe': parse_euro(row.get('Voorschot GWE', '')),
                'overige_kosten': parse_euro(row.get(' Overige kosten ', '')),
                # Inhuur
                'eigenaar': row.get('Eigenaar', '').strip(),
                'eigenaar_relatie_id': None,  # Will extract from row
                'inhuur_excl': parse_euro(row.get('Inhuur EXCL BTW', '')),
                'kale_inhuur': parse_euro(row.get('Kale inhuurprijs', '')),
                'inhuur_start': None,
                'inhuur_eind': None,
            })
            # Find eigenaar relatie_id (it's a second column named relatie_id)
            # The CSV has duplicate column names, need to handle differently
    return data

def main():
    print("=== Loading CSV data ===")
    csv_data = load_csv()
    print(f"Loaded {len(csv_data)} entries from CSV")
    
    print("\n=== Connecting to database ===")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Get current huizen data
    db_huizen = {}
    for row in conn.execute("SELECT * FROM huizen"):
        db_huizen[row['object_id']] = dict(row)
    print(f"Database has {len(db_huizen)} huizen entries")
    
    # Find differences
    differences = []
    new_entries = []
    
    for csv_row in csv_data:
        obj_id = csv_row['object_id']
        
        if obj_id not in db_huizen:
            new_entries.append(csv_row)
            continue
        
        db_row = db_huizen[obj_id]
        diffs = {}
        
        # Compare fields
        if csv_row['adres'] and csv_row['adres'] != db_row.get('adres', ''):
            diffs['adres'] = {'old': db_row.get('adres'), 'new': csv_row['adres']}
        
        if csv_row['postcode'] and csv_row['postcode'] != (db_row.get('postcode') or ''):
            diffs['postcode'] = {'old': db_row.get('postcode'), 'new': csv_row['postcode']}
            
        if csv_row['plaats'] and csv_row['plaats'] != (db_row.get('plaats') or ''):
            diffs['plaats'] = {'old': db_row.get('plaats'), 'new': csv_row['plaats']}
            
        if csv_row['capaciteit'] and csv_row['capaciteit'] != db_row.get('capaciteit_personen'):
            diffs['capaciteit_personen'] = {'old': db_row.get('capaciteit_personen'), 'new': csv_row['capaciteit']}
            
        if csv_row['slaapkamers'] and csv_row['slaapkamers'] != db_row.get('aantal_slaapkamers'):
            diffs['aantal_slaapkamers'] = {'old': db_row.get('aantal_slaapkamers'), 'new': csv_row['slaapkamers']}
        
        if diffs:
            differences.append({'object_id': obj_id, 'diffs': diffs})
    
    print(f"\n=== RESULTS ===")
    print(f"New entries (not in DB): {len(new_entries)}")
    print(f"Entries with differences: {len(differences)}")
    
    if new_entries:
        print(f"\n--- NEW ENTRIES ---")
        for e in new_entries[:10]:
            print(f"  {e['object_id']}: {e['adres']}")
        if len(new_entries) > 10:
            print(f"  ... and {len(new_entries) - 10} more")
    
    if differences:
        print(f"\n--- DIFFERENCES ---")
        for d in differences[:20]:
            print(f"\n{d['object_id']}:")
            for field, vals in d['diffs'].items():
                print(f"  {field}: '{vals['old']}' → '{vals['new']}'")
        if len(differences) > 20:
            print(f"\n... and {len(differences) - 20} more entries with differences")
    
    conn.close()
    return differences, new_entries

if __name__ == "__main__":
    main()
