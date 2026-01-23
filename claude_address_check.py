#!/usr/bin/env python3
"""
Use Claude for address comparison - smarter about typos vs truly different addresses.
"""
import csv
import sqlite3
import json
from pathlib import Path
from dotenv import load_dotenv
import anthropic

PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

DB_V2_PATH = PROJECT_ROOT / "database" / "ryanrent_v2.db"
CSV_PATH = PROJECT_ROOT / "Shared/Sources/csv_data/1-CoHousingNL_B.V.-23-01-2026-HRMCostCenters.csv"
REPORT_PATH = PROJECT_ROOT / "kostenplaatsen_TRUE_mismatches.md"

def normalize(addr):
    if not addr:
        return ""
    return addr.lower().replace(",", "").replace("'s-", "s-").strip()

def main():
    # Load data
    csv_data = {}
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f, delimiter=';'):
            csv_data[row['Code'].strip()] = row['Omschrijving'].strip()
    
    conn = sqlite3.connect(DB_V2_PATH)
    db_data = {r[0]: f"{r[1]} {r[2] or ''}".strip() for r in conn.execute("SELECT object_id, adres, plaats FROM huizen")}
    conn.close()
    
    # Get potential mismatches
    mismatches = []
    for obj_id, db in db_data.items():
        padded = obj_id.zfill(4) if obj_id.isdigit() else obj_id
        if padded in csv_data:
            csv_a = csv_data[padded]
            if normalize(db) not in normalize(csv_a) and normalize(csv_a) not in normalize(db):
                mismatches.append({'code': padded, 'db': db, 'csv': csv_a})
    
    print(f"{len(mismatches)} potential mismatches to check")
    
    # Claude check
    client = anthropic.Anthropic()
    
    prompt = """Look at these Dutch address pairs. For each one, just tell me: are they the SAME physical location?

Typos, abbreviations, and spelling variations = SAME (e.g. "Gorinchem" vs "Gorichem", "F.Erensstraat" vs "Frans Erensstraat")
Different street names = DIFFERENT (e.g. "Industriestraat" vs "Donze Visserstraat")

Return a JSON object: {"different": ["code1", "code2", ...]} with ONLY the codes that are truly DIFFERENT locations.

Pairs:
"""
    
    pairs = "\n".join([f'{m["code"]}: "{m["db"]}" vs "{m["csv"]}"' for m in mismatches])
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt + pairs}]
    )
    
    # Parse response
    text = response.content[0].text
    # Extract JSON from response
    import re
    json_match = re.search(r'\{[^}]+\}', text, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group())
        diff_codes = data.get('different', [])
    else:
        diff_codes = []
    
    print(f"Different: {len(diff_codes)}")
    
    # Write report
    with open(REPORT_PATH, 'w') as f:
        f.write('# TRUE Mismatches (Claude Verified)\n\n')
        f.write(f'**{len(diff_codes)} entries** with actually different addresses:\n\n')
        f.write('| Code | Database | Exact |\n|------|----------|-------|\n')
        for c in sorted(diff_codes, key=lambda x: int(x) if x.isdigit() else 9999):
            m = next((x for x in mismatches if x['code'] == c), None)
            if m:
                f.write(f"| {c} | {m['db'][:45]} | {m['csv'][:45]} |\n")
    
    print(f"Saved to {REPORT_PATH}")

if __name__ == "__main__":
    main()
