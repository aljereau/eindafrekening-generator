import pandas as pd
import os
import sys
from datetime import datetime
import re

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.manager import HuizenManager
from Shared.entities import Huis, Eigenaar, InhuurContract

def parse_dutch_float(val):
    if pd.isna(val) or val == '':
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    # Replace comma with dot, remove thousands separator if any (usually dot in Dutch, but here likely none or dot)
    # The CSV output showed "207,6924675", so comma is decimal separator.
    val = str(val).replace(',', '.')
    try:
        return float(val)
    except ValueError:
        return 0.0

def parse_date(val):
    if pd.isna(val) or val == '':
        return None
    # Excel serial date? Or string?
    # CSV output showed "45961" which is Excel serial date.
    try:
        # Check if it's an Excel serial date (int/float)
        serial = float(val)
        # Excel base date is usually Dec 30 1899
        return datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(serial) - 2).date()
    except (ValueError, TypeError):
        pass
        
    # Try string formats
    for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']:
        try:
            return datetime.strptime(str(val), fmt).date()
        except ValueError:
            continue
    return None

def import_data():
    manager = HuizenManager()
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    csv_path = os.path.join(base_dir, "HuizenManager", "Huizenlijst.csv")
    excel_path = os.path.join(base_dir, "HuizenManager", "1-CoHousingNL_B.V.-26-11-2025-HRMCostCenters.xlsx")

    print("--- Starting Import ---")

    # 1. Import Active Houses from CSV
    print(f"Reading CSV: {csv_path}")
    # Use sep=';' based on the header inspection
    df_csv = pd.read_csv(csv_path, sep=';', dtype=str)
    
    success_count = 0
    
    for _, row in df_csv.iterrows():
        try:
            obj_id_raw = row.get('Object_ID')
            if pd.isna(obj_id_raw) or not obj_id_raw:
                continue
                
            # Pad Object ID to 4 digits
            object_id = obj_id_raw.zfill(4)
            
            # Check if house exists
            existing_huis = None
            # We don't have get_huis_by_object_id yet, but we can check via DB directly or add a method.
            # For now, let's just try to add, if it fails (unique constraint?) 
            # Actually we don't have a unique constraint on object_id in the schema yet?
            # Migration 003 added index but not UNIQUE constraint.
            # Let's check via SQL
            conn = manager.db._get_connection()
            existing = conn.execute("SELECT id FROM huizen WHERE object_id = ?", (object_id,)).fetchone()
            conn.close()
            
            if existing:
                print(f"House {object_id} exists. Checking/Adding contract...")
                huis_id = existing['id']
            else:
                # Create Huis
                huis = Huis(
                    id=None,
                    object_id=object_id,
                    adres=row.get('Adres', ''),
                    postcode=row.get('Postcode', ''),
                    plaats=row.get('Plaats', ''),
                    aantal_sk=int(float(row.get('Aant. SK', 0) or 0)),
                    aantal_pers=int(float(row.get('Aant. pers.', 0) or 0)),
                    status='active'
                )
                huis_id = manager.add_huis(huis)
            
            # Create/Find Owner
            eigenaar_name = row.get('Eigenaar')
            eigenaar_id = None
            if eigenaar_name and not pd.isna(eigenaar_name):
                existing_owner = manager.get_eigenaar_by_name(eigenaar_name)
                if existing_owner:
                    eigenaar_id = existing_owner.id
                else:
                    eigenaar = Eigenaar(
                        id=None,
                        naam=eigenaar_name,
                        telefoonnummer=row.get('Telefoonnummer')
                    )
                    eigenaar_id = manager.add_eigenaar(eigenaar)
            
            # Create Contract
            # Inhuur section
            kale_huur = parse_dutch_float(row.get('Kale inhuurprijs'))
            inhuur_incl = parse_dutch_float(row.get('Inhuur INCL BTW'))
            inhuur_excl = parse_dutch_float(row.get('Inhuur EXCL BTW'))
            
            # Calculate service costs as difference between Excl and Kale
            service_costs = max(0, inhuur_excl - kale_huur)
            
            # Start date
            start_date = parse_date(row.get('Startdatum.1')) # .1 because there are two Startdatum columns
            if not start_date:
                start_date = parse_date(row.get('Startdatum')) # Try the first one if second is missing
            if not start_date:
                start_date = datetime.today().date() # Fallback

            # Check if contract already exists to avoid dupes
            active_contract = manager.get_active_contract(huis_id, start_date)
            if active_contract and active_contract.start_date == start_date:
                 print(f"Contract for {object_id} already exists.")
            else:
                contract = InhuurContract(
                    id=None,
                    property_id=huis_id,
                    eigenaar_id=eigenaar_id,
                    start_date=start_date,
                    kale_huur=kale_huur,
                    servicekosten=service_costs,
                    totale_huur=inhuur_incl,
                    # We don't have explicit columns for other costs, so we leave them 0
                )
                manager.add_contract(contract)
                success_count += 1
            
        except Exception as e:
            print(f"Error importing row {row.get('Object_ID')}: {e}")

    print(f"Imported {success_count} active houses from CSV.")

    # 2. Import Archived Houses from Excel
    print(f"Reading Excel: {excel_path}")
    try:
        # Find header row
        df_head = pd.read_excel(excel_path, header=None)
        header_row_idx = df_head[df_head.iloc[:, 0] == 'Code'].index[0]
        df_excel = pd.read_excel(excel_path, skiprows=header_row_idx+1, header=None)
        df_excel.columns = ['Code', 'Omschrijving']
        
        archived_count = 0
        for _, row in df_excel.iterrows():
            code = str(row['Code'])
            if code.startswith('A-'):
                # Check if exists
                conn = manager.db._get_connection()
                # Need to use new table name 'huizen' here too!
                existing = conn.execute("SELECT id FROM huizen WHERE object_id = ?", (code,)).fetchone()
                conn.close()
                
                if existing:
                    continue
                
                # Parse Address/City from Omschrijving
                desc = str(row['Omschrijving'])
                # Heuristic: Split by comma
                parts = desc.split(',')
                if len(parts) >= 2:
                    address = parts[0].strip()
                    city = parts[1].strip()
                    # Remove extra info in parens from city
                    city = re.sub(r'\(.*\)', '', city).strip()
                else:
                    # Try to split by last space if looks like city? Difficult.
                    # Just put everything in address
                    address = desc
                    city = ""

                huis = Huis(
                    id=None,
                    object_id=code,
                    adres=address,
                    plaats=city,
                    status='archived'
                )
                manager.add_huis(huis)
                archived_count += 1
                
        print(f"Imported {archived_count} archived houses from Excel.")
        
    except Exception as e:
        print(f"Error reading Excel: {e}")

if __name__ == "__main__":
    import_data()
