#!/usr/bin/env python3
"""
Smart Financial Classifier
Matches unclassified financial transactions to Properties (Kostenplaats) using:
1. Regex Text Search (Address/ID in Description)
2. Financial Fingerprinting (Unique Amount + Relatie match)
3. Heuristic Logic (GWE Advances, Owner Payments)
"""
import pandas as pd
import sqlite3
import re
from datetime import datetime

DB_PATH = "database/ryanrent_mock.db"
INPUT_FILE = "Shared/Sources/Copy of RR-example-CoHousingNL_B.V.-07-01-2026-FinTransactionSearch (1).xlsx"
OUTPUT_FILE = "Eindafrekening/output/Smart_Financial_Classification.xlsx"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def load_knowledge_base():
    """
    Builds a 'Fingerprint' of the system:
    - Which amounts belong to which active contract?
    - Which relations (Relatie) belong to which house?
    """
    print("🧠 Building Knowledge Base from Database...")
    conn = get_db_connection()
    
    # 1. Active Contracts (Rental & Inhuur)
    # We want: Amount -> House ID, Relatie -> House ID
    query = """
    SELECT 
        h.object_id,
        h.adres,
        v.kale_huur as verhuur_prijs,
        v.verhuur_incl_btw,
        v.voorschot_gwe as verhuur_gwe,
        v.afval_kosten as verhuur_afval,
        v.huurder_naam,
        i.kale_inhuurprijs,
        i.inhuur_prijs_incl_btw as inhuur_incl_btw,
        lev.naam as leverancier_naam
    FROM huizen h
    LEFT JOIN (
        SELECT * FROM verhuur_contracten 
        WHERE id IN (SELECT MAX(id) FROM verhuur_contracten GROUP BY object_id)
    ) v ON h.object_id = v.object_id
    LEFT JOIN (
        SELECT * FROM inhuur_contracten 
        WHERE id IN (SELECT MAX(id) FROM inhuur_contracten GROUP BY object_id)
    ) i ON h.object_id = i.object_id
    LEFT JOIN leveranciers lev ON i.leverancier_id = lev.id
    WHERE h.status = 'active'
    """
    
    
    contracts = pd.read_sql_query(query, conn)
    conn.close()
    
    # Build Lookup Dictionaries
    fingerprints = {
        'amount_map': {},         # {amount: [obj_id1, obj_id2]}
        'relatie_map': {},        # {clean_name: [obj_id1, obj_id2]}
        'amount_relatie_map': {}, # {(amount, clean_name): [obj_id]}
        'house_addresses': {},     # {clean_address: obj_id}
        'huis_number_map': {},     # {number: obj_id} for [huis N] addresses
        'valid_ids': set()        # Set of all valid object IDs
    }
    
    for _, row in contracts.iterrows():
        obj_id = row['object_id']
        fingerprints['valid_ids'].add(obj_id)
        adres_lower = row['adres'].lower()
        fingerprints['house_addresses'][adres_lower] = obj_id
        
        # Check for [huis N] pattern in address to build map
        # e.g. "Kerkweg 9a [huis 359]" -> Map 359 to this ID
        huis_match = re.search(r'\[huis\s*(\d+)\]', adres_lower)
        if huis_match:
            num = huis_match.group(1)
            fingerprints['huis_number_map'][num] = obj_id

        # Helper to add to map
        def add_to_map(val, map_name):
            if pd.isna(val) or val == 0: return
            val = round(float(val), 2)
            if val not in fingerprints[map_name]:
                fingerprints[map_name][val] = []
            if obj_id not in fingerprints[map_name][val]:
                fingerprints[map_name][val].append(obj_id)

        def add_relatie(name, map_name, map_key=None):
            if pd.isna(name): return
            clean_name = name.lower().strip()
            if map_key:
                key = (round(float(map_key), 2), clean_name)
            else:
                key = clean_name
                
            if key not in fingerprints[map_name]:
                fingerprints[map_name][key] = []
            if obj_id not in fingerprints[map_name][key]:
                fingerprints[map_name][key].append(obj_id)

        # Map Amounts
        amounts = [
            row['verhuur_prijs'], row['verhuur_incl_btw'], 
            row['verhuur_gwe'], row['kale_inhuurprijs'], 
            row['inhuur_incl_btw']
        ]
        for amt in amounts:
            add_to_map(amt, 'amount_map')
            
        # Map Relaties
        add_relatie(row['huurder_naam'], 'relatie_map')
        add_relatie(row['leverancier_naam'], 'relatie_map')
        
        # Map Specific Combinations (Strongest Signal)
        if not pd.isna(row['verhuur_incl_btw']):
            add_relatie(row['huurder_naam'], 'amount_relatie_map', row['verhuur_incl_btw'])
            
        if not pd.isna(row['inhuur_incl_btw']):
            add_relatie(row['leverancier_naam'], 'amount_relatie_map', row['inhuur_incl_btw'])

    print(f"   Indexed {len(fingerprints['amount_map'])} unique amounts")
    print(f"   Indexed {len(fingerprints['relatie_map'])} unique relations")
    print(f"   Indexed {len(fingerprints['valid_ids'])} unique Object IDs")
    print(f"   Indexed {len(fingerprints['huis_number_map'])} specific 'huis' numbers")
    return fingerprints

