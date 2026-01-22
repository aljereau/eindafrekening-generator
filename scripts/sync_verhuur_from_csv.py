#!/usr/bin/env python3
"""
Sync verhuur contract data from woningoverzicht Excel/CSV.
Updates verhuur_contracten with latest dates and financials.

Note: CSV has duplicate column names (Startdatum appears twice),
so we read by position, not by header name.

Usage:
    python sync_verhuur_from_csv.py
"""

import sqlite3
import csv
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "database" / "ryanrent_v2.db"
CSV_PATH = BASE_DIR / "Shared" / "Sources" / "excel_data" / "woningoverzichtdata_20012026.csv"

# CSV column positions (0-indexed) - verhuur data
COL_OBJECT_ID = 0
COL_VERHUUR_START = 7        # Column H: Startdatum (verhuur)
COL_VERHUUR_END = 8          # Column I: Einddatum Min. Per. (verhuur)
COL_RELATIE_ID_HUURDER = 10  # relatie_id_huurder
COL_KALE_VERHUUR = 18        # Kale verhuurprijs
COL_VOORSCHOT_GWE = 19       # Voorschot GWE
COL_OVERIGE_KOSTEN = 20      # Overige kosten
COL_VERHUUR_EXCL = 16        # Verhuur EXCL. BTW


def parse_dutch_date(date_str: str) -> str | None:
    """Parse Dutch date format to ISO (YYYY-MM-DD)."""
    if not date_str or date_str.strip() == '':
        return None
    date_str = date_str.strip()
    
    formats = [
        "%d/%m/%Y",   # 31/12/2025
        "%d/%m/%y",   # 31/12/25 (2-digit year)
        "%d-%m-%Y",   # 31-12-2025
        "%d-%m-%y",   # 31-12-25
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_dutch_money(money_str: str) -> float:
    """Parse Dutch money format (€ 1.234,56) to float."""
    if not money_str or money_str.strip() == '' or money_str.strip() == '-':
        return 0.0
    cleaned = money_str.replace('€', '').replace(' ', '').strip()
    cleaned = cleaned.replace('.', '').replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def get_cell(row: list, idx: int) -> str:
    """Safely get cell value by index."""
    if idx < len(row):
        return row[idx].strip() if row[idx] else ''
    return ''


def sync_verhuur():
    """Sync verhuur contracts from CSV."""
    print(f"📂 Reading: {CSV_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Read CSV as list (not dict) to handle duplicate column names
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        header = next(reader)  # Skip header
        rows = list(reader)
    
    print(f"   Found {len(rows)} rows in CSV")
    
    updated = 0
    created = 0
    skipped = 0
    errors = []
    
    for row in rows:
        object_id = get_cell(row, COL_OBJECT_ID)
        if not object_id:
            continue
        
        # Parse verhuur fields by position
        start_date = parse_dutch_date(get_cell(row, COL_VERHUUR_START))
        end_date = parse_dutch_date(get_cell(row, COL_VERHUUR_END))
        kale_huur = parse_dutch_money(get_cell(row, COL_KALE_VERHUUR))
        voorschot_gwe = parse_dutch_money(get_cell(row, COL_VOORSCHOT_GWE))
        overige_kosten = parse_dutch_money(get_cell(row, COL_OVERIGE_KOSTEN))
        relatie_id = get_cell(row, COL_RELATIE_ID_HUURDER)
        
        # Skip if no verhuur data
        if not start_date and kale_huur == 0:
            skipped += 1
            continue
        
        # Get house_id
        cursor.execute("SELECT id FROM huizen WHERE object_id = ?", (object_id,))
        house_row = cursor.fetchone()
        if not house_row:
            errors.append(f"House not found: {object_id}")
            continue
        house_id = house_row[0]
        
        # Check for existing verhuur contract
        cursor.execute("""
            SELECT id, start_date, end_date, kale_huur 
            FROM verhuur_contracten 
            WHERE house_id = ? 
            ORDER BY start_date DESC 
            LIMIT 1
        """, (house_id,))
        existing = cursor.fetchone()
        
        # Calculate huur_excl_btw (kale + gwe + overige)
        huur_excl_btw = kale_huur + voorschot_gwe + overige_kosten
        
        if existing:
            contract_id = existing[0]
            old_start = existing[1]
            old_end = existing[2]
            # Update - use CSV dates if available
            cursor.execute("""
                UPDATE verhuur_contracten SET
                    start_date = ?,
                    end_date = ?,
                    kale_huur = ?,
                    huur_excl_btw = ?,
                    voorschot_gwe_excl_btw = ?,
                    overige_kosten = ?
                WHERE id = ?
            """, (start_date or old_start, end_date or old_end, kale_huur, 
                  huur_excl_btw, voorschot_gwe, overige_kosten, contract_id))
            updated += 1
        else:
            # Create new contract if we have relatie_id
            if relatie_id and relatie_id.isdigit():
                cursor.execute("""
                    INSERT INTO verhuur_contracten 
                    (house_id, relatie_id, start_date, end_date, kale_huur, huur_excl_btw, 
                     voorschot_gwe_excl_btw, overige_kosten, huur_btw_pct, voorschot_gwe_btw_pct)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0.09, 0.21)
                """, (house_id, int(relatie_id), start_date, end_date, kale_huur, 
                      huur_excl_btw, voorschot_gwe, overige_kosten))
                created += 1
            else:
                skipped += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Sync complete:")
    print(f"   Updated: {updated}")
    print(f"   Created: {created}")
    print(f"   Skipped: {skipped}")
    if errors:
        print(f"   Errors: {len(errors)}")
        for e in errors[:5]:
            print(f"     - {e}")


if __name__ == "__main__":
    sync_verhuur()
