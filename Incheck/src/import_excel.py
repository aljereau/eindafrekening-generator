import pandas as pd
import sqlite3
import os
import sys
from datetime import datetime, date, time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Shared.database import Database

def import_excel_data(excel_path, db_path):
    print(f"Reading {excel_path}...")
    df = pd.read_excel(excel_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Importing data...")
    
    # Detect format based on columns
    cols = df.columns.tolist()
    is_new_format = 'Checkout_Scheduled_Date' in cols
    
    for index, row in df.iterrows():
        try:
            # Initialize variables
            huis_id = None
            object_id = None
            booking_id = None
            
            # --- 1. Parse Address & House ---
            if is_new_format:
                adres_raw = str(row.get('Property_Address', ''))
                object_id = str(row.get('Property_ID', ''))
            else:
                adres_raw = str(row.get('Adres', ''))
                # Try to extract ID if present in brackets [123]
                import re
                match = re.search(r'\[huis (\d+)\]', adres_raw)
                if match:
                    object_id = match.group(1)
            
            # Find or Create House
            if object_id and object_id != 'nan':
                cursor.execute("SELECT id FROM huizen WHERE object_id = ?", (object_id,))
                res = cursor.fetchone()
                if res:
                    huis_id = res[0]
            
            if not huis_id:
                # Try by address
                cursor.execute("SELECT id FROM huizen WHERE adres = ?", (adres_raw,))
                res = cursor.fetchone()
                if res:
                    huis_id = res[0]
                else:
                    # Create new house
                    if not object_id or object_id == 'nan':
                        import hashlib
                        hash_object = hashlib.md5(adres_raw.encode())
                        object_id = hash_object.hexdigest()[:6].upper()
                    
                    print(f"⚠️ Creating new house: {adres_raw} (ID: {object_id})")
                    cursor.execute("""
                        INSERT INTO huizen (object_id, adres, plaats, status)
                        VALUES (?, ?, ?, 'active')
                    """, (object_id, adres_raw, 'Unknown'))
                    huis_id = cursor.lastrowid

            # --- 2. Parse Client ---
            if is_new_format:
                client_name = str(row.get('Client_Name', 'Unknown'))
            else:
                client_name = str(row.get('Klant', 'Unknown'))
                
            if pd.isna(client_name) or client_name == 'nan':
                client_name = "Unknown Client"
                
            cursor.execute("SELECT id FROM klanten WHERE naam = ?", (client_name,))
            res = cursor.fetchone()
            if res:
                client_id = res[0]
            else:
                cursor.execute("INSERT INTO klanten (naam) VALUES (?)", (client_name,))
                client_id = cursor.lastrowid
                
            # --- 3. Parse Booking (Checkout) ---
            if is_new_format:
                checkout_date = row.get('Checkout_Scheduled_Date')
            else:
                checkout_date = row.get('Datum') or row.get(' Uitcheck Datum ')
                
            if pd.isna(checkout_date):
                print(f"Skipping row {index}: No checkout date")
                continue
                
            # Normalize Date
            if isinstance(checkout_date, str):
                try:
                    checkout_date = datetime.strptime(checkout_date, '%d-%m-%Y').date()
                except:
                    try:
                        checkout_date = datetime.strptime(checkout_date, '%Y-%m-%d').date()
                    except:
                        pass
            elif hasattr(checkout_date, 'date'):
                checkout_date = checkout_date.date()
                
            if not isinstance(checkout_date, date):
                print(f"Skipping row {index}: Invalid date {checkout_date}")
                continue

            # Find or Create Booking
            cursor.execute("""
                SELECT id FROM boekingen 
                WHERE huis_id = ? AND checkout_datum = ?
            """, (huis_id, checkout_date))
            
            res = cursor.fetchone()
            if res:
                booking_id = res[0]
            else:
                # Create booking (assume 6 months prior checkin)
                from datetime import timedelta
                checkin_date = checkout_date - timedelta(days=180)
                
                cursor.execute("""
                    INSERT INTO boekingen (huis_id, klant_id, checkin_datum, checkout_datum, status)
                    VALUES (?, ?, ?, ?, 'confirmed')
                """, (huis_id, client_id, checkin_date, checkout_date))
                booking_id = cursor.lastrowid
                
            # --- 4. Populate uitchecks (New Format Only) ---
            if is_new_format:
                werkelijke_datum = row.get('Checkout_Actual_Date')
                if pd.isna(werkelijke_datum): werkelijke_datum = None
                elif hasattr(werkelijke_datum, 'date'): werkelijke_datum = werkelijke_datum.date()
                
                werkelijke_tijd = row.get('Checkout_Time')
                if pd.isna(werkelijke_tijd): werkelijke_tijd = None
                
                # Boolean fields
                def parse_bool(val):
                    return 1 if str(val).lower() in ['yes', 'ja', 'true', '1'] else 0
                
                terug_naar_eigenaar = parse_bool(row.get('Returning_To_Owner'))
                schoonmaak_vereist = parse_bool(row.get('Cleaning_Required'))
                meubilair_verwijderen = parse_bool(row.get('Furniture_Removal'))
                sleutels_ontvangen = parse_bool(row.get('Keys_Collected'))
                schade_gemeld = parse_bool(row.get('Damage_Reported'))
                afrekening_status = row.get('Settlement_Status', 'in_afwachting')
                
                # Check if uitcheck exists
                cursor.execute("SELECT id FROM uitchecks WHERE boeking_id = ?", (booking_id,))
                if cursor.fetchone():
                    cursor.execute("""
                        UPDATE uitchecks 
                        SET werkelijke_datum=?, tijd=?, terug_naar_eigenaar=?, 
                            schoonmaak_vereist=?, meubilair_verwijderen=?, sleutels_ontvangen=?, 
                            schade_gemeld=?, afrekening_status=?
                        WHERE boeking_id=?
                    """, (werkelijke_datum, werkelijke_tijd, terug_naar_eigenaar, schoonmaak_vereist, 
                          meubilair_verwijderen, sleutels_ontvangen, schade_gemeld, afrekening_status, booking_id))
                else:
                    cursor.execute("""
                        INSERT INTO uitchecks 
                        (boeking_id, geplande_datum, werkelijke_datum, tijd, terug_naar_eigenaar, schoonmaak_vereist, 
                         meubilair_verwijderen, sleutels_ontvangen, schade_gemeld, afrekening_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (booking_id, checkout_date, werkelijke_datum, werkelijke_tijd, terug_naar_eigenaar, 
                          schoonmaak_vereist, meubilair_verwijderen, sleutels_ontvangen, schade_gemeld, afrekening_status))

            # --- 5. Create/Update Inspecties ---
            # Voorinspectie
            pre_date = row.get('Pre_Inspection_Date') if is_new_format else row.get('Datum Vooroplevering (PRE)')
            if not pd.isna(pre_date):
                if hasattr(pre_date, 'date'): pre_date = pre_date.date()
                
                cursor.execute("SELECT id FROM inspecties WHERE boeking_id=? AND inspectie_type='voorinspectie'", (booking_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO inspecties (boeking_id, inspectie_type, geplande_datum, status)
                        VALUES (?, 'voorinspectie', ?, 'gepland')
                    """, (booking_id, pre_date))
            
            # Eindinspectie
            cursor.execute("SELECT id FROM inspecties WHERE boeking_id=? AND inspectie_type='eindinspectie'", (booking_id,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO inspecties (boeking_id, inspectie_type, geplande_datum, status)
                    VALUES (?, 'eindinspectie', ?, 'gepland')
                """, (booking_id, checkout_date))

        except Exception as e:
            print(f"Error processing row {index}: {e}")
            continue
            
    conn.commit()
    conn.close()
    print("Import completed!")

if __name__ == "__main__":
    # Default to the new file if available
    default_file = 'Incheck/RyanRent_Uitchecks_WITH_DATA.xlsx'
    if not os.path.exists(default_file):
        default_file = 'Incheck/UitchecksData.xlsx'
        
    import_excel_data(default_file, 'database/ryanrent_core.db')
