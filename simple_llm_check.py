#!/usr/bin/env python3
"""
Simple LLM address comparison - let it think naturally.
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
    cursor = conn.cursor()
    cursor.execute("SELECT object_id, adres, plaats FROM huizen")
    db_data = {r[0]: f"{r[1]} {r[2] or ''}".strip() for r in cursor.fetchall()}
    conn.close()
    
    # Find potential mismatches
    mismatches = []
    for obj_id, db_addr in db_data.items():
        padded = obj_id.zfill(4) if obj_id.isdigit() or obj_id.startswith('0') else obj_id
        if padded in csv_data:
            csv_addr = csv_data[padded]
            if normalize(db_addr) not in normalize(csv_addr) and normalize(csv_addr) not in normalize(db_addr):
                mismatches.append({'code': padded, 'db': db_addr, 'csv': csv_addr})
    
    print(f"Found {len(mismatches)} potential mismatches\n")
    
    # Simple LLM check
    client = OpenAI()
    
    PROMPT = """Are these the same physical property? Just use common sense.
- "Visartstraat 31" vs "Visstraat 31" = probably same (typo)
- "F.Erensstraat 21" vs "Frans Erensstraat 21" = same (abbreviation)
- "Industriestraat 9 Dongen" vs "Donze Visserstraat 13 Terneuzen" = obviously different

Return JSON: {"results": [{"code": "XXXX", "same": true/false}]}

"""
    
    true_mismatches = []
    batch_size = 50
    
    for i in range(0, len(mismatches), batch_size):
        batch = mismatches[i:i+batch_size]
        pairs = "\n".join([f"{m['code']}: \"{m['db']}\" vs \"{m['csv']}\"" for m in batch])
        
        print(f"Batch {i//batch_size + 1}...")
        
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": PROMPT + pairs}],
                response_format={"type": "json_object"},
                temperature=0
            )
            
            data = json.loads(resp.choices[0].message.content)
            for r in data.get('results', []):
                if not r.get('same', True):
                    item = next((m for m in batch if m['code'] == str(r.get('code'))), None)
                    if item:
                        true_mismatches.append(item)
                        
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\n❌ TRUE mismatches: {len(true_mismatches)}")
    
    # Generate report
    lines = [
        '# Kostenplaatsen - TRUE Mismatches',
        '',
        f'**{len(true_mismatches)} entries** with actually different addresses:',
        '',
        '| Code | Database | Exact CSV |',
        '|------|----------|-----------|'
    ]
    for m in sorted(true_mismatches, key=lambda x: int(x['code']) if x['code'].isdigit() else 9999):
        lines.append(f"| {m['code']} | {m['db'][:45]} | {m['csv'][:45]} |")
    
    with open(REPORT_PATH, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"Saved to {REPORT_PATH}")

if __name__ == "__main__":
    main()