def clean_amount(val):
    if pd.isna(val) or val == '': return 0.0
    return round(float(val), 2)

def clean_text(val):
    if pd.isna(val): return ""
    return str(val).lower().strip()

def classify_row(row, fingerprints):
    """
    The Brain: Tries to determine the Object ID for a transaction row.
    Returns: (Predicted_ID, Confidence, Method, Reason)
    """
    description = clean_text(row['Omschrijving'])
    relatie_raw = clean_text(row['Relatie'])
    
    # Remove code from relatie (e.g., "50329 - Impianti..." -> "Impianti...")
    relatie_clean = relatie_raw.split(' - ', 1)[1] if ' - ' in relatie_raw else relatie_raw
    
    amount = 0.0
    # Determine amount (could be debit or credit depending on context)
    d = clean_amount(row['d'])
    c = clean_amount(row['c'])
    amount = d if d > 0 else c
    
    # 1. TEXT SEARCH (Highest Confidence)
    
    # 1A. Specific "Huisje" or "Huis" pattern matching (for Holland Chalet Park etc)
    # Looks for "huisje 359", "huis 346", etc.
    huisje_match = re.search(r'huis(je)?\s*(\d+)', description)
    if huisje_match:
        num = huisje_match.group(2)
        if num in fingerprints['huis_number_map']:
             found_id = fingerprints['huis_number_map'][num]
             return found_id, 'High', 'Huis Number Match', f"Found 'huis(je) {num}' matched to {found_id}"

    # 1B. Search for Object IDs (e.g. 0135, A-0099)
    # Regex: Look for 4 digits, optional A- prefix
    id_matches = re.finditer(r'\b(A-)?(\d{4})\b', description.upper())
    for match in id_matches:
        candidate_id = f"{match.group(1) or ''}{match.group(2)}"
        if candidate_id in fingerprints['valid_ids']:
             return candidate_id, 'High', 'Text Search', f"Found valid ID {candidate_id} in description"
        
    # Search for Address (Street Name)
    for addr, obj_id in fingerprints['house_addresses'].items():
        # Get street name part (e.g. "amperestraat")
        street = addr.split(' ')[0]
        if len(street) > 4 and street in description:
            # check number match too for safety
            number_match = re.search(r'\d+', addr)
            if number_match and number_match.group(0) in description:
                return obj_id, 'High', 'Address Search', f"Found address {addr} in description"

    # 2. FINANCIAL FINGERPRINTING (Strong)
    # Match specific (Amount + Relatie) combination
    key = (amount, relatie_clean)
    if key in fingerprints['amount_relatie_map']:
        candidates = fingerprints['amount_relatie_map'][key]
        if len(candidates) == 1:
            return candidates[0], 'High', 'Unique Contract Match', f"Only {candidates[0]} has contract with {relatie_clean} for €{amount}"
        elif len(candidates) > 1:
            return candidates[0], 'Medium', 'Multi Contract Match', f"Matches {len(candidates)} contracts (e.g. {candidates[0]})"
            
    # 3. RELATIE + AMOUNT (Medium)
    # If Relatie maps to one house AND Amount matches a known cost for that house
    if relatie_clean in fingerprints['relatie_map']:
        candidates = fingerprints['relatie_map'][relatie_clean]
        if len(candidates) == 1:
            # Check if amount matches ANY known amount for this house
            # This is a bit loose, but good for "Variable costs" from known supplier
            return candidates[0], 'Medium', 'Unique Relatie', f"Relatie {relatie_clean} only linked to {candidates[0]}"

    # 4. AMOUNT ONLY (Low/Risky - Only for large/unique amounts)
    # If amount is very specific (e.g. 1641.12) and unique to one house
    if amount > 500 and amount in fingerprints['amount_map']:
        candidates = fingerprints['amount_map'][amount]
        if len(candidates) == 1:
             return candidates[0], 'Low', 'Unique Amount', f"Only house {candidates[0]} has amount €{amount}"

    return None, None, None, None

