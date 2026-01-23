#!/usr/bin/env python3
"""
Use GPT-5.2 for smart address matching between Exact CSV and database.
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
REPORT_PATH = PROJECT_ROOT / "exact_to_db_mapping.md"

def main():
    # Load DB
    conn = sqlite3.connect(DB_V2_PATH)
    db_list = [(r[0], f"{r[1]} {r[2] or ''}".strip()) for r in conn.execute("SELECT object_id, adres, plaats FROM huizen")]
    conn.close()
    
    db_text = "\n".join([f"{code}: {addr}" for code, addr in db_list])
    
    # Load Exact CSV
    exact_entries = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f, delimiter=';'):
            code = row['Code'].strip()
            addr = row['Omschrijving'].strip()
            if not code.startswith('A-') and code not in ['000', '0000', '00000']:
                exact_entries.append((code, addr))
    
    print(f"Matching {len(exact_entries)} Exact entries against {len(db_list)} DB entries")
    
    client = OpenAI()
    
    prompt = f"""Match each Exact address to the correct database entry. 
ONLY match if it's the EXACT SAME physical property (street + number + suffix must match).
"Boswoning 45" ≠ "Boswoning 11" - different units!
"Papsouwselaan 52" ≠ "Papsouwselaan 30" - different numbers!

Return JSON: {{"matches": [{{"exact_code": "X", "db_code": "Y" or null if not found}}]}}

DATABASE ENTRIES:
{db_text}

EXACT ENTRIES TO MATCH:
"""
    
    results = []
    batch_size = 50
    
    for i in range(0, len(exact_entries), batch_size):
        batch = exact_entries[i:i+batch_size]
        batch_text = "\n".join([f"{code}: {addr}" for code, addr in batch])
        
        print(f"Batch {i//batch_size + 1}...")
        
        try:
            resp = client.chat.completions.create(
                model="gpt-5.2",
                messages=[{"role": "user", "content": prompt + batch_text}],
                response_format={"type": "json_object"},
                max_completion_tokens=4096,
                temperature=0
            )
            
            data = json.loads(resp.choices[0].message.content)
            for m in data.get('matches', []):
                results.append((m.get('exact_code'), m.get('db_code')))
                
        except Exception as e:
            print(f"  Error: {e}")
    
    # Generate report
    exact_dict = {code: addr for code, addr in exact_entries}
    db_dict = dict(db_list)
    
    lines = ['# Exact → Database Mapping (GPT-5.2)', '', '| Exact Code | Exact Address | DB Code | DB Address |', '|------------|---------------|---------|------------|']
    
    needs_change = []
    not_found = []
    
    for exact_code, db_code in results:
        exact_addr = exact_dict.get(exact_code, '')
        if db_code and db_code != exact_code:
            db_addr = db_dict.get(db_code, '')
            lines.append(f'| {exact_code} | {exact_addr[:40]} | **{db_code}** | {db_addr[:35]} |')
            needs_change.append((exact_code, db_code))
        elif not db_code:
            not_found.append((exact_code, exact_addr))
    
    lines.append('')
    lines.append(f'## Not Found in Database ({len(not_found)})')
    lines.append('')
    lines.append('| Exact Code | Exact Address |')
    lines.append('|------------|---------------|')
    for code, addr in not_found[:100]:
        lines.append(f'| {code} | {addr} |')
    
    with open(REPORT_PATH, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"\nSaved to {REPORT_PATH}")
    print(f"Entries needing code change: {len(needs_change)}")
    print(f"Not found in DB: {len(not_found)}")

if __name__ == "__main__":
    main()
