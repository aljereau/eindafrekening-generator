import os
import sys
import pandas as pd
import sqlite3
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import existing scripts
import create_input_template

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'Templates', 'RyanRent_Input_Template.xlsx')
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_core.db')

def get_conn():
    return sqlite3.connect(DB_PATH)

def process_input_sheet():
    print(f"📂 Reading input sheet from: {TEMPLATE_PATH}")
    if not os.path.exists(TEMPLATE_PATH):
        print("❌ Template file not found! Please generate it first.")
        return

    df = pd.read_excel(TEMPLATE_PATH)
    conn = get_conn()
    cursor = conn.cursor()
    
    processed = 0
    
    for _, row in df.iterrows():
        # Skip empty rows
        if pd.isna(row['Object ID (e.g. 0099)']): continue
        
        obj_id = str(row['Object ID (e.g. 0099)']).strip()
        adres = row['Adres']
        
        # 1. Upsert House
        cursor.execute("SELECT id FROM huizen WHERE object_id = ?", (obj_id,))
        house_row = cursor.fetchone()
        
        if house_row:
            house_id = house_row[0]
            print(f"   🔄 Updating house {obj_id} ({adres})...")
            # Update fields if provided
            fields = []
            vals = []
            
            if not pd.isna(row['Aantal Slaapkamers']): fields.append("aantal_sk = ?"); vals.append(row['Aantal Slaapkamers'])
            if not pd.isna(row['Aantal Personen']): fields.append("aantal_pers = ?"); vals.append(row['Aantal Personen'])
            if not pd.isna(row['Kluis Code 1']): fields.append("kluis_code_1 = ?"); vals.append(str(row['Kluis Code 1']))
            if not pd.isna(row['Kluis Code 2']): fields.append("kluis_code_2 = ?"); vals.append(str(row['Kluis Code 2']))
            
            if fields:
                query = f"UPDATE huizen SET {', '.join(fields)} WHERE id = ?"
                vals.append(house_id)
                cursor.execute(query, vals)
        else:
            print(f"   ➕ Creating new house {obj_id} ({adres})...")
            cursor.execute("""
                INSERT INTO huizen (object_id, adres, postcode, plaats, aantal_sk, aantal_pers, kluis_code_1, kluis_code_2)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                obj_id, 
                adres, 
                row['Postcode'], 
                row['Plaats'], 
                row['Aantal Slaapkamers'], 
                row['Aantal Personen'],
                str(row['Kluis Code 1']) if not pd.isna(row['Kluis Code 1']) else None,
                str(row['Kluis Code 2']) if not pd.isna(row['Kluis Code 2']) else None
            ))
            house_id = cursor.lastrowid
            
        # 2. Process Contracts (Simplified)
        # Client
        if not pd.isna(row['Huurder (Naam)']):
            client_name = row['Huurder (Naam)']
            cursor.execute("SELECT id FROM klanten WHERE naam = ?", (client_name,))
            c_row = cursor.fetchone()
            if c_row: cid = c_row[0]
            else:
                cursor.execute("INSERT INTO klanten (naam, type) VALUES (?, 'zakelijk')", (client_name,))
                cid = cursor.lastrowid
            
            # Verhuur Contract
            if not pd.isna(row['Verhuur Prijs (Kale huur)']):
                start = row['Start Datum (YYYY-MM-DD)'] if not pd.isna(row['Start Datum (YYYY-MM-DD)']) else date.today().strftime('%Y-%m-%d')
                end = row['Eind Datum (YYYY-MM-DD)'] if not pd.isna(row['Eind Datum (YYYY-MM-DD)']) else None
                
                # Check active
                cursor.execute("SELECT id FROM verhuur_contracten WHERE huis_id = ? AND status = 'active'", (house_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO verhuur_contracten (huis_id, klant_id, kale_huur, start_datum, eind_datum)
                        VALUES (?, ?, ?, ?, ?)
                    """, (house_id, cid, row['Verhuur Prijs (Kale huur)'], start, end))
                    print(f"      📄 Created rental contract for {client_name}")

        processed += 1
        
    conn.commit()
    conn.close()
    print(f"✅ Processed {processed} rows from input sheet.")

def main():
    print("\n🤖 RYAN BOT - Workflow Automation 🤖")
    print("-----------------------------------")
    print("1. 📝 Generate Input Template")
    print("2. 📥 Process Filled Input Sheet")
    print("3. ❌ Exit")
    
    choice = input("\nSelect an option (1-3): ")
    
    if choice == '1':
        print("\nGenerating template...")
        import subprocess
        script_path = os.path.join(os.path.dirname(__file__), 'create_input_template.py')
        subprocess.run([sys.executable, script_path])
        
    elif choice == '2':
        process_input_sheet()
        
    elif choice == '3':
        print("Bye! 👋")
        
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
