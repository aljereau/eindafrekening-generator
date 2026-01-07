#!/usr/bin/env python3
"""
Import data from aub_huizenlijst.xlsx into the database.
Updates huizen, leveranciers, and inhuur_contracten tables.
"""

import openpyxl
import sqlite3
import os
from datetime import datetime

# Paths
EXCEL_FILE = "Shared/Sources/aub_huizenlijst.xlsx"
DB_PATH = "database/ryanrent_mock.db"

def parse_date(val):
    """Parse date from Excel value"""
    if not val:
        return None
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d')
    if isinstance(val, str):
        # Try common formats
        for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']:
            try:
                return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
            except:
                pass
    return None

def parse_int(val):
    """Parse integer from Excel value"""
    if not val:
        return None
    try:
        return int(float(val))
    except:
        return None

def parse_opzegtermijn(val):
    """Parse opzegtermijn from text like '2 maanden'"""
    if not val:
        return None
    val_str = str(val).lower().strip()
    # Extract number from strings like "2 maanden", "1 maand"
    import re
    match = re.search(r'(\d+)', val_str)
    if match:
        return int(match.group(1))
    return None

def main():
    print(f"📖 Reading: {EXCEL_FILE}")
    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active
    
    print(f"📊 Connecting to: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Track stats
    stats = {
        'huizen_updated': 0,
        'leveranciers_created': 0,
        'leveranciers_updated': 0,
        'inhuur_updated': 0,
        'skipped': 0
    }
    
    # Column mapping from Excel (0-indexed)
    # 0: object_id, 1: Huis, 2: Postcode, 5: Eigenaar, 6: Contactpersoon
    # 7: Adres (owner), 8: Postcode (owner), 9: Woonplaats, 10: Telefoon, 11: Mail, 12: Rekeningnr
    # 13: Bedden, 14: Kamers, 15: Tekening, 16: Lijst meters
    # 17: Energie Gas, 20: Energie Electra, 25: Energie Water
    # 28: Begindatum, 29: Einddatum, 42: Opzegtermijn
    
    for row in ws.iter_rows(min_row=2, values_only=True):
        object_id = str(row[0]).strip() if row[0] else None
        if not object_id:
            stats['skipped'] += 1
            continue
        
        # Check if house exists
        cursor.execute("SELECT object_id FROM huizen WHERE object_id = ?", (object_id,))
        if not cursor.fetchone():
            print(f"   ⚠️ House {object_id} not found in DB, skipping")
            stats['skipped'] += 1
            continue
        
        # --- Update HUIZEN ---
        tekening = str(row[15]).strip() if row[15] else None
        lijst_meters = str(row[16]).strip() if row[16] else None
        meter_gas = str(row[17]).strip() if row[17] else None
        meter_electra = str(row[20]).strip() if row[20] else None
        meter_water = str(row[25]).strip() if row[25] else None
        
        # Also update aantal_sk and aantal_pers if available
        kamers = parse_int(row[14])
        bedden = parse_int(row[13])
        
        cursor.execute("""
            UPDATE huizen SET
                tekening = COALESCE(?, tekening),
                lijst_meters = COALESCE(?, lijst_meters),
                meter_gas = COALESCE(?, meter_gas),
                meter_electra = COALESCE(?, meter_electra),
                meter_water = COALESCE(?, meter_water),
                aantal_sk = COALESCE(?, aantal_sk),
                aantal_pers = COALESCE(?, aantal_pers),
                gewijzigd_op = CURRENT_TIMESTAMP
            WHERE object_id = ?
        """, (tekening, lijst_meters, meter_gas, meter_electra, meter_water, kamers, bedden, object_id))
        
        if cursor.rowcount > 0:
            stats['huizen_updated'] += 1
        
        # --- Handle LEVERANCIER ---
        eigenaar_naam = str(row[5]).strip() if row[5] else None
        if eigenaar_naam:
            contactpersoon = str(row[6]).strip() if row[6] else None
            owner_adres = str(row[7]).strip() if row[7] else None
            owner_postcode = str(row[8]).strip() if row[8] else None
            owner_woonplaats = str(row[9]).strip() if row[9] else None
            owner_telefoon = str(row[10]).strip() if row[10] else None
            owner_email = str(row[11]).strip() if row[11] else None
            owner_iban = str(row[12]).strip() if row[12] else None
            
            # Check if leverancier exists by name
            cursor.execute("SELECT id FROM leveranciers WHERE naam = ?", (eigenaar_naam,))
            result = cursor.fetchone()
            
            if result:
                leverancier_id = result[0]
                # Update existing
                cursor.execute("""
                    UPDATE leveranciers SET
                        contactpersoon = COALESCE(?, contactpersoon),
                        adres = COALESCE(?, adres),
                        postcode = COALESCE(?, postcode),
                        woonplaats = COALESCE(?, woonplaats),
                        telefoonnummer = COALESCE(?, telefoonnummer),
                        email = COALESCE(?, email),
                        iban = COALESCE(?, iban),
                        gewijzigd_op = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (contactpersoon, owner_adres, owner_postcode, owner_woonplaats, 
                      owner_telefoon, owner_email, owner_iban, leverancier_id))
                stats['leveranciers_updated'] += 1
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO leveranciers (naam, contactpersoon, adres, postcode, woonplaats, 
                                              telefoonnummer, email, iban)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (eigenaar_naam, contactpersoon, owner_adres, owner_postcode, owner_woonplaats,
                      owner_telefoon, owner_email, owner_iban))
                leverancier_id = cursor.lastrowid
                stats['leveranciers_created'] += 1
            
            # --- Update INHUUR_CONTRACTEN ---
            opzegtermijn = parse_opzegtermijn(row[42])
            start_date = parse_date(row[28])
            end_date = parse_date(row[29])
            
            # Check if contract exists for this house
            cursor.execute("SELECT id FROM inhuur_contracten WHERE object_id = ?", (object_id,))
            contract = cursor.fetchone()
            
            if contract:
                cursor.execute("""
                    UPDATE inhuur_contracten SET
                        leverancier_id = ?,
                        opzegtermijn = COALESCE(?, opzegtermijn),
                        start_date = COALESCE(?, start_date),
                        end_date = COALESCE(?, end_date),
                        gewijzigd_op = CURRENT_TIMESTAMP
                    WHERE object_id = ?
                """, (leverancier_id, opzegtermijn, start_date, end_date, object_id))
                stats['inhuur_updated'] += 1
            else:
                # Create new contract linking house to leverancier
                cursor.execute("""
                    INSERT INTO inhuur_contracten (object_id, leverancier_id, opzegtermijn, start_date, end_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (object_id, leverancier_id, opzegtermijn, start_date, end_date))
                stats['inhuur_updated'] += 1
    
    conn.commit()
    conn.close()
    
    print("\n✅ Import Complete!")
    print(f"   Huizen updated:       {stats['huizen_updated']}")
    print(f"   Leveranciers created: {stats['leveranciers_created']}")
    print(f"   Leveranciers updated: {stats['leveranciers_updated']}")
    print(f"   Inhuur updated:       {stats['inhuur_updated']}")
    print(f"   Skipped:              {stats['skipped']}")

if __name__ == "__main__":
    main()
