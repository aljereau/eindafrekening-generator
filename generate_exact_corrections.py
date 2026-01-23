#!/usr/bin/env python3
"""
Generate a report of what needs to be changed IN EXACT
to match the database object_ids.

For conflicting entries, the database is the source of truth.
"""
import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_V2_PATH = BASE_DIR / "database" / "ryanrent_v2.db"
CSV_PATH = BASE_DIR / "Shared/Sources/csv_data/1-CoHousingNL_B.V.-23-01-2026-HRMCostCenters.csv"
REPORT_PATH = BASE_DIR / "exact_corrections_needed.md"

def normalize_address(addr: str) -> str:
    if not addr:
        return ""
    return (addr.lower()
            .replace(",", "")
            .replace("'s-", "s-")
            .replace("'s ", "s ")
            .replace("-", " ")
            .strip())

def main():
    # Load CSV
    csv_data = {}
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            code = row['Code'].strip()
            desc = row['Omschrijving'].strip()
            csv_data[code] = desc
    
    # Load DB
    conn = sqlite3.connect(DB_V2_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT object_id, adres, plaats FROM huizen ORDER BY CAST(object_id AS INTEGER)")
    db_data = {row[0]: f"{row[1]} {row[2] or ''}".strip() for row in cursor.fetchall()}
    conn.close()
    
    # Find mismatches where DB has a different address than CSV for the same code
    exact_changes = []
    db_only = []
    
    for obj_id, db_addr in db_data.items():
        padded_id = obj_id.zfill(4)
        
        if padded_id in csv_data:
            csv_addr = csv_data[padded_id]
            norm_db = normalize_address(db_addr)
            norm_csv = normalize_address(csv_addr)
            
            # Check if they're different (not just formatting)
            if not (norm_db in norm_csv or norm_csv in norm_db):
                # This is a real mismatch - CSV needs to be changed
                exact_changes.append({
                    'code': padded_id,
                    'csv_has': csv_addr,
                    'should_be': db_addr
                })
        else:
            # DB has this code but CSV doesn't - needs to be added to Exact
            db_only.append({
                'code': padded_id,
                'address': db_addr
            })
    
    # Generate report
    report = []
    report.append("# Exact Kostenplaatsen Corrections Needed")
    report.append(f"\n**Generated:** 2026-01-23 10:16")
    report.append(f"\n**Action:** Update these entries in Exact to match the database")
    report.append("\n---")
    
    report.append(f"\n## ⚠️ Change These Codes in Exact ({len(exact_changes)})")
    report.append("\nThese kostenplaatsen exist in Exact but have the WRONG address. Change them to match your database:")
    report.append("\n| Code | Currently in Exact | Change To (from DB) |")
    report.append("|------|-------------------|---------------------|")
    for item in sorted(exact_changes, key=lambda x: int(x['code'])):
        report.append(f"| {item['code']} | {item['csv_has'][:40]} | **{item['should_be'][:40]}** |")
    
    report.append(f"\n## ➕ Add These Codes to Exact ({len(db_only)})")
    report.append("\nThese properties exist in your database but NOT in Exact. Add them:")
    report.append("\n| Code | Address |")
    report.append("|------|---------|")
    for item in sorted(db_only, key=lambda x: int(x['code'])):
        report.append(f"| {item['code']} | {item['address']} |")
    
    report.append("\n---")
    report.append("\n## Summary")
    report.append(f"- **Fix in Exact:** {len(exact_changes)} entries")
    report.append(f"- **Add to Exact:** {len(db_only)} entries")
    
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"Report saved to: {REPORT_PATH}")
    print(f"\nSummary:")
    print(f"  ⚠️ Fix in Exact: {len(exact_changes)} entries")
    print(f"  ➕ Add to Exact: {len(db_only)} entries")

if __name__ == "__main__":
    main()
