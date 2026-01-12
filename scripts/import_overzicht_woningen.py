#!/usr/bin/env python3
"""
Import overzicht_rr_woningen.xlsx into the database.
Updates huizen, verhuur_contracten, inhuur_contracten with comprehensive data.
"""

import pandas as pd
import sqlite3
from datetime import datetime
import re

EXCEL_FILE = "Shared/Sources/overzicht_rr_woningen.xlsx"
DB_PATH = "database/ryanrent_mock.db"


def parse_date(val):
    """Parse date from various formats"""
    if pd.isna(val):
        return None
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d')
    if isinstance(val, (int, float)):
        # Excel serial date
        try:
            from datetime import timedelta
            base = datetime(1899, 12, 30)
            return (base + timedelta(days=int(val))).strftime('%Y-%m-%d')
        except:
            return None
    if isinstance(val, str):
        for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y']:
            try:
                return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
            except:
                pass
    return None


def parse_float(val):
    if pd.isna(val):
        return None
    try:
        return float(val)
    except:
        return None


def main():
    print(f"📖 Reading: {EXCEL_FILE}")
    df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
    print(f"   {len(df)} rows loaded")
    
    print(f"\n📦 Connecting to: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    stats = {
        'huizen_updated': 0,
        'verhuur_created': 0,
        'verhuur_updated': 0,
        'inhuur_updated': 0,
        'skipped': 0
    }
    
    for _, row in df.iterrows():
        object_id = str(row.get('object_id', '')).strip()
        if not object_id or object_id == 'nan':
            stats['skipped'] += 1
            continue
        
        # Pad object_id to 4 digits if numeric
        if object_id.isdigit():
            object_id = object_id.zfill(4)
        
        # Check if house exists
        cursor.execute("SELECT object_id FROM huizen WHERE object_id = ?", (object_id,))
        if not cursor.fetchone():
            print(f"   ⚠️ House {object_id} not found, skipping")
            stats['skipped'] += 1
            continue
        
        # --- Update HUIZEN ---
        cursor.execute("""
            UPDATE huizen SET
                adres = COALESCE(?, adres),
                postcode = COALESCE(?, postcode),
                plaats = COALESCE(?, plaats),
                aantal_pers = COALESCE(?, aantal_pers),
                aantal_sk = COALESCE(?, aantal_sk),
                voorschot_gwe = COALESCE(?, voorschot_gwe),
                gewijzigd_op = CURRENT_TIMESTAMP
            WHERE object_id = ?
        """, (
            row.get('Adres') if not pd.isna(row.get('Adres')) else None,
            row.get('Postcode') if not pd.isna(row.get('Postcode')) else None,
            row.get('Plaats') if not pd.isna(row.get('Plaats')) else None,
            parse_float(row.get('Aant. pers.')),
            parse_float(row.get('Aant. SK')),
            parse_float(row.get('Voorschot GWE')),
            object_id
        ))
        if cursor.rowcount > 0:
            stats['huizen_updated'] += 1
        
        # --- Update/Create VERHUUR_CONTRACTEN ---
        huurder = str(row.get('Huurder', '')) if not pd.isna(row.get('Huurder')) else None
        start_datum = parse_date(row.get('Startdatum'))
        
        if huurder or start_datum:
            # Check if verhuur contract exists for this house
            cursor.execute("SELECT id FROM verhuur_contracten WHERE object_id = ?", (object_id,))
            existing = cursor.fetchone()
            
            verhuur_data = {
                'start_datum': start_datum,
                'eind_datum': parse_date(row.get('Einddatum Min. Per.')),
                'opgezegd_datum': parse_date(row.get('Opgezegd')),
                'huurder_naam': huurder,
                'mutatie_notities': str(row.get('Mutatie Daan')) if not pd.isna(row.get('Mutatie Daan')) else None,
                'marge': parse_float(row.get('Marge')),
                'verhuur_incl_btw': parse_float(row.get('Verhuur INCL. BTW')),
                'verhuur_excl_btw': parse_float(row.get('Verhuur EXCL. BTW')),
                'kale_huur': parse_float(row.get('Kale verhuurprijs')),
                'overige_kosten': parse_float(row.get('Overige kosten')),
                'afval_kosten': parse_float(row.get('Afval ')),
            }
            
            if existing:
                cursor.execute("""
                    UPDATE verhuur_contracten SET
                        start_datum = COALESCE(?, start_datum),
                        eind_datum = COALESCE(?, eind_datum),
                        opgezegd_datum = COALESCE(?, opgezegd_datum),
                        huurder_naam = COALESCE(?, huurder_naam),
                        mutatie_notities = COALESCE(?, mutatie_notities),
                        marge = COALESCE(?, marge),
                        verhuur_incl_btw = COALESCE(?, verhuur_incl_btw),
                        verhuur_excl_btw = COALESCE(?, verhuur_excl_btw),
                        kale_huur = COALESCE(?, kale_huur),
                        overige_kosten = COALESCE(?, overige_kosten),
                        afval_kosten = COALESCE(?, afval_kosten),
                        gewijzigd_op = CURRENT_TIMESTAMP
                    WHERE object_id = ?
                """, (
                    verhuur_data['start_datum'],
                    verhuur_data['eind_datum'],
                    verhuur_data['opgezegd_datum'],
                    verhuur_data['huurder_naam'],
                    verhuur_data['mutatie_notities'],
                    verhuur_data['marge'],
                    verhuur_data['verhuur_incl_btw'],
                    verhuur_data['verhuur_excl_btw'],
                    verhuur_data['kale_huur'],
                    verhuur_data['overige_kosten'],
                    verhuur_data['afval_kosten'],
                    object_id
                ))
                stats['verhuur_updated'] += 1
            else:
                # Create new verhuur contract with dummy klant_id
                cursor.execute("""
                    INSERT INTO verhuur_contracten (
                        object_id, klant_id, start_datum, eind_datum, opgezegd_datum,
                        huurder_naam, mutatie_notities, marge, verhuur_incl_btw, verhuur_excl_btw,
                        kale_huur, overige_kosten, afval_kosten
                    ) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    object_id,
                    verhuur_data['start_datum'] or '2025-01-01',
                    verhuur_data['eind_datum'],
                    verhuur_data['opgezegd_datum'],
                    verhuur_data['huurder_naam'],
                    verhuur_data['mutatie_notities'],
                    verhuur_data['marge'] or 0,
                    verhuur_data['verhuur_incl_btw'] or 0,
                    verhuur_data['verhuur_excl_btw'] or 0,
                    verhuur_data['kale_huur'] or 0,
                    verhuur_data['overige_kosten'] or 0,
                    verhuur_data['afval_kosten'] or 0,
                ))
                stats['verhuur_created'] += 1
        
        # --- Update INHUUR_CONTRACTEN ---
        eigenaar = str(row.get('Eigenaar', '')) if not pd.isna(row.get('Eigenaar')) else None
        facturatie = str(row.get('Facturatie', '')) if not pd.isna(row.get('Facturatie')) else None
        
        cursor.execute("SELECT id FROM inhuur_contracten WHERE object_id = ?", (object_id,))
        existing_inhuur = cursor.fetchone()
        
        inhuur_data = {
            'facturatie': facturatie,
            'inhuur_prijs_incl_btw': parse_float(row.get('Inhuur INCL BTW')),
            'inhuur_prijs_excl_btw': parse_float(row.get('Inhuur EXCL BTW')),
            'kale_inhuurprijs': parse_float(row.get('Kale inhuurprijs')),
            'start_date': parse_date(row.get('Startdatum.1')),
            'end_date': parse_date(row.get('Einddatum Min. Per..1')),
        }
        
        if existing_inhuur:
            cursor.execute("""
                UPDATE inhuur_contracten SET
                    facturatie = COALESCE(?, facturatie),
                    inhuur_prijs_incl_btw = COALESCE(?, inhuur_prijs_incl_btw),
                    inhuur_prijs_excl_btw = COALESCE(?, inhuur_prijs_excl_btw),
                    kale_inhuurprijs = COALESCE(?, kale_inhuurprijs),
                    start_date = COALESCE(?, start_date),
                    end_date = COALESCE(?, end_date),
                    gewijzigd_op = CURRENT_TIMESTAMP
                WHERE object_id = ?
            """, (
                inhuur_data['facturatie'],
                inhuur_data['inhuur_prijs_incl_btw'],
                inhuur_data['inhuur_prijs_excl_btw'],
                inhuur_data['kale_inhuurprijs'],
                inhuur_data['start_date'],
                inhuur_data['end_date'],
                object_id
            ))
            stats['inhuur_updated'] += 1
        elif eigenaar:
            # Need to create inhuur contract - first find/create leverancier
            cursor.execute("SELECT id FROM leveranciers WHERE naam = ?", (eigenaar,))
            lev = cursor.fetchone()
            if lev:
                lev_id = lev[0]
            else:
                cursor.execute("INSERT INTO leveranciers (naam) VALUES (?)", (eigenaar,))
                lev_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO inhuur_contracten (
                    object_id, leverancier_id, facturatie, 
                    inhuur_prijs_incl_btw, inhuur_prijs_excl_btw, kale_inhuurprijs,
                    start_date, end_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                object_id, lev_id, inhuur_data['facturatie'],
                inhuur_data['inhuur_prijs_incl_btw'],
                inhuur_data['inhuur_prijs_excl_btw'],
                inhuur_data['kale_inhuurprijs'],
                inhuur_data['start_date'],
                inhuur_data['end_date'],
            ))
            stats['inhuur_updated'] += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Import Complete!")
    print(f"   Huizen updated:         {stats['huizen_updated']}")
    print(f"   Verhuur created:        {stats['verhuur_created']}")
    print(f"   Verhuur updated:        {stats['verhuur_updated']}")
    print(f"   Inhuur updated/created: {stats['inhuur_updated']}")
    print(f"   Skipped:                {stats['skipped']}")


if __name__ == "__main__":
    main()
