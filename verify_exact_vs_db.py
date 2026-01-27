#!/usr/bin/env python3
"""
Full comparison of Exact kostenplaatsen with database using GPT-5.2.
Checks ALL entries to ensure kostenplaatsen match for financial accuracy.
"""
import openpyxl
import sqlite3
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
XLSX = PROJECT_ROOT / "1-CoHousingNL_B.V.-26-01-2026-HRMCostCenters.xlsx"
DB = PROJECT_ROOT / "database" / "ryanrent_v2.db"
OUTPUT = PROJECT_ROOT / "Shared/Sources/csv_data/correcting_kpls/exact_db_comparison_full.csv"

def main():
    # Load Exact data
    print("=== Loading Exact export ===")
    wb = openpyxl.load_workbook(XLSX)
    ws = wb.active
    
    exact_data = {}
    for row in ws.iter_rows(min_row=8, values_only=True):
        code = str(row[0]).strip() if row[0] else None
        desc = str(row[1]).strip() if row[1] else None
        if code and desc and code not in ['000', '0000', '00000']:
            # Pad code to 4 digits if numeric
            if code.isdigit():
                code = code.zfill(4)
            exact_data[code] = desc
    
    print(f"Loaded {len(exact_data)} kostenplaatsen from Exact")
    
    # Load Database
    print("\n=== Loading database ===")
    conn = sqlite3.connect(DB)
    db_data = {}
    for row in conn.execute('SELECT object_id, adres, plaats FROM huizen'):
        addr = f"{row[1]} {row[2] or ''}".strip()
        db_data[row[0]] = addr
    conn.close()
    
    print(f"Loaded {len(db_data)} huizen from database")
    
    # Compare using GPT-5.2 in batches
    print("\n=== Comparing with GPT-5.2 ===")
    client = OpenAI()
    
    all_mismatches = []
    all_missing_in_db = []
    all_missing_in_exact = []
    match_count = 0
    
    # Process in batches of 100
    exact_items = list(exact_data.items())
    batch_size = 100
    
    for i in range(0, len(exact_items), batch_size):
        batch = dict(exact_items[i:i+batch_size])
        batch_db = {k: db_data.get(k, "NOT_IN_DB") for k in batch.keys()}
        
        prompt = f"""Compare these kostenplaatsen from Exact with our database.
Goal: Verify that the CODE (object_id) points to the SAME property in both systems.

Rules for matching:
- Minor formatting differences (commas, case, spacing) = MATCH
- Abbreviations (St. vs Sint, Str. vs Straat) = MATCH  
- Typos in city/street names = MISMATCH (report it)
- Different house numbers or additions (108 vs 108B) = MISMATCH (critical!)
- NOT_IN_DB = property missing from database

EXACT DATA (Code: Address):
{json.dumps(batch, indent=2, ensure_ascii=False)}

DATABASE DATA (Code: Address):
{json.dumps(batch_db, indent=2, ensure_ascii=False)}

Return JSON:
{{
  "matches": <count of matching entries>,
  "mismatches": [
    {{"code": "XXXX", "exact": "...", "db": "...", "issue": "brief description"}}
  ],
  "missing_in_db": ["list of codes not in database"]
}}
"""
        
        print(f"Processing batch {i//batch_size + 1}/{(len(exact_items) + batch_size - 1)//batch_size}...")
        
        resp = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_completion_tokens=8192,
            temperature=0
        )
        
        result = json.loads(resp.choices[0].message.content)
        match_count += result.get("matches", 0)
        all_mismatches.extend(result.get("mismatches", []))
        all_missing_in_db.extend(result.get("missing_in_db", []))
    
    # Check for entries in DB but not in Exact
    for db_code in db_data.keys():
        if db_code not in exact_data and not db_code.startswith("A-"):
            all_missing_in_exact.append(db_code)
    
    # Print results
    print("\n" + "="*60)
    print("FULL COMPARISON RESULTS")
    print("="*60)
    print(f"\nTotal Exact entries: {len(exact_data)}")
    print(f"Total DB entries: {len(db_data)}")
    print(f"\n✅ MATCHES: {match_count}")
    print(f"❌ MISMATCHES: {len(all_mismatches)}")
    print(f"⚠️  Missing in DB: {len(all_missing_in_db)}")
    print(f"⚠️  Missing in Exact: {len(all_missing_in_exact)}")
    
    if all_mismatches:
        print("\n--- MISMATCHES (require attention) ---")
        for m in all_mismatches:
            print(f"\n{m['code']}:")
            print(f"  Exact: {m['exact']}")
            print(f"  DB:    {m['db']}")
            print(f"  Issue: {m['issue']}")
    
    if all_missing_in_db:
        print(f"\n--- MISSING IN DATABASE ({len(all_missing_in_db)}) ---")
        for code in all_missing_in_db[:20]:
            print(f"  {code}: {exact_data.get(code, 'N/A')}")
        if len(all_missing_in_db) > 20:
            print(f"  ... and {len(all_missing_in_db) - 20} more")
    
    # Save full report to CSV
    import csv
    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Type', 'Code', 'Exact', 'Database', 'Issue'])
        for m in all_mismatches:
            writer.writerow(['MISMATCH', m['code'], m['exact'], m['db'], m['issue']])
        for code in all_missing_in_db:
            writer.writerow(['MISSING_IN_DB', code, exact_data.get(code, ''), '', 'Not in database'])
        for code in all_missing_in_exact:
            writer.writerow(['MISSING_IN_EXACT', code, '', db_data.get(code, ''), 'Not in Exact'])
    
    print(f"\n📄 Full report saved to: {OUTPUT}")

if __name__ == "__main__":
    main()
