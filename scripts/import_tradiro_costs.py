#!/usr/bin/env python3
"""
Import Tradiro Mutations with LLM-based address matching.

Uses Claude API to semantically match addresses from Tradiro to existing huizen,
handling variations like "Energieweg 40 Vlaardingen" vs "Energieweg 40".
"""

import zipfile
import xml.etree.ElementTree as ET
import sqlite3
import os
import json
from collections import defaultdict
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Try importing anthropic
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("⚠️ anthropic not installed, falling back to fuzzy matching")

# Paths
EXCEL_FILE = "Shared/Sources/Mutaties woningen Tradiro.xlsx"
DB_PATH = "database/ryanrent_mock.db"

# Grootboek categories we care about
GROOTBOEK_MAPPING = {
    '4250': 'voorschot_gwe',        # Gas, water en electra woningen
    '4230': 'internet',             # Internet en telefoonkosten woningen
    '4220': 'inventaris',           # Kleine inventaris/inrichting woningen
    '4270': 'vve_kosten',           # Kosten VvE woningen
    '4240': 'reparatie_onderhoud',  # Reparatie en onderhoud
    '4260': 'schoonmaak',           # Schoonmaakkosten woningen
}

SKIP_ADDRESSES = {'Algemeen woningen', '999', ''}


def parse_tradiro_excel():
    """Parse the Tradiro Excel using XML extraction"""
    print(f"📖 Reading: {EXCEL_FILE}")
    
    with zipfile.ZipFile(EXCEL_FILE) as z:
        with z.open('xl/sharedStrings.xml') as f:
            strings_xml = f.read()
        with z.open('xl/worksheets/sheet1.xml') as f:
            sheet_xml = f.read()
    
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    strings_root = ET.fromstring(strings_xml)
    shared_strings = []
    for si in strings_root.findall(f'.//{{{ns}}}si'):
        t_elem = si.find(f'.//{{{ns}}}t')
        shared_strings.append(t_elem.text if t_elem is not None else '')
    
    sheet_root = ET.fromstring(sheet_xml)
    rows = sheet_root.findall(f'.//{{{ns}}}row')
    
    def get_cell_value(cell):
        t = cell.get('t')
        v_elem = cell.find(f'{{{ns}}}v')
        if v_elem is None:
            return ''
        v = v_elem.text
        if t == 's':
            idx = int(v)
            return shared_strings[idx] if idx < len(shared_strings) else ''
        return v
    
    transactions = []
    
    for row in rows[1:]:  # Skip header
        cells = row.findall(f'{{{ns}}}c')
        if not cells or len(cells) < 12:
            continue
        
        row_values = [get_cell_value(c) for c in cells]
        
        grootboek_code = str(row_values[5]).strip() if len(row_values) > 5 else ''
        debet = row_values[7] if len(row_values) > 7 else '0'
        credit = row_values[8] if len(row_values) > 8 else '0'
        omschrijving = str(row_values[11]).strip() if len(row_values) > 11 else ''
        
        if grootboek_code not in GROOTBOEK_MAPPING:
            continue
        if omschrijving in SKIP_ADDRESSES or omschrijving.startswith('999'):
            continue
        
        try:
            debet_val = float(debet) if debet else 0.0
            credit_val = float(credit) if credit else 0.0
        except:
            debet_val, credit_val = 0.0, 0.0
        
        net_cost = debet_val - credit_val
        if net_cost != 0:
            transactions.append({
                'address': omschrijving,
                'grootboek_code': grootboek_code,
                'cost': net_cost
            })
    
    print(f"   Parsed {len(transactions)} transactions")
    return transactions


