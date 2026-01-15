#!/usr/bin/env python3
"""
Import extracted contract data into the RyanRent database.
- Adds eigenaren to relaties table
- Creates/updates inhuur_contracten
- Creates/updates verhuur_contracten
"""

import csv
import sqlite3
import os
from datetime import datetime

DB_PATH = "database/ryanrent_v2.db"
CSV_PATH = "Shared/Sources/tradiro_llm_extracted.csv"


def normalize_address(addr):
    """Normalize address for matching"""
    if not addr:
        return ""
    addr = addr.lower().strip()
    # Remove common variations
    addr = addr.replace("straat", "str").replace("laan", "ln").replace("weg", "wg")
    addr = addr.replace("-", " ").replace("  ", " ")
    return addr


def parse_date(date_str):
    """Parse date string to YYYY-MM-DD format"""
    if not date_str or date_str in ['null', 'N/A', '']:
        return None
    try:
        # Try DD-MM-YYYY
        if '-' in date_str:
            parts = date_str.split('-')
            if len(parts) == 3:
                if len(parts[2]) == 4:  # DD-MM-YYYY
                    return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                elif len(parts[0]) == 4:  # YYYY-MM-DD
                    return date_str
        return None
    except:
        return None


def parse_float(val):
    """Parse float value"""
    if not val or val in ['null', 'N/A', '', 'None']:
        return None
    try:
        return float(str(val).replace(',', '.'))
    except:
        return None


def parse_int(val):
    """Parse int value"""
    if not val or val in ['null', 'N/A', '', 'None']:
        return None
    try:
        return int(float(val))
    except:
        return None


def is_ryanrent(name):
    """Check if name is RyanRent"""
    if not name:
        return False
    name = name.lower()
    return 'ryanrent' in name or 'ryan rent' in name


def is_tradiro(name):
    """Check if name is Tradiro"""
    if not name:
        return False
    name = name.lower()
    return 'tradiro' in name


