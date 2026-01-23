#!/usr/bin/env python3
"""
STRICT LLM verification - focus ONLY on house number differences.
Spelling/city variations should be ignored.
"""
import csv
import sqlite3
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

DB_V2_PATH = PROJECT_ROOT / "database" / "ryanrent_v2.db"
CSV_PATH = PROJECT_ROOT / "Shared/Sources/csv_data/1-CoHousingNL_B.V.-23-01-2026-HRMCostCenters.csv"
REPORT_PATH = PROJECT_ROOT / "kostenplaatsen_TRUE_mismatches.md"

def normalize_address(addr: str) -> str:
    if not addr:
        return ""
    return addr.lower().replace(",", "").replace("'s-", "s-").replace("'s ", "s ").strip()

def main():
    # Load CSV
    csv_data = {}
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            code = row['Code'].strip()
            csv_data[code] = row['Omschrijving'].strip()
    
    # Load DB huizen
    conn = sqlite3.connect(DB_V2_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT object_id, adres, plaats FROM huizen ORDER BY CAST(object_id AS INTEGER)")
    db_data = {row[0]: f"{row[1]} {row[2] or ''}".strip() for row in cursor.fetchall()}
    conn.close()
    
    # Find potential mismatches
    mismatches = []
    for obj_id, db_addr in db_data.items():
        padded_id = obj_id.zfill(4)
        if padded_id in csv_data:
            csv_addr = csv_data[padded_id]
            norm_db = normalize_address(db_addr)
            norm_csv = normalize_address(csv_addr)
            if not (norm_db in norm_csv or norm_csv in norm_db):
                mismatches.append({
                    'object_id': padded_id,
                    'db_addr': db_addr,
                    'csv_addr': csv_addr
                })
    
    print(f"Found {len(mismatches)} potential mismatches to verify\n")
    
    # STRICT LLM verify
    client = OpenAI()
    
    PROMPT = """You are comparing Dutch property addresses. For EACH pair, answer: is the HOUSE NUMBER AND SUFFIX different?

Rules:
- IGNORE all spelling differences in street names (Gorinchem=Gorichem, straat=str, etc.)
- IGNORE all spelling differences in city names
- IGNORE punctuation, spacing, capitalization
- ONLY flag as "different" if the HOUSE NUMBER or LETTER SUFFIX is different:
  * "106" vs "108" = DIFFERENT
  * "33" vs "33c" = DIFFERENT  
  * "139" vs "19" = DIFFERENT
  * "Gorinchem" vs "Gorichem" = SAME (just spelling)
  * "Westfrankelandsestraat" vs "Westfrankelandsestr" = SAME (abbreviation)

Return JSON: {"results": [{"id": "XXXX", "different_number": true/false}]}

Pairs to check:
"""
    
    true_mismatches = []
    spelling_only = []
    batch_size = 40
    
    for i in range(0, len(mismatches), batch_size):
        batch = mismatches[i:i+batch_size]
        pairs = "\n".join([f"{m['object_id']}. DB: '{m['db_addr']}' | CSV: '{m['csv_addr']}'" for m in batch])
        
        print(f"Verifying batch {i//batch_size + 1}...")
        
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": PROMPT + pairs}],
                response_format={"type": "json_object"},
                temperature=0
            )
            
            data = json.loads(resp.choices[0].message.content)
            results = data.get('results', [])
            
            for r in results:
                obj_id = str(r.get('id', ''))
                is_diff = r.get('different_number', False)
                item = next((m for m in batch if m['object_id'] == obj_id), None)
                if item:
                    if is_diff:
                        true_mismatches.append(item)
                    else:
                        spelling_only.append(item)
                        
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\n✅ Spelling only (SAME property): {len(spelling_only)}")
    print(f"❌ DIFFERENT house numbers: {len(true_mismatches)}")
    
    # Show true mismatches
    if true_mismatches:
        print("\nTRUE mismatches (different house number):")
        for m in true_mismatches[:15]:
            print(f"  {m['object_id']}: '{m['db_addr'][:35]}' vs '{m['csv_addr'][:35]}'")
    
    # Generate report
    report = []
    report.append("# Kostenplaatsen - TRUE Mismatches (House Number Different)")
    report.append(f"\n**Generated:** 2026-01-23 11:23")
    report.append(f"\n## Summary")
    report.append(f"- ✅ Spelling only (same property): **{len(spelling_only)}**")
    report.append(f"- ❌ Different house numbers: **{len(true_mismatches)}**")
    
    if true_mismatches:
        report.append(f"\n## ❌ TRUE Mismatches ({len(true_mismatches)})")
        report.append("\nThese have **different house numbers** - need correction in Exact:")
        report.append("\n| Code | Database Address | Exact CSV Address |")
        report.append("|------|------------------|-------------------|")
        for m in sorted(true_mismatches, key=lambda x: int(x['object_id']) if x['object_id'].isdigit() else 9999):
            report.append(f"| {m['object_id']} | {m['db_addr']} | {m['csv_addr']} |")
    
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"\nReport saved to: {REPORT_PATH}")

if __name__ == "__main__":
    main()
