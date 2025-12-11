import sys
import os
import pandas as pd
import sqlite3
from datetime import date

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.manager import HuizenManager

def clean_iban(iban):
    if pd.isna(iban): return None
    return str(iban).replace(" ", "").upper()

def import_entities():
    manager = HuizenManager()
    
    # 1. Import Clients (Klanten)
    print("\n--- Importing Clients from klanten.xlsx ---")
    try:
        df_klanten = pd.read_excel('klanten.xlsx', header=11)
        # Expected columns: Code, Naam, ..., E-mailadres
        # We need to map them to our schema: naam, email, telefoonnummer, iban, kvk_nummer
        
        count = 0
        for _, row in df_klanten.iterrows():
            if pd.isna(row['Naam']): continue
            
            naam = row['Naam']
            email = row['E-mailadres'] if 'E-mailadres' in row else None
            # Assuming 'Bankrekening' exists, if not we skip
            iban = clean_iban(row.get('Bankrekening'))
            kvk = str(row.get('Kamer van Koophandel')) if not pd.isna(row.get('Kamer van Koophandel')) else None
            
            # Check if exists
            conn = manager.db._get_connection()
            exists = conn.execute("SELECT id FROM klanten WHERE naam = ?", (naam,)).fetchone()
            conn.close()
            
            if not exists:
                # Determine margin based on name (Tradiro = 8%, others = 15%)
                max_marge = 8.0 if 'Tradiro' in naam else None
                min_marge = 15.0 if not max_marge else None
                
                manager.add_klant(naam, email=email, min_marge=min_marge, max_marge=max_marge)
                count += 1
                
        print(f"✅ Imported {count} new clients.")
        
    except Exception as e:
        print(f"❌ Error importing clients: {e}")

    # 2. Import Suppliers (Eigenaren)
    print("\n--- Importing Suppliers from leverancier.xlsx ---")
    try:
        df_lev = pd.read_excel('leverancier.xlsx', header=11)
        
        count = 0
        for _, row in df_lev.iterrows():
            if pd.isna(row['Naam']): continue
            
            naam = row['Naam']
            email = row['E-mailadres'] if 'E-mailadres' in row else None
            iban = clean_iban(row.get('Bankrekening'))
            
            # Check if exists
            conn = manager.db._get_connection()
            exists = conn.execute("SELECT id FROM eigenaren WHERE naam = ?", (naam,)).fetchone()
            conn.close()
            
            if not exists:
                # We use the raw SQL insert or add_eigenaar if we update it to take more fields
                # For now, add_eigenaar takes (naam, email, telefoon, iban)
                # We don't have phone in the snippet, so pass None
                
                # Create Eigenaar object logic inline or use manager
                # manager.add_eigenaar expects Eigenaar object, let's just do direct SQL for speed/simplicity here
                # or construct the object. Let's use SQL to avoid importing Eigenaar entity just for this.
                conn = manager.db._get_connection()
                conn.execute("INSERT INTO eigenaren (naam, email, iban) VALUES (?, ?, ?)", (naam, email, iban))
                conn.commit()
                conn.close()
                count += 1
                
        print(f"✅ Imported {count} new suppliers (owners).")
        
    except Exception as e:
        print(f"❌ Error importing suppliers: {e}")

    # 3. Link to Houses (Huizenlijst.csv)
    print("\n--- Linking Entities to Houses ---")
    try:
        df_huizen = pd.read_csv('Archive/Huizenlijst.csv', sep=';')
        
        linked_contracts = 0
        linked_owners = 0
        
        for _, row in df_huizen.iterrows():
            # Fix Object ID formatting (Handle 22.0 -> 0022)
            raw_id = row['Object_ID']
            if pd.isna(raw_id): continue
            
            try:
                # Convert to int first to remove .0, then string, then zfill
                obj_id = str(int(float(raw_id))).zfill(4)
            except ValueError:
                # Handle non-numeric IDs if any (e.g. A-123)
                obj_id = str(raw_id)
            
            huurder_naam = row['Huurder']
            eigenaar_naam = row['Eigenaar']
            
            # Find House ID
            conn = manager.db._get_connection()
            huis_row = conn.execute("SELECT id FROM huizen WHERE object_id = ?", (obj_id,)).fetchone()
            conn.close()
            
            if not huis_row:
                continue
            huis_id = huis_row['id']
            
            # A. Link Owner (Create Inhuur Contract if missing)
            if not pd.isna(eigenaar_naam):
                # Find Owner ID
                conn = manager.db._get_connection()
                eig_row = conn.execute("SELECT id FROM eigenaren WHERE naam LIKE ?", (f"%{eigenaar_naam}%",)).fetchone()
                conn.close()
                
                if eig_row:
                    eig_id = eig_row['id']
                    # Check if contract exists
                    existing = manager.get_active_contract(huis_id)
                    if not existing:
                        # Create dummy contract
                        # We need kale_huur etc. from CSV if available
                        kale_huur = float(str(row['Kale inhuurprijs']).replace(',', '.')) if not pd.isna(row['Kale inhuurprijs']) else 0
                        
                        conn = manager.db._get_connection()
                        conn.execute("""
                            INSERT INTO inhuur_contracten (property_id, eigenaar_id, start_date, kale_huur)
                            VALUES (?, ?, ?, ?)
                        """, (huis_id, eig_id, date.today(), kale_huur))
                        conn.commit()
                        conn.close()
                        linked_owners += 1

            # B. Link Client (Create Verhuur Contract if missing)
            if not pd.isna(huurder_naam):
                # Find Client ID
                conn = manager.db._get_connection()
                klant_row = conn.execute("SELECT id FROM klanten WHERE naam LIKE ?", (f"%{huurder_naam}%",)).fetchone()
                conn.close()
                
                if klant_row:
                    klant_id = klant_row['id']
                    # Check if contract exists
                    conn = manager.db._get_connection()
                    existing = conn.execute("SELECT id FROM verhuur_contracten WHERE huis_id = ?", (huis_id,)).fetchone()
                    
                    if not existing:
                        kale_huur = float(str(row['Kale verhuurprijs']).replace(',', '.')) if not pd.isna(row['Kale verhuurprijs']) else 0
                        
                        conn.execute("""
                            INSERT INTO verhuur_contracten (huis_id, klant_id, start_datum, kale_huur)
                            VALUES (?, ?, ?, ?)
                        """, (huis_id, klant_id, date.today(), kale_huur))
                        conn.commit()
                        linked_contracts += 1
                    conn.close()

        print(f"✅ Created {linked_owners} owner contracts.")
        print(f"✅ Created {linked_contracts} client contracts.")

    except Exception as e:
        print(f"❌ Error linking houses: {e}")

if __name__ == "__main__":
    import_entities()
