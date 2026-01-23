#!/usr/bin/env python3
"""
LLM-based address matcher for archived_huizen
Uses GPT-4o-mini to match unmatched addresses to A-codes from Exact CSV
"""
import csv
import sqlite3
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

DB_V2_PATH = PROJECT_ROOT / "database" / "ryanrent_v2.db"
CSV_PATH = PROJECT_ROOT / "Shared/Sources/csv_data/1-CoHousingNL_B.V.-23-01-2026-HRMCostCenters.csv"

def main():
    # Load A-codes from CSV
    a_codes = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            code = row['Code'].strip()
            if code.startswith('A-'):
                desc = row['Omschrijving'].strip()
                a_codes.append({'code': code, 'address': desc})
    
    print(f"Loaded {len(a_codes)} A-codes from CSV")
    
    # Get unmatched archived houses
    conn = sqlite3.connect(DB_V2_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, adres, plaats FROM archived_huizen WHERE object_id IS NULL")
    unmatched = [{'id': r[0], 'address': f"{r[1]} {r[2] or ''}".strip()} for r in cursor.fetchall()]
    
    print(f"Found {len(unmatched)} unmatched archived houses\n")
    
    if not unmatched:
        print("All houses already matched!")
        return
    
    # LLM matching
    client = OpenAI()
    
    # Build A-code list for prompt
    a_code_list = "\n".join([f"{a['code']}: {a['address']}" for a in a_codes])
    
    PROMPT = f"""Match these Dutch property addresses to the correct A-code from the list below.
Return JSON: {{"matches": [{{"db_id": N, "a_code": "A-XXXXX" or null if no match}}]}}

Rules:
- Match by street name and number (ignore minor spelling differences)
- "straat" = "str" = "strt", "laan" = "ln", etc.
- "33c" = "33C" = "33 c" (case/space insensitive)
- Return null if no confident match

A-CODES AVAILABLE:
{a_code_list}

ADDRESSES TO MATCH:
"""
    
    batch_size = 30
    total_matched = 0
    
    for i in range(0, len(unmatched), batch_size):
        batch = unmatched[i:i+batch_size]
        addresses = "\n".join([f"{v['id']}. {v['address']}" for v in batch])
        
        print(f"Processing batch {i//batch_size + 1}...")
        
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": PROMPT + addresses}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            data = json.loads(resp.choices[0].message.content)
            matches = data.get('matches', [])
            
            for m in matches:
                db_id = m.get('db_id')
                a_code = m.get('a_code')
                if db_id and a_code:
                    cursor.execute("UPDATE archived_huizen SET object_id = ? WHERE id = ?", 
                                 (a_code, db_id))
                    total_matched += 1
                    # Find address for logging
                    addr = next((v['address'] for v in batch if v['id'] == db_id), '?')
                    print(f"  ✅ [{db_id}] {addr[:40]} → {a_code}")
            
            conn.commit()
            
        except Exception as e:
            print(f"  Error in batch: {e}")
    
    conn.close()
    
    print(f"\n✅ Total newly matched: {total_matched}")
    print(f"❌ Remaining unmatched: {len(unmatched) - total_matched}")

if __name__ == "__main__":
    main()
