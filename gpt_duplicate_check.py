#!/usr/bin/env python3
"""
Use GPT-5.2 to find true duplicate addresses between ranges 0001-0397 and 0398-0492.
"""
import sqlite3
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

DB_PATH = PROJECT_ROOT / "database" / "ryanrent_v2.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    rows = list(conn.execute("SELECT object_id, adres, plaats FROM huizen WHERE object_id NOT LIKE 'A-%'"))
    conn.close()
    
    # Split into ranges
    range1 = []  # 0001-0397 (original)
    range2 = []  # 0398-0492 (new)
    
    for obj_id, adres, plaats in rows:
        try:
            num = int(obj_id)
            full = f"{adres} {plaats or ''}".strip()
            if 1 <= num <= 397:
                range1.append((obj_id, full))
            elif 398 <= num <= 492:
                range2.append((obj_id, full))
        except:
            pass
    
    print(f"Range 0001-0397: {len(range1)} entries")
    print(f"Range 0398-0492: {len(range2)} entries")
    print()
    
    # Prepare lists for GPT
    list1 = "\n".join([f"{code}: {addr}" for code, addr in range1])
    list2 = "\n".join([f"{code}: {addr}" for code, addr in range2])
    
    client = OpenAI()
    
    prompt = f"""Compare these two address lists. Find entries in LIST 2 that are DUPLICATES of entries in LIST 1.

DUPLICATE means: EXACT SAME physical property (same street, same house number, same suffix).
NOT duplicates: different house numbers (25 vs 26), different suffixes (A vs B).

Return JSON: {{"duplicates": [{{"id1": "XXXX", "addr1": "...", "id2": "XXXX", "addr2": "..."}}]}}

LIST 1 (Original 0001-0397):
{list1}

LIST 2 (New 0398-0492):
{list2}
"""
    
    print("Calling GPT-5.2...")
    
    resp = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_completion_tokens=4096,
        temperature=0
    )
    
    data = json.loads(resp.choices[0].message.content)
    duplicates = data.get("duplicates", [])
    
    print(f"\nTRUE DUPLICATES FOUND: {len(duplicates)}")
    print()
    print("| Original Code | Address | Duplicate Code | Address |")
    print("|---------------|---------|----------------|---------|")
    for d in duplicates:
        print(f"| {d['id1']} | {d['addr1'][:35]} | {d['id2']} | {d['addr2'][:35]} |")

if __name__ == "__main__":
    main()