def main():
    # Load CSV data
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        contracts = list(reader)
    
    print(f"Loaded {len(contracts)} contracts from CSV")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Load existing huizen for address matching
    cur.execute("SELECT id, object_id, adres, postcode, plaats FROM huizen")
    huizen = {normalize_address(row['adres']): dict(row) for row in cur.fetchall()}
    huizen_by_id = {row['id']: row for row in cur.execute("SELECT * FROM huizen").fetchall()}
    
    # Load existing relaties
    cur.execute("SELECT id, naam, kvk_nummer FROM relaties")
    existing_relaties = {row['naam'].lower(): dict(row) for row in cur.fetchall()}
    
    # Statistics
    stats = {
        'new_eigenaren': 0,
        'inhuur_created': 0,
        'inhuur_updated': 0,
        'verhuur_created': 0,
        'verhuur_updated': 0,
        'unmatched_addresses': [],
        'skipped_tradiro_internal': 0
    }
    
    # Get or create Tradiro relatie for verhuur contracts
    tradiro_relatie = None
    for name, rel in existing_relaties.items():
        if 'tradiro services' in name:
            tradiro_relatie = rel
            break
    
    if not tradiro_relatie:
        cur.execute("""
            INSERT INTO relaties (naam, type, kvk_nummer, is_klant)
            VALUES (?, ?, ?, 1)
        """, ("Tradiro Services B.V.", "bedrijf", "59979135"))
        tradiro_relatie = {'id': cur.lastrowid, 'naam': 'Tradiro Services B.V.'}
        print(f"Created Tradiro Services relatie: {tradiro_relatie['id']}")
    
    for contract in contracts:
        verhuurder = contract.get('verhuurder_naam', '').strip()
        adres = contract.get('adres', '').strip()
        
        if not verhuurder or not adres:
            continue
        
        # Skip Tradiro internal contracts
        if is_tradiro(verhuurder) and not is_ryanrent(verhuurder):
            stats['skipped_tradiro_internal'] += 1
            continue
        
        # Match to huizen
        normalized_addr = normalize_address(adres)
        house = None
        for db_addr, h in huizen.items():
            if normalized_addr in db_addr or db_addr in normalized_addr:
                house = h
                break
        
        if not house:
            # Try with postcode
            postcode = contract.get('postcode', '').strip()
            for db_addr, h in huizen.items():
                if postcode and h.get('postcode') and postcode.replace(' ', '') == h['postcode'].replace(' ', ''):
                    house = h
                    break
        
        if not house:
            stats['unmatched_addresses'].append(f"{adres} ({contract.get('filename', '')})")
            continue
        
        # Determine contract type
        if is_ryanrent(verhuurder):
            # VERHUUR: RyanRent rents TO Tradiro
            # Create verhuur_contracten entry
            cur.execute("""
                INSERT OR REPLACE INTO verhuur_contracten 
                (relatie_id, house_id, start_date, end_date, huur_excl_btw, borg_override, contract_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                tradiro_relatie['id'],
                house['id'],
                parse_date(contract.get('start_datum')),
                parse_date(contract.get('eind_datum')),
                parse_float(contract.get('huurprijs_excl_btw')),
                parse_float(contract.get('borg')),
                contract.get('contract_type', 'onbepaalde_tijd')
            ))
            stats['verhuur_created'] += 1
        else:
            # INHUUR: Eigenaar rents TO RyanRent
            # First, ensure eigenaar exists in relaties
            eigenaar_key = verhuurder.lower()
            if eigenaar_key not in existing_relaties:
                # Create new eigenaar
                cur.execute("""
                    INSERT INTO relaties (naam, type, kvk_nummer, iban, email, telefoonnummer, adres, postcode, plaats, is_eigenaar)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    verhuurder,
                    contract.get('verhuurder_type', 'bedrijf'),
                    contract.get('verhuurder_kvk') if contract.get('verhuurder_kvk') not in ['null', ''] else None,
                    contract.get('verhuurder_iban') if contract.get('verhuurder_iban') not in ['null', ''] else None,
                    contract.get('verhuurder_email') if contract.get('verhuurder_email') not in ['null', ''] else None,
                    contract.get('verhuurder_telefoon') if contract.get('verhuurder_telefoon') not in ['null', ''] else None,
                    contract.get('verhuurder_adres') if contract.get('verhuurder_adres') not in ['null', ''] else None,
                    contract.get('verhuurder_postcode') if contract.get('verhuurder_postcode') not in ['null', ''] else None,
                    contract.get('verhuurder_plaats') if contract.get('verhuurder_plaats') not in ['null', ''] else None,
                ))
                eigenaar_id = cur.lastrowid
                existing_relaties[eigenaar_key] = {'id': eigenaar_id, 'naam': verhuurder}
                stats['new_eigenaren'] += 1
            else:
                eigenaar_id = existing_relaties[eigenaar_key]['id']
            
            # Create inhuur_contracten entry
            cur.execute("""
                INSERT OR REPLACE INTO inhuur_contracten 
                (house_id, relatie_id, inhuur_excl_btw, borg, start_datum, eind_datum, 
                 minimale_duur_maanden, opzegtermijn_maanden, vve_kosten)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                house['id'],
                eigenaar_id,
                parse_float(contract.get('huurprijs_excl_btw')),
                parse_float(contract.get('borg')),
                parse_date(contract.get('start_datum')),
                parse_date(contract.get('eind_datum')),
                parse_int(contract.get('minimale_duur_maanden')),
                parse_int(contract.get('opzegtermijn_maanden')),
                parse_float(contract.get('vve_kosten')),
            ))
            stats['inhuur_created'] += 1
    
    conn.commit()
    
    # Print results
    print("\n" + "="*50)
    print("IMPORT RESULTS")
    print("="*50)
    print(f"New eigenaren added: {stats['new_eigenaren']}")
    print(f"Inhuur contracts created: {stats['inhuur_created']}")
    print(f"Verhuur contracts created: {stats['verhuur_created']}")
    print(f"Tradiro internal skipped: {stats['skipped_tradiro_internal']}")
    print(f"Unmatched addresses: {len(stats['unmatched_addresses'])}")
    
    if stats['unmatched_addresses']:
        print("\nUnmatched addresses:")
        for addr in stats['unmatched_addresses'][:20]:
            print(f"  - {addr}")
        if len(stats['unmatched_addresses']) > 20:
            print(f"  ... and {len(stats['unmatched_addresses'])-20} more")
    
    conn.close()
    print("\n✅ Import complete!")


if __name__ == '__main__':
    main()