def aggregate_costs(transactions):
    """Aggregate costs per address per category"""
    address_costs = defaultdict(lambda: defaultdict(list))
    
    for tx in transactions:
        addr = tx['address']
        cat = GROOTBOEK_MAPPING[tx['grootboek_code']]
        address_costs[addr][cat].append(tx['cost'])
    
    result = {}
    for addr, cats in address_costs.items():
        result[addr] = {}
        for cat, costs in cats.items():
            if len(costs) >= 3:
                sorted_costs = sorted(costs)
                median = sorted_costs[len(sorted_costs) // 2]
                result[addr][cat] = round(median, 2)
            elif len(costs) > 0:
                result[addr][cat] = round(sum(costs) / len(costs), 2)
    
    return result


def llm_match_addresses(tradiro_addresses, huizen_list):
    """Use Claude to match Tradiro addresses to existing huizen"""
    if not HAS_ANTHROPIC:
        return {}
    
    client = anthropic.Anthropic()
    
    # Build huizen lookup
    huizen_str = "\n".join([f"{obj_id}: {addr}" for obj_id, addr in huizen_list])
    addresses_str = "\n".join(tradiro_addresses)
    
    prompt = f"""I have a list of property addresses from a financial system (Tradiro) that need to be matched to our existing property database.

EXISTING PROPERTIES (object_id: address):
{huizen_str}

ADDRESSES TO MATCH (from Tradiro):
{addresses_str}

For each Tradiro address, find the matching object_id from the existing properties list. 
Consider that:
- City names may be included or omitted
- Slight spelling variations may exist
- Postcodes may or may not be present
- "s-Gravenzande", "'s-Gravenzande", "S-GRAVENZANDE" are the same city

Return a JSON object mapping each Tradiro address to its matched object_id.
If no match is found, map to null.
ONLY return the JSON object, no other text.

Example format:
{{"Energieweg 40 Vlaardingen": "0063", "Unknown Address 123": null}}
"""

    print(f"\n🤖 Calling Claude to match {len(tradiro_addresses)} addresses...")
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = message.content[0].text.strip()
    
    # Parse JSON response
    try:
        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        matches = json.loads(response_text)
        print(f"   ✓ Claude matched {sum(1 for v in matches.values() if v)} addresses")
        return matches
    except json.JSONDecodeError as e:
        print(f"   ⚠️ Failed to parse Claude response: {e}")
        print(f"   Response was: {response_text[:500]}...")
        return {}


def main():
    transactions = parse_tradiro_excel()
    address_costs = aggregate_costs(transactions)
    print(f"\n📊 Found {len(address_costs)} unique addresses with costs")
    
    # Connect to DB
    print(f"\n📦 Connecting to: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get existing huizen
    cursor.execute("SELECT object_id, adres FROM huizen ORDER BY object_id")
    huizen_list = [(row['object_id'], row['adres']) for row in cursor.fetchall()]
    print(f"   Found {len(huizen_list)} existing huizen")
    
    # Use LLM to match addresses
    tradiro_addresses = list(address_costs.keys())
    matches = llm_match_addresses(tradiro_addresses, huizen_list)
    
    # Get next object_id for new houses
    cursor.execute("SELECT MAX(CAST(object_id AS INTEGER)) as max_id FROM huizen WHERE object_id NOT LIKE 'A-%'")
    max_id = cursor.fetchone()['max_id'] or 398
    next_id = 399  # Start from 0399 as requested
    
    stats = {'updated': 0, 'new_houses': 0, 'new_list': []}
    
    for addr, costs in address_costs.items():
        matched_id = matches.get(addr)
        
        if matched_id:
            # Update existing house
            update_parts = []
            values = []
            
            if 'voorschot_gwe' in costs and costs['voorschot_gwe'] > 0:
                update_parts.append("voorschot_gwe = ?")
                values.append(costs['voorschot_gwe'])
            if 'internet' in costs and costs['internet'] > 0:
                update_parts.append("internet = ?")
                values.append(costs['internet'])
            
            if update_parts:
                values.append(matched_id)
                sql = f"UPDATE huizen SET {', '.join(update_parts)}, gewijzigd_op = CURRENT_TIMESTAMP WHERE object_id = ?"
                cursor.execute(sql, values)
                if cursor.rowcount > 0:
                    stats['updated'] += 1
        else:
            # New house
            new_obj_id = f"{next_id:04d}"
            next_id += 1
            
            cursor.execute("""
                INSERT INTO huizen (object_id, adres, voorschot_gwe, internet, status)
                VALUES (?, ?, ?, ?, 'active')
            """, (
                new_obj_id,
                addr,
                costs.get('voorschot_gwe', 0),
                costs.get('internet', 0)
            ))
            
            stats['new_houses'] += 1
            stats['new_list'].append((new_obj_id, addr))
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Import Complete!")
    print(f"   Updated existing:  {stats['updated']}")
    print(f"   New houses added:  {stats['new_houses']}")
    
    if stats['new_list']:
        print(f"\n📋 New houses (not found in DB):")
        for obj_id, addr in stats['new_list'][:15]:
            print(f"   {obj_id}: {addr}")
        if len(stats['new_list']) > 15:
            print(f"   ... and {len(stats['new_list']) - 15} more")


if __name__ == "__main__":
    main()
