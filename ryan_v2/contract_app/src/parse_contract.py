
import re
import sys
from pathlib import Path
from datetime import datetime

# Dutch month mapping
DUTCH_MONTHS = {
    'januari': '01', 'februari': '02', 'maart': '03', 'april': '04',
    'mei': '05', 'juni': '06', 'juli': '07', 'augustus': '08',
    'september': '09', 'oktober': '10', 'november': '11', 'december': '12'
}

def parse_dutch_date(date_str):
    try:
        parts = date_str.lower().split()
        if len(parts) != 3:
            return date_str
        day = parts[0].zfill(2)
        month = DUTCH_MONTHS.get(parts[1], '00')
        year = parts[2]
        return f"{year}-{month}-{day}"
    except:
        return date_str

def parse_contract_text(text):
    results = {}
    
    # --- 1. Duration ---
    # Pattern: gaat in op <date> ... loopt tot en met <date>
    start_date_match = re.search(r"gaat in op\s+(\d+\s+\w+\s+\d{4})", text, re.IGNORECASE)
    end_date_match = re.search(r"loopt tot en met\s+(\d+\s+\w+\s+\d{4})", text, re.IGNORECASE)
    
    if start_date_match:
        results['start_datum_raw'] = start_date_match.group(1)
        results['start_datum'] = parse_dutch_date(start_date_match.group(1))
    
    if end_date_match:
        results['eind_datum_raw'] = end_date_match.group(1)
        results['eind_datum'] = parse_dutch_date(end_date_match.group(1))
        
    # --- 2. Borg (Deposit) ---
    # Pattern: waarborgsom betalen ter grootte van een bedrag van € <amount>
    borg_match = re.search(r"waarborgsom.*?€\s*([\d\.,-]+)", text, re.IGNORECASE | re.DOTALL)
    if borg_match:
        results['borg_raw'] = borg_match.group(1)
        # Clean amount: swap dot/comma for float parsing if needed
        results['borg'] = borg_match.group(1).replace('.', '').replace(',', '.')
    
    # --- 3. GWE (Gas/Water/Electricity) ---
    # Priority: Check Financial Table (Voorschot G/W/E)
    # This overrides general text clauses because it reflects the actual payment obligation
    gwe_table_match = re.search(r"Voorschot G/W/E.*?€\s*([\d\.,-]+|n\.v\.t)", text, re.IGNORECASE)
    
    if gwe_table_match:
        val = gwe_table_match.group(1).strip().lower()
        results['gwe_voorschot'] = gwe_table_match.group(1)
        
        if 'n.v.t' in val or val == '0' or val == '0,00':
            results['gwe_provider'] = "Self/Excluded"
            results['gwe_included'] = False
        else:
            results['gwe_provider'] = "RyanRent"
            results['gwe_included'] = True
    else:
        # Fallback to Clause 6 text if table line missing (unlikely in this template)
        if re.search(r"Verhuurder zal zorgdragen voor de levering van elektriciteit, gas en water", text, re.IGNORECASE):
            results['gwe_provider'] = "RyanRent (Clause Text)"
        elif re.search(r"Huurder zal zelf zorgdragen", text, re.IGNORECASE):
            results['gwe_provider'] = "Self (Clause Text)"
        else:
            results['gwe_provider'] = "Unknown"

    # --- 4. Cleaning Costs (Eindschoonmaak) ---
    # Pattern: Kosten eindschoonmaak exclusief BTW € <amount>
    # Often found in the 'First Payment' section (approx Clause 5.10)
    cleaning_match = re.search(r"Kosten eindschoonmaak.*?€\s*([\d\.,-]+)", text, re.IGNORECASE)
    if cleaning_match:
        results['eindschoonmaak_kosten_raw'] = cleaning_match.group(1)
        results['eindschoonmaak_kosten'] = cleaning_match.group(1).replace('.', '').replace(',', '.')

    return results

if __name__ == "__main__":
    # If a file argument is provided, read it. Otherwise read the analyze_pdf output file
    if len(sys.argv) > 1:
        fpath = sys.argv[1]
        with open(fpath, 'r') as f:
            text = f.read()
    else:
        # Default to the previous dump
        fpath = "contract_text.txt" 
        try:
            with open(fpath, 'r') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: {fpath} not found. Run analyze_pdf.py first.")
            sys.exit(1)

    extracted = parse_contract_text(text)
    
    print("--- Extracted Contract Data ---")
    for key, val in extracted.items():
        print(f"{key}: {val}")
