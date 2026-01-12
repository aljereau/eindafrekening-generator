#!/usr/bin/env python3
"""
Clean up Tradiro-imported house addresses by splitting out the plaats (city).
Uses Claude API for parsing irregular address formats.
"""

import sqlite3
import json
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

DB_PATH = "database/ryanrent_mock.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get houses that need cleaning (0399+)
    cursor.execute("""
        SELECT object_id, adres FROM huizen 
        WHERE CAST(object_id AS INTEGER) >= 399 
        AND object_id NOT LIKE 'A-%'
        AND (plaats IS NULL OR plaats = '')
        ORDER BY object_id
    """)
    houses = [(r['object_id'], r['adres']) for r in cursor.fetchall()]
    
    if not houses:
        print("No houses need cleaning")
        return
    
    print(f"📍 Found {len(houses)} houses to clean")
    
    # Build prompt for Claude
    addresses_list = "\n".join([f"{obj_id}: {addr}" for obj_id, addr in houses])
    
    prompt = f"""Parse these Dutch addresses and extract the city (plaats) from each.

The format is typically: "Street Number, City" or "Street Number City"
Some edge cases:
- "Homeflex Park Honselersdijk" -> plaats: Honselersdijk
- "Messchaertplein 36 Bovenwoning, Vlaardingen" -> plaats: Vlaardingen (Bovenwoning is part of address)
- "'s-gravenzande" is a city name

Addresses to parse:
{addresses_list}

Return a JSON object mapping object_id to an object with "adres" (clean street+number only) and "plaats" (city only).
Example: {{"0399": {{"adres": "Maasdijk 67", "plaats": "'s-Gravenzande"}}}}
ONLY return valid JSON, no other text.
"""

    client = anthropic.Anthropic()
    print("🤖 Calling Claude to parse addresses...")
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = message.content[0].text.strip()
    
    # Parse JSON
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    
    parsed = json.loads(response_text)
    print(f"   ✓ Parsed {len(parsed)} addresses")
    
    # Update database
    updated = 0
    for obj_id, data in parsed.items():
        cursor.execute("""
            UPDATE huizen SET 
                adres = ?,
                plaats = ?,
                gewijzigd_op = CURRENT_TIMESTAMP
            WHERE object_id = ?
        """, (data['adres'], data['plaats'], obj_id))
        if cursor.rowcount > 0:
            updated += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Updated {updated} houses with clean addresses")


if __name__ == "__main__":
    main()
