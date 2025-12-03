import pandas as pd
import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'Sources', 'Houses + Informationrelated.xlsx')

def get_enriched_data():
    df = pd.read_excel(EXCEL_PATH)
    data = []
    for _, row in df.iterrows():
        adres = row['Adres']
        if pd.isna(adres): continue
        
        # Extract relevant fields
        huurder = row['Huurder'] if not pd.isna(row['Huurder']) else None
        eigenaar = row['Eigenaar'] if not pd.isna(row['Eigenaar']) else None
        voorschot_gwe = row['Voorschot GWE'] if not pd.isna(row['Voorschot GWE']) else 0
        
        # House details
        aantal_sk = row['Aant. SK'] if not pd.isna(row['Aant. SK']) else None
        aantal_pers = row['Aant. pers.'] if not pd.isna(row['Aant. pers.']) else None
        postcode = row['Postcode'] if not pd.isna(row['Postcode']) else None
        plaats = row['Plaats'] if not pd.isna(row['Plaats']) else None
        
        # Verhuur Contract Info
        verhuur_prijs = row['Kale verhuurprijs'] if not pd.isna(row['Kale verhuurprijs']) else None
        if verhuur_prijs is None: # Fallback
            verhuur_prijs = row['Verhuur EXCL. BTW'] if not pd.isna(row['Verhuur EXCL. BTW']) else None
            
        vh_start = row['Startdatum'] if not pd.isna(row['Startdatum']) else None
        vh_eind = row['Einddatum Min. Per.'] if not pd.isna(row['Einddatum Min. Per.']) else None
        
        # Inhuur Contract Info
        inhuur_prijs = row['Kale inhuurprijs'] if not pd.isna(row['Kale inhuurprijs']) else None
        if inhuur_prijs is None:
            inhuur_prijs = row['Inhuur EXCL BTW'] if not pd.isna(row['Inhuur EXCL BTW']) else None
            
        ih_start = row['Startdatum.1'] if not pd.isna(row['Startdatum.1']) else None
        ih_eind = row['Einddatum Min. Per..1'] if not pd.isna(row['Einddatum Min. Per..1']) else None

        data.append({
            'adres': adres,
            'huurder': huurder,
            'eigenaar': eigenaar,
            'voorschot_gwe': voorschot_gwe,
            'aantal_sk': aantal_sk,
            'aantal_pers': aantal_pers,
            'postcode': postcode,
            'plaats': plaats,
            'verhuur': {
                'prijs': verhuur_prijs,
                'start': vh_start,
                'eind': vh_eind
            },
            'inhuur': {
                'prijs': inhuur_prijs,
                'start': ih_start,
                'eind': ih_eind
            }
        })
    return data

