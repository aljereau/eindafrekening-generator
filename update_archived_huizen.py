#!/usr/bin/env python3
"""
Add object_id column to archived_huizen in ryanrent_v2.db
and populate with A-codes from Exact CSV based on address matching.
"""
import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_V2_PATH = BASE_DIR / "database" / "ryanrent_v2.db"
CSV_PATH = BASE_DIR / "Shared/Sources/csv_data/1-CoHousingNL_B.V.-23-01-2026-HRMCostCenters.csv"

def normalize_address(addr: str) -> str:
    if not addr:
        return ""
    return (addr.lower()
            .replace(",", "")
            .replace("'s-", "s-")
            .replace("'s ", "s ")
            .replace("-", " ")
            .replace(".", "")
            .strip())

def main():
    # Load A-codes from CSV
    a_codes = {}
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            code = row['Code'].strip()
            if code.startswith('A-'):
                desc = row['Omschrijving'].strip()
                a_codes[code] = desc
    
    print(f"Loaded {len(a_codes)} A-codes from CSV")
    
    conn = sqlite3.connect(DB_V2_PATH)
    cursor = conn.cursor()
    
    # Add object_id column if it doesn't exist
    cursor.execute("PRAGMA table_info(archived_huizen)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'object_id' not in columns:
        print("Adding object_id column to archived_huizen...")
        cursor.execute("ALTER TABLE archived_huizen ADD COLUMN object_id TEXT")
        conn.commit()
    
    # Get all archived houses
    cursor.execute("SELECT id, adres, plaats FROM archived_huizen")
    archived = cursor.fetchall()
    print(f"Found {len(archived)} archived houses")
    
    # Match and update
    matched = 0
    not_matched = []
    
    for db_id, adres, plaats in archived:
        full_addr = f"{adres} {plaats or ''}".strip()
        norm_db = normalize_address(full_addr)
        
        found_code = None
        for code, csv_addr in a_codes.items():
            norm_csv = normalize_address(csv_addr)
            if norm_db in norm_csv or norm_csv in norm_db:
                found_code = code
                break
        
        if found_code:
            cursor.execute("UPDATE archived_huizen SET object_id = ? WHERE id = ?", 
                         (found_code, db_id))
            matched += 1
        else:
            not_matched.append((db_id, full_addr))
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Matched and updated: {matched}")
    print(f"❌ Not matched: {len(not_matched)}")
    
    if not_matched[:10]:
        print("\nFirst 10 unmatched:")
        for db_id, addr in not_matched[:10]:
            print(f"  [{db_id}] {addr}")

if __name__ == "__main__":
    main()