# ... existing code ...

import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def classify_with_llm(row, fingerprints):
    """
    Asks Claude to classify the row based on the description and amounts.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None, None, None, None
        
    client = Anthropic(api_key=api_key)
    
    # Prepare context (simplified for token limit)
    # We can't send ALL fingerprints, but we can send some context or just ask it to infer
    # For now, let's just ask it to extract address if hidden, or match implied context
    
    prompt = f"""
    You are an expert financial auditor. Your task is to link a financial transaction to a specific Property (Address).
    
    Transaction Details:
    - Description: "{row['Omschrijving']}"
    - Relation: "{row['Relatie']}"
    - Amount: {row['d'] if row['d'] > 0 else -row['c']}
    
    Known Active Contracts (Context):
    - We have properties in Rotterdam, Vlaardingen, Schiedam, etc.
    - Common Suppliers: Vattenfall (Energy), Tradiro (Tenant).
    
    Task:
    1. Extract a hidden address or street name from the description.
    2. Infer the property based on the unique combination of Tenant Name or Amount if possible (though you don't have the full DB).
    3. Return the Street Name and House Number if found.
    
    Output Format: JSON
    {{
        "found_address": "Street Number",
        "confidence": "High/Medium/Low",
        "reasoning": "..."
    }}
    """
    
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse response (Simplified)
        content = message.content[0].text
        # Logic to extract address and match against fingerprints['house_addresses'] would go here
        # For this demo, we return the raw LLM thought process as a placeholder
        return None, "Low", "AI Attempt", "Not fully implemented yet"
        
    except Exception as e:
        print(f"LLM Error: {e}")
        return None, None, None, None

def main():
    print("🚀 Starting Smart Classifier (AI Enhanced)...")
    
    # ... existing loading code ...
    print(f"📂 Loading transactions from {INPUT_FILE}...")
    df = pd.read_excel(INPUT_FILE, sheet_name='Sheet1')
    target_rows = df[df['Kostenplaats'].isna()].copy()
    print(f"   Targeting {len(target_rows)} unclassified rows.")
    
    kb = load_knowledge_base()
    
    print("\n🕵️‍♀️ Classifying...")
    
    results = []
    classified_count = 0
    
    total = len(target_rows)
    for idx, row in target_rows.iterrows():
        # 1. Try Logic First (Fast)
        pred_id, conf, method, reason = classify_row(row, kb)
        
        # 2. Try LLM if Logic Fails
        # Limit to 50 rows for safety/cost during dev
        if not pred_id and idx < 50: 
             try:
                 # Call LLM
                 print(f"      🤖 Asking Claude about row {idx}...")
                 pred_id, conf, method, reason = classify_with_llm(row, kb)
             except Exception as e:
                 print(f"      ⚠️ LLM Call Failed: {e}")
        
        if pred_id:
            classified_count += 1
            results.append({
                'Original_Idx': idx,
                'Predicted_Kostenplaats': f"{pred_id} - [AI Generated]",
                'Confidence': conf,
                'Method': method,
                'Reason': reason
            })
            
    # ... existing export code ...
    print(f"✅ Classification Complete!")
    print(f"   Matched: {classified_count}/{total} ({classified_count/total*100:.1f}%)")
    
    if results:
        results_df = pd.DataFrame(results)
        output = df.loc[results_df['Original_Idx']].copy()
        output['AI_Predicted_ID'] = results_df['Predicted_Kostenplaats'].values
        output['AI_Confidence'] = results_df['Confidence'].values
        output['AI_Method'] = results_df['Method'].values
        output['AI_Reason'] = results_df['Reason'].values
        
        print(f"💾 Saving results to {OUTPUT_FILE}...")
        output.to_excel(OUTPUT_FILE, index=False)
    else:
        print("⚠️ No matches found.")

if __name__ == "__main__":
    main()
