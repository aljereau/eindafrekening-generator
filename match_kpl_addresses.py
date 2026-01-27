#!/usr/bin/env python3
"""
Use GPT-5.2 to match addresses that need kostenplaats to the source list.
Some addresses may be written differently (spelling variations, abbreviations).
"""
import csv
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

KPL_SOURCE = PROJECT_ROOT / "Shared/Sources/csv_data/correcting_kpls/kpls_adressen.csv"
ADDRESSES_NEEDING = PROJECT_ROOT / "Shared/Sources/csv_data/correcting_kpls/adressen needing kpl.csv"
OUTPUT = PROJECT_ROOT / "Shared/Sources/csv_data/correcting_kpls/matched_addresses.csv"

def main():
    # Load source (kostenplaatsen with object_id -> address)
    source = {}
    with open(KPL_SOURCE, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f, delimiter=';'):
            obj = row['OBJECT'].strip()
            addr = row['Straat en huisnummer'].strip()
            if obj and addr:
                source[obj] = addr
    
    # Load addresses needing kostenplaats
    needing = []
    with open(ADDRESSES_NEEDING, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            addr = row['Adres'].strip()
            if addr:
                needing.append(addr)
    
    print(f"Source addresses: {len(source)}")
    print(f"Addresses needing KPL: {len(needing)}")
    
    # Format source list for LLM
    source_list = "\n".join([f"{code}: {addr}" for code, addr in sorted(source.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 9999)])
    
    # Batch addresses for API call (avoid context limit)
    batch_size = 100
    all_results = []
    
    client = OpenAI()
    
    for i in range(0, len(needing), batch_size):
        batch = needing[i:i+batch_size]
        addresses_list = "\n".join([f"{j+1}. {addr}" for j, addr in enumerate(batch)])
        
        prompt = f"""Match each address in LIST B to the correct object_id from LIST A.
Addresses may have spelling variations, abbreviations, or formatting differences.
Examples of same address:
- "Akkerweg 41 [huis 14]" = "Akkerweg 41 [014]"
- "Kerkweg 9a [huis 137]" = "Kerkweg 9a [137]"
- "De Zwingel 8B" = "Zwingel 8B"
- "Desiree Geerartstraat 1B" = "Desiree Geeraertstraat 1 B"

Return JSON: {{"matches": [{{"address": "...", "object_id": "XXXX", "source_address": "..."}}]}}
If no match found, use object_id: "NOT_FOUND"

LIST A (Source with object_ids):
{source_list}

LIST B (Addresses to match):
{addresses_list}
"""
        
        print(f"Processing batch {i//batch_size + 1}...")
        
        resp = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_completion_tokens=8192,
            temperature=0
        )
        
        data = json.loads(resp.choices[0].message.content)
        all_results.extend(data.get("matches", []))
    
    # Write output CSV
    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Adres', 'Object_ID', 'Source_Adres', 'Status'])
        
        matched = 0
        not_found = 0
        
        for r in all_results:
            addr = r.get('address', '')
            obj_id = r.get('object_id', 'NOT_FOUND')
            src_addr = r.get('source_address', '')
            
            status = 'OK' if obj_id != 'NOT_FOUND' else 'NOT_FOUND'
            if obj_id != 'NOT_FOUND':
                matched += 1
            else:
                not_found += 1
            
            writer.writerow([addr, obj_id, src_addr, status])
    
    print(f"\n=== RESULTS ===")
    print(f"Matched: {matched}")
    print(f"Not found: {not_found}")
    print(f"Output written to: {OUTPUT}")

if __name__ == "__main__":
    main()
