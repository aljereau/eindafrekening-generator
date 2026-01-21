#!/usr/bin/env python3
"""
LLM-based address matcher for Tradiro data
Verifies matches and reverts incorrect ones
"""

import csv
import sqlite3
import re
import json
import os
from pathlib import Path
from difflib import SequenceMatcher
from dotenv import load_dotenv
from openai import OpenAI

# Load environment
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

CSV_PATH = PROJECT_ROOT / "Shared/Sources/excel_data/tradirowoningen-data.csv"
DB_PATH = PROJECT_ROOT / "database/ryanrent_v2.db"

def normalize(s):
    if not s: return ""
    s = s.lower()
    s = re.sub(r"'s-|'", "", s)
    s = re.sub(r"[\-\.]", " ", s)
    s = re.sub(r"\s+", " ", s)
    cities = ['vlaardingen', 'schiedam', 'rotterdam', 'den haag', 'maassluis', 'delft', 
              'naaldwijk', 'rozenburg', 'terneuzen', 'steenbergen', 'pijnacker', 'hoofddorp',
              'honselersdijk', 'hoogvliet', 'maasdijk', 'de lier', 'gravenzande', 'biervliet',
              'sluiskil', 'moordrecht', 'kwintsheul', 'roosendaal', 'baarn', 'zwartewaal',
              'hoek van holland', 'nieuwerkerk aan den ijssel', 'spijkenisse']
    for city in cities:
        s = re.sub(rf'\s*{city}\s*$', '', s)
    return s.strip()

def score(t, d):
    return SequenceMatcher(None, normalize(t), normalize(d)).ratio()

def main():
    # Read CSV
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        tradiro_data = list(csv.DictReader(f, delimiter=';'))
    
    # Connect to DB
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    db_houses = list(conn.execute("SELECT id, object_id, adres, plaats, capaciteit_personen FROM huizen"))
    
    # Build matches
    all_matches = []
    for row in tradiro_data:
        adres = row.get('Adres', '').strip()
        plaats = row.get('Plaats', '').strip()
        cap = row.get('Cap.', '').strip()
        if not adres or adres == 'Huis' or not cap:
            continue
        try:
            cap_int = int(cap)
            if cap_int > 50: continue
        except:
            continue
        
        scores = [(dict(db), score(adres, db['adres'])) for db in db_houses]
        scores.sort(key=lambda x: -x[1])
        best = scores[0]
        
        if best[1] >= 0.6:
            all_matches.append({
                'tradiro': adres, 'tradiro_plaats': plaats, 'tradiro_cap': cap_int,
                'db_match': best[0]['adres'], 'db_plaats': best[0]['plaats'] or '',
                'db_object_id': best[0]['object_id'], 'db_id': best[0]['id'], 
                'db_cap': best[0]['capaciteit_personen'], 'score': best[1]
            })
    
    print(f"📊 Total matches to verify: {len(all_matches)}")
    
    # LLM verify
    client = OpenAI()
    
    PROMPT = """Verify these Dutch address pairs are the SAME physical property.
Return JSON: {"results": [{"index": N, "match": true/false}]}
Rules: Street name AND number AND suffix must match. "33c" = "33C" but "33" ≠ "33c". Minor spelling OK.

"""
    
    batch_size = 40
    
    for i in range(0, len(all_matches), batch_size):
        batch = all_matches[i:i+batch_size]
        pairs = "\n".join([f"{j}. '{v['tradiro']}' vs '{v['db_match']}'" for j, v in enumerate(batch)])
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": PROMPT + pairs}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        data = json.loads(resp.choices[0].message.content)
        results = data.get('results', [])
        
        for r in results:
            idx = r.get('index', 0)
            if idx < len(batch):
                batch[idx]['verified'] = r.get('match', False)
        
        print(f"  Batch {i//batch_size + 1}: verified {len(batch)}")
    
    # Find incorrect
    incorrect = [v for v in all_matches if v.get('verified') == False]
    correct = [v for v in all_matches if v.get('verified') == True]
    
    print(f"\n✅ Correct matches: {len(correct)}")
    print(f"❌ Incorrect matches: {len(incorrect)}")
    
    # Revert incorrect
    reverted = 0
    for m in incorrect:
        conn.execute("UPDATE huizen SET capaciteit_personen = NULL WHERE id = ?", (m['db_id'],))
        reverted += 1
        print(f"  Reverted {m['db_object_id']}: '{m['tradiro'][:35]}' ≠ '{m['db_match'][:35]}'")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Reverted {reverted} incorrect capacity updates")

if __name__ == '__main__':
    main()
