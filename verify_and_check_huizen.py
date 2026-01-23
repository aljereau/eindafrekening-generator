#!/usr/bin/env python3
"""
1. Verify fuzzy-matched addresses using LLM
2. Check if unmatched archived addresses appear in huizen table
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

def normalize(addr):
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
    # Load A-codes
    a_codes = {}
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            code = row['Code'].strip()
            if code.startswith('A-'):
                a_codes[code] = row['Omschrijving'].strip()
    
    conn = sqlite3.connect(DB_V2_PATH)
    cursor = conn.cursor()
    
    print("="*60)
    print("PART 1: Verify fuzzy-matched addresses with LLM")
    print("="*60)
    
    # Get matched archived houses
    cursor.execute("SELECT id, adres, plaats, object_id FROM archived_huizen WHERE object_id IS NOT NULL")
    matched = [{'id': r[0], 'db_addr': f"{r[1]} {r[2] or ''}".strip(), 'a_code': r[3]} for r in cursor.fetchall()]
    
    # Add CSV address
    to_verify = []
    for m in matched:
        if m['a_code'] in a_codes:
            m['csv_addr'] = a_codes[m['a_code']]
            to_verify.append(m)
    
    print(f"Verifying {len(to_verify)} matched addresses...\n")
    
    # LLM verify
    client = OpenAI()
    
    PROMPT = """Verify these Dutch address pairs are the SAME physical property.
Return JSON: {"results": [{"id": N, "match": true/false}]}
Rules: Street name AND number AND suffix must match. "33c" = "33C" OK. Minor spelling OK.

"""
    
    batch_size = 40
    incorrect = []
    
    for i in range(0, len(to_verify), batch_size):
        batch = to_verify[i:i+batch_size]
        pairs = "\n".join([f"{v['id']}. '{v['db_addr'][:50]}' vs '{v['csv_addr'][:50]}'" for v in batch])
        
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": PROMPT + pairs}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            data = json.loads(resp.choices[0].message.content)
            results = data.get('results', [])
            
            for r in results:
                if not r.get('match', True):
                    item = next((v for v in batch if v['id'] == r.get('id')), None)
                    if item:
                        incorrect.append(item)
            
            print(f"  Batch {i//batch_size + 1}: verified {len(batch)}")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\n✅ Correct matches: {len(to_verify) - len(incorrect)}")
    print(f"❌ Incorrect matches: {len(incorrect)}")
    
    if incorrect:
        print("\nIncorrect matches to fix:")
        for m in incorrect[:20]:
            print(f"  [{m['id']}] {m['a_code']}: '{m['db_addr'][:30]}' ≠ '{m['csv_addr'][:30]}'")
        
        # Clear incorrect matches
        for m in incorrect:
            cursor.execute("UPDATE archived_huizen SET object_id = NULL WHERE id = ?", (m['id'],))
        conn.commit()
        print(f"\n🔄 Cleared {len(incorrect)} incorrect matches")
    
    print("\n" + "="*60)
    print("PART 2: Check if unmatched addresses are in huizen table")
    print("="*60)
    
    # Get unmatched
    cursor.execute("SELECT id, adres, plaats FROM archived_huizen WHERE object_id IS NULL")
    unmatched = [{'id': r[0], 'addr': f"{r[1]} {r[2] or ''}".strip()} for r in cursor.fetchall()]
    
    # Get huizen
    cursor.execute("SELECT object_id, adres, plaats FROM huizen")
    huizen = [{'object_id': r[0], 'addr': f"{r[1]} {r[2] or ''}".strip()} for r in cursor.fetchall()]
    
    print(f"Checking {len(unmatched)} unmatched against {len(huizen)} huizen...\n")
    
    found_in_huizen = []
    for u in unmatched:
        norm_u = normalize(u['addr'])
        for h in huizen:
            norm_h = normalize(h['addr'])
            if norm_u in norm_h or norm_h in norm_u:
                found_in_huizen.append({
                    'archived_id': u['id'],
                    'archived_addr': u['addr'],
                    'huizen_object_id': h['object_id'],
                    'huizen_addr': h['addr']
                })
                break
    
    print(f"Found {len(found_in_huizen)} unmatched archived houses that exist in huizen table:\n")
    for f in found_in_huizen:
        print(f"  [{f['archived_id']}] {f['archived_addr'][:35]}")
        print(f"       → huizen {f['huizen_object_id']}: {f['huizen_addr'][:35]}")
        # Update with huizen object_id
        cursor.execute("UPDATE archived_huizen SET object_id = ? WHERE id = ?", 
                      (f['huizen_object_id'], f['archived_id']))
    
    conn.commit()
    print(f"\n✅ Updated {len(found_in_huizen)} archived houses with huizen object_ids")
    
    conn.close()

if __name__ == "__main__":
    main()