def get_or_create_client(cursor, naam):
    if not naam: return None
    cursor.execute("SELECT id FROM klanten WHERE naam = ?", (naam,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        ctype = 'bureau' if 'BV' in naam or 'Services' in naam or 'Homes' in naam else 'particulier'
        cursor.execute("INSERT INTO klanten (naam, type) VALUES (?, ?)", (naam, ctype))
        return cursor.lastrowid

def get_or_create_supplier(cursor, naam):
    if not naam: return None
    cursor.execute("SELECT id FROM leveranciers WHERE naam = ?", (naam,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        cursor.execute("INSERT INTO leveranciers (naam) VALUES (?)", (naam,))
        return cursor.lastrowid

def format_date(d):
    if pd.isna(d): return None
    try:
        return pd.to_datetime(d).strftime('%Y-%m-%d')
    except:
        return None

def sync_database(db_path, enriched_data):
    print(f"🔄 Enriching {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    updated_count = 0
    houses_updated = 0
    contracts_created = 0
    
    for item in enriched_data:
        adres = item['adres']
        
        cursor.execute("SELECT id FROM huizen WHERE adres = ?", (adres,))
        house_row = cursor.fetchone()
        
        if not house_row:
            continue
            
        house_id = house_row[0]
        
        # 0. Update House Details (SK, Pers, Postcode, Plaats)
        house_fields = []
        house_vals = []
        if item['aantal_sk'] is not None:
            house_fields.append("aantal_sk = ?")
            house_vals.append(item['aantal_sk'])
        if item['aantal_pers'] is not None:
            house_fields.append("aantal_pers = ?")
            house_vals.append(item['aantal_pers'])
        if item['postcode'] is not None:
            house_fields.append("postcode = ?")
            house_vals.append(item['postcode'])
        if item['plaats'] is not None:
            house_fields.append("plaats = ?")
            house_vals.append(item['plaats'])
            
        if house_fields:
            query = f"UPDATE huizen SET {', '.join(house_fields)} WHERE id = ?"
            house_vals.append(house_id)
            cursor.execute(query, house_vals)
            houses_updated += 1
        
        # 1. Update/Create Client & Supplier
        client_id = get_or_create_client(cursor, item['huurder'])
        supplier_id = get_or_create_supplier(cursor, item['eigenaar'])
        
        # 2. Verhuur Contract
        if client_id and item['verhuur']['prijs']:
            # Check if contract exists
            cursor.execute("SELECT id FROM verhuur_contracten WHERE huis_id = ? AND klant_id = ?", (house_id, client_id))
            vc_row = cursor.fetchone()
            
            start_date = format_date(item['verhuur']['start']) or '2023-01-01'
            end_date = format_date(item['verhuur']['eind'])
            
            if not vc_row:
                cursor.execute("""
                    INSERT INTO verhuur_contracten (huis_id, klant_id, kale_huur, start_datum, eind_datum)
                    VALUES (?, ?, ?, ?, ?)
                """, (house_id, client_id, item['verhuur']['prijs'], start_date, end_date))
                contracts_created += 1
            else:
                cursor.execute("""
                    UPDATE verhuur_contracten SET kale_huur = ?, start_datum = ?, eind_datum = ?
                    WHERE id = ?
                """, (item['verhuur']['prijs'], start_date, end_date, vc_row[0]))

        # 3. Inhuur Contract
        if supplier_id and item['inhuur']['prijs']:
            cursor.execute("SELECT id FROM inhuur_contracten WHERE property_id = ? AND leverancier_id = ?", (house_id, supplier_id))
            ic_row = cursor.fetchone()
            
            start_date = format_date(item['inhuur']['start']) or '2023-01-01'
            end_date = format_date(item['inhuur']['eind'])
            
            if not ic_row:
                cursor.execute("""
                    INSERT INTO inhuur_contracten (property_id, leverancier_id, kale_huur, start_date, end_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (house_id, supplier_id, item['inhuur']['prijs'], start_date, end_date))
                contracts_created += 1
            else:
                cursor.execute("""
                    UPDATE inhuur_contracten SET kale_huur = ?, start_date = ?, end_date = ?
                    WHERE id = ?
                """, (item['inhuur']['prijs'], start_date, end_date, ic_row[0]))

        # 4. Update Bookings (Voorschot & Client)
        update_fields = []
        params = []
        
        if item['voorschot_gwe'] is not None:
            update_fields.append("voorschot_gwe = ?")
            params.append(item['voorschot_gwe'])
            
        if client_id:
            update_fields.append("klant_id = ?")
            params.append(client_id)
            
        if update_fields:
            query = f"UPDATE boekingen SET {', '.join(update_fields)} WHERE huis_id = ?"
            params.append(house_id)
            cursor.execute(query, params)
            if cursor.rowcount > 0:
                updated_count += 1
                
    conn.commit()
    conn.close()
    print(f"✅ Updated bookings for {updated_count} houses.")
    print(f"✅ Updated details for {houses_updated} houses.")
    print(f"✅ Processed {contracts_created} new contracts.")

if __name__ == "__main__":
    data = get_enriched_data()
    print(f"Found {len(data)} rows of enriched data.")
    
    db_core = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_core.db')
    db_mock = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_mock.db')
    
    if os.path.exists(db_core):
        sync_database(db_core, data)
        
    if os.path.exists(db_mock):
        sync_database(db_mock, data)
        
    print("🎉 Done enriching data.")
