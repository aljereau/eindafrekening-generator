import pandas as pd
import sqlite3
import os
import sys
from datetime import date

# Setup paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, "database", "ryanrent_mock.db")
EXCEL_PATH = os.path.join(PROJECT_ROOT, "Shared", "Sources", "GWE Voorschot Per object.xlsx")

def clean_currency(val):
    if pd.isna(val) or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        # Remove €, space, replace , with .
        val = val.replace('€', '').replace(' ', '').replace(',', '.')
        try:
            return float(val)
        except:
            return 0.0
    return 0.0

def update_database():
    print(f"📂 Reading Excel: {EXCEL_PATH}")
    try:
        df = pd.read_excel(EXCEL_PATH)
    except Exception as e:
        print(f"❌ Failed to read Excel: {e}")
        return

    # Normalize columns (strip spaces)
    df.columns = [c.strip() for c in df.columns]
    print(f"   Columns found: {list(df.columns)}")
    
    print(f"📂 Database Path: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # DEBUG: Check columns
    cursor.execute("PRAGMA table_info(huizen)")
    cols = [r['name'] for r in cursor.fetchall()]
    print(f"🔎 Huizen Columns: {cols}")
    if 'minimum_verhuur_prijs' not in cols:
        print("⚠️  MISSING COLUMN: minimum_verhuur_prijs")
        # Optional: Add it on the fly if missing (Ad-hoc fix)
        # cursor.execute("ALTER TABLE huizen ADD COLUMN minimum_verhuur_prijs REAL DEFAULT 0")
        # conn.commit()
        
    updated_houses = 0
    updated_inhuur = 0
    updated_verhuur = 0
    
    for _, row in df.iterrows():
        try:
            obj_num = row.get('Object nummer')
            if pd.isna(obj_num): 
                continue
                
            # Handle object number format (e.g. 63 -> "0063", 254 -> "0254")
            # DB seems to use 4-digit zero padding
            obj_id_str = str(int(obj_num)).zfill(4) if isinstance(obj_num, (int, float)) else str(obj_num)
            
            # 1. Find House
            cursor.execute("SELECT id FROM huizen WHERE object_id = ?", (obj_id_str,))
            house = cursor.fetchone()
            
            if not house:
                print(f"⚠️  House not found for Object {obj_id_str} (Row val: {obj_num})")
                continue
                
            house_id = house['id']
            
            # Extract Values
            voorschot_gwe = clean_currency(row.get('Voorschot GWE'))
            kale_inhuur = clean_currency(row.get('Kale inhuurprijs'))
            inhuur_excl = clean_currency(row.get('Inhuur EXCL BTW'))
            inhuur_incl = clean_currency(row.get('Inhuur INCL BTW'))
            kale_verhuur = clean_currency(row.get('Kale verhuurprijs'))
            
            # 2. Update House Defaults
            # Removed minimum_verhuur_prijs from huizen as it doesn't exist there
            cursor.execute("""
                UPDATE huizen 
                SET voorschot_gwe = ?
                WHERE id = ?
            """, (voorschot_gwe, house_id))
            updated_houses += 1
            
            # 3. Update Active Inhuur Contract
            # Find contract that is currently active (end_date >= now OR end_date IS NULL)
            cursor.execute("""
                SELECT id FROM inhuur_contracten 
                WHERE property_id = ? 
                AND (end_date >= DATE('now') OR end_date IS NULL)
                ORDER BY start_date DESC LIMIT 1
            """, (house_id,))
            inhuur_contract = cursor.fetchone()
            
            if inhuur_contract:
                cursor.execute("""
                    UPDATE inhuur_contracten
                    SET kale_huur = ?, 
                        voorschot_gwe = ?,
                        inhuur_prijs_excl_btw = ?,
                        inhuur_prijs_incl_btw = ?
                    WHERE id = ?
                """, (kale_inhuur, voorschot_gwe, inhuur_excl, inhuur_incl, inhuur_contract['id']))
                updated_inhuur += 1
            
            # 4. Update Active Verhuur Contract (Rent only)
            if kale_verhuur > 0:
                cursor.execute("""
                    UPDATE verhuur_contracten
                    SET kale_huur = ?
                    WHERE huis_id = ?
                    AND (eind_datum >= DATE('now') OR eind_datum IS NULL)
                """, (kale_verhuur, house_id))
                updated_verhuur += cursor.rowcount

        except Exception as e:
            print(f"❌ Error processing row {row}: {e}")
            
    conn.commit()
    conn.close()
    
    print("\n✅ Update Complete")
    print(f"   Houses Updated: {updated_houses}")
    print(f"   Inhuur Contracts Updated: {updated_inhuur}")
    print(f"   Verhuur Contracts Updated: {updated_verhuur}")

if __name__ == "__main__":
    update_database()
