#!/usr/bin/env python3
"""
Regenerate exact_corrections_needed.md using only TRUE mismatches from LLM verification.
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
REPORT_PATH = PROJECT_ROOT / "exact_corrections_needed.md"

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
    
    # Find mismatches
    mismatches = []
    db_only = []
    
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
        else:
            db_only.append({'object_id': padded_id, 'db_addr': db_addr})
    
    print(f"Found {len(mismatches)} potential mismatches")
    print(f"Found {len(db_only)} DB-only entries")
    
    # LLM verify to filter TRUE mismatches
    client = OpenAI()
    
    PROMPT = """For each pair, determine if they refer to the SAME physical property (just spelling/formatting differences) or DIFFERENT properties.
Return JSON: {"results": [{"id": "XXXX", "same": true/false}]}

Rules:
- Minor spelling OK: "Gorinchem" = "Gorichem", "straat" = "str"  
- Case/punctuation/spacing OK
- House number + suffix MUST match: "106" ≠ "108", "33" ≠ "33c"
- Different street names = DIFFERENT property

Pairs:
"""
    
    true_mismatches = []
    batch_size = 40
    
    for i in range(0, len(mismatches), batch_size):
        batch = mismatches[i:i+batch_size]
        pairs = "\n".join([f"{m['object_id']}. '{m['db_addr'][:50]}' vs '{m['csv_addr'][:50]}'" for m in batch])
        
        print(f"Verifying batch {i//batch_size + 1}...")
        
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
                obj_id = str(r.get('id', ''))
                if not r.get('same', False):
                    item = next((m for m in batch if m['object_id'] == obj_id), None)
                    if item:
                        true_mismatches.append(item)
                        
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\n✅ TRUE mismatches only: {len(true_mismatches)}")
    
    # Generate report
    report = []
    report.append("# Exact Kostenplaatsen Corrections Needed (LLM Verified)")
    report.append(f"\n**Generated:** 2026-01-23 11:08")
    report.append(f"\n**Action:** Update these entries in Exact to match the database")
    report.append("\n> [!IMPORTANT]")
    report.append("> Only TRUE mismatches are listed. Spelling-only differences have been filtered out.")
    report.append("\n---")
    
    report.append(f"\n## ⚠️ Change These Codes in Exact ({len(true_mismatches)})")
    report.append("\nThese are **DIFFERENT properties** - the address in Exact is wrong:")
    report.append("\n| Code | Currently in Exact | Change To (from DB) |")
    report.append("|------|-------------------|---------------------|")
    for m in sorted(true_mismatches, key=lambda x: int(x['object_id']) if x['object_id'].isdigit() else 9999):
        report.append(f"| {m['object_id']} | {m['csv_addr'][:40]} | **{m['db_addr'][:40]}** |")
    
    report.append(f"\n## ➕ Add These Codes to Exact ({len(db_only)})")
    report.append("\nThese properties exist in your database but NOT in Exact:")
    report.append("\n| Code | Address |")
    report.append("|------|---------|")
    for item in sorted(db_only, key=lambda x: int(x['object_id']) if x['object_id'].isdigit() else 9999):
        report.append(f"| {item['object_id']} | {item['db_addr']} |")
    
    report.append("\n---")
    report.append(f"\n## Summary")
    report.append(f"- **Fix in Exact:** {len(true_mismatches)} entries (TRUE mismatches only)")
    report.append(f"- **Add to Exact:** {len(db_only)} entries")
    
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"\nReport saved to: {REPORT_PATH}")

if __name__ == "__main__":
    main()
