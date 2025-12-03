import pandas as pd
import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'Sources', 'Klanten + Leverancies info.xlsx')

def get_info_data():
    df = pd.read_excel(EXCEL_PATH)
    data = []
    for _, row in df.iterrows():
        naam = row['Naam']
        if pd.isna(naam): continue
        
        # Determine roles
        is_client = str(row['Klant']).lower() in ['ja', 'yes', 'true', '1'] if not pd.isna(row['Klant']) else False
        is_supplier = str(row['Leverancier']).lower() in ['ja', 'yes', 'true', '1'] if not pd.isna(row['Leverancier']) else False
        
        # If neither specified, infer? Or skip?
        # Let's assume if it's in the list, we should try to match it.
        
        info = {
            'naam': naam,
            'adres': row['Adres'] if not pd.isna(row['Adres']) else None,
            'plaats': row['Plaats'] if not pd.isna(row['Plaats']) else None,
            'email': row['E-mailadres'] if not pd.isna(row['E-mailadres']) else None,
            'iban': row['Bankrekening'] if not pd.isna(row['Bankrekening']) else None,
            'kvk': row['Kamer van Koophandel'] if not pd.isna(row['Kamer van Koophandel']) else None,
            'is_client': is_client,
            'is_supplier': is_supplier
        }
        data.append(info)
    return data

def update_table(cursor, table, info, is_supplier_table=False):
    # Try to find by name
    cursor.execute(f"SELECT id FROM {table} WHERE naam = ?", (info['naam'],))
    row = cursor.fetchone()
    
    fields = []
    values = []
    
    if info['email']:
        fields.append("email = ?")
        values.append(info['email'])
        
    if info['iban']:
        fields.append("iban = ?")
        values.append(info['iban'])
        
    if not is_supplier_table: # Clients have more fields
        if info['adres']:
            full_adres = f"{info['adres']}, {info['plaats']}" if info['plaats'] else info['adres']
            fields.append("adres = ?")
            values.append(full_adres)
        if info['kvk']:
            fields.append("kvk_nummer = ?")
            values.append(info['kvk'])
            
    if not fields:
        return False # Nothing to update
        
    if row:
        # Update existing
        query = f"UPDATE {table} SET {', '.join(fields)} WHERE id = ?"
        values.append(row[0])
        cursor.execute(query, values)
        return True
    else:
        # Insert new?
        # Only insert if explicitly marked as such in Excel, to avoid polluting with random entities?
        # Or just insert everything?
        # Let's insert if marked.
        should_insert = info['is_supplier'] if is_supplier_table else info['is_client']
        
        if should_insert:
            cols = ["naam"]
            vals = [info['naam']]
            
            if info['email']:
                cols.append("email")
                vals.append(info['email'])
            if info['iban']:
                cols.append("iban")
                vals.append(info['iban'])
                
            if not is_supplier_table:
                if info['adres']:
                    cols.append("adres")
                    vals.append(f"{info['adres']}, {info['plaats']}" if info['plaats'] else info['adres'])
                if info['kvk']:
                    cols.append("kvk_nummer")
                    vals.append(info['kvk'])
                    
            placeholders = ", ".join(["?"] * len(cols))
            query = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
            cursor.execute(query, vals)
            return True
            
    return False

def sync_database(db_path, info_data):
    print(f"🔄 Syncing info to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    clients_updated = 0
    suppliers_updated = 0
    
    for info in info_data:
        # Try updating clients
        if update_table(cursor, 'klanten', info, is_supplier_table=False):
            clients_updated += 1
            
        # Try updating suppliers
        if update_table(cursor, 'leveranciers', info, is_supplier_table=True):
            suppliers_updated += 1
            
    conn.commit()
    conn.close()
    print(f"✅ Processed info: {clients_updated} clients / {suppliers_updated} suppliers updated/added.")

if __name__ == "__main__":
    data = get_info_data()
    print(f"Found {len(data)} entities in Excel.")
    
    db_core = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_core.db')
    db_mock = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_mock.db')
    
    if os.path.exists(db_core):
        sync_database(db_core, data)
        
    if os.path.exists(db_mock):
        sync_database(db_mock, data)
        
    print("🎉 Done syncing info.")
