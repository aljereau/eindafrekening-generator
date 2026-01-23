#!/usr/bin/env python3
"""
Compare Exact CSV kostenplaatsen with database huizen.
Generates a report of mismatches and migration SQL.
"""
import csv
import sqlite3
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "database" / "ryanrent_v2.db"
CSV_PATH = BASE_DIR / "Shared/Sources/csv_data/1-CoHousingNL_B.V.-23-01-2026-HRMCostCenters.csv"
REPORT_PATH = BASE_DIR / "kostenplaatsen_comparison_report.md"

def normalize_address(addr: str) -> str:
    """Normalize address for comparison."""
    if not addr:
        return ""
    return addr.lower().replace(",", "").replace("'s-", "s-").replace("'s ", "s ").strip()

def main():
    # Load CSV data
    csv_data = {}
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            code = row['Code'].strip()
            desc = row['Omschrijving'].strip()
            csv_data[code] = desc
    
    # Load database data
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT object_id, adres, plaats FROM huizen ORDER BY CAST(object_id AS INTEGER)")
    db_data = {row[0]: f"{row[1]} {row[2] or ''}".strip() for row in cursor.fetchall()}
    conn.close()
    
    # Compare
    matches = []
    mismatches = []
    db_only = []
    csv_only_numeric = []
    csv_only_alpha = []
    
    for obj_id, db_addr in db_data.items():
        padded_id = obj_id.zfill(4)  # Pad to 4 digits for CSV lookup
        if padded_id in csv_data:
            csv_addr = csv_data[padded_id]
            # Compare normalized addresses
            if normalize_address(db_addr) in normalize_address(csv_addr) or normalize_address(csv_addr) in normalize_address(db_addr):
                matches.append((obj_id, db_addr, csv_addr))
            else:
                mismatches.append((obj_id, db_addr, csv_addr))
        else:
            db_only.append((obj_id, db_addr))
    
    # Find CSV entries not in DB
    db_codes = {obj_id.zfill(4) for obj_id in db_data.keys()}
    for code, desc in csv_data.items():
        if code.startswith('A-'):
            csv_only_alpha.append((code, desc))
        elif code not in db_codes and code.isdigit() or (code.startswith('0') and code[1:].isdigit()):
            csv_only_numeric.append((code, desc))
    
    # Generate report
    report = []
    report.append("# Kostenplaatsen Comparison Report")
    report.append(f"\n**Generated:** 2026-01-23 09:58")
    report.append(f"\n## Summary")
    report.append(f"- ✅ Matches: {len(matches)}")
    report.append(f"- ❌ Mismatches: {len(mismatches)}")
    report.append(f"- 📦 DB only (not in CSV): {len(db_only)}")
    report.append(f"- 📄 CSV numeric (not in DB): {len(csv_only_numeric)}")
    report.append(f"- 🗄️ CSV A-codes (archived): {len(csv_only_alpha)}")
    
    if mismatches:
        report.append(f"\n## ❌ Mismatches ({len(mismatches)})")
        report.append("\n| Object ID | Database Address | Exact CSV Address |")
        report.append("|-----------|------------------|-------------------|")
        for obj_id, db_addr, csv_addr in sorted(mismatches, key=lambda x: int(x[0]) if x[0].isdigit() else 9999):
            report.append(f"| {obj_id} | {db_addr} | {csv_addr} |")
    
    if db_only:
        report.append(f"\n## 📦 In Database Only ({len(db_only)})")
        report.append("\nThese properties exist in DB but not in Exact CSV:")
        report.append("\n| Object ID | Address |")
        report.append("|-----------|---------|")
        for obj_id, addr in sorted(db_only, key=lambda x: int(x[0]) if x[0].isdigit() else 9999):
            report.append(f"| {obj_id} | {addr} |")
    
    if csv_only_numeric:
        report.append(f"\n## 📄 In CSV Only - Numeric ({len(csv_only_numeric)})")
        report.append("\nThese exist in Exact but not in database:")
        report.append("\n| Code | Address |")
        report.append("|------|---------|")
        for code, desc in sorted(csv_only_numeric, key=lambda x: int(x[0].lstrip('0') or 0)):
            report.append(f"| {code} | {desc} |")
    
    report.append(f"\n## 🗄️ A-Code Properties ({len(csv_only_alpha)})")
    report.append("\nArchived properties using A-code system in Exact:")
    report.append("\n| Code | Address |")
    report.append("|------|---------|")
    for code, desc in sorted(csv_only_alpha)[:30]:  # Show first 30
        report.append(f"| {code} | {desc} |")
    if len(csv_only_alpha) > 30:
        report.append(f"\n*...and {len(csv_only_alpha) - 30} more A-code entries*")
    
    # Write report
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"Report written to: {REPORT_PATH}")
    print(f"\nSummary:")
    print(f"  ✅ Matches: {len(matches)}")
    print(f"  ❌ Mismatches: {len(mismatches)}")
    print(f"  📦 DB only: {len(db_only)}")
    print(f"  📄 CSV numeric only: {len(csv_only_numeric)}")
    print(f"  🗄️ CSV A-codes: {len(csv_only_alpha)}")

if __name__ == "__main__":
    main()
