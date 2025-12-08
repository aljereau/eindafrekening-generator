import openpyxl
import sqlite3
import re
from collections import defaultdict

EXCEL_PATH = '/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/Shared/Sources/Houses List.xlsx'
DB_PATH = '/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/database/ryanrent_mock.db'

def get_street_name(address):
    """Extract street name from address (remove house number)"""
    if not address:
        return ""
    # Match everything up to the last digit sequence
    match = re.match(r"^(.*?)\s*\d+", address)
    if match:
        return match.group(1).strip()
    return address

def update_properties():
    print(f"🚀 Starting Property Update...")
    print(f"📂 Excel: {EXCEL_PATH}")
    print(f"💾 Database: {DB_PATH}")

    # 1. Read Excel Data
    try:
        wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
        sheet = wb.active
        
        # Map headers
        headers = {}
        for idx, cell in enumerate(sheet[1]):
            if cell.value:
                headers[cell.value] = idx
        
        print(f"📋 Found headers: {list(headers.keys())}")
        
        required_cols = ['OBJECT', 'Straat en huisnummer', 'Postcode', 'Plaats']
        for col in required_cols:
            if col not in headers:
                print(f"❌ Missing required column: {col}")
                return

        # Read all rows
        rows = []
        street_counts = defaultdict(int)
        
        for row in sheet.iter_rows(min_row=2, values_only=True):
            obj_id = row[headers['OBJECT']]
            if not obj_id:
                continue
                
            address = row[headers['Straat en huisnummer']]
            if not address:
                print(f"⚠️  Skipping Object {obj_id}: Missing address")
                continue
                
            street = get_street_name(str(address))
            street_counts[street] += 1
            
            data = {
                'object_id': str(obj_id),
                'adres': address,
                'postcode': row[headers['Postcode']] or "",
                'plaats': row[headers['Plaats']] or "",
                'kluis_1': row[headers.get('Kluis 1')] if 'Kluis 1' in headers else None,
                'kluis_2': row[headers.get('Kluis 2')] if 'Kluis 2' in headers else None,
                'street_name': street
            }
            rows.append(data)
            
        print(f"📊 Read {len(rows)} properties from Excel.")
        
        # 2. Update Database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        updated_count = 0
        inserted_count = 0
        
        for row in rows:
            # Determine woning_type
            woning_type = 'Appartement'
            if street_counts[row['street_name']] > 1:
                woning_type = 'Vakantiepark'
            
            # Check if exists
            cursor.execute("SELECT id FROM huizen WHERE object_id = ?", (row['object_id'],))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE huizen 
                    SET adres = ?, postcode = ?, plaats = ?, woning_type = ?, kluis_code_1 = ?, kluis_code_2 = ?, gewijzigd_op = CURRENT_TIMESTAMP
                    WHERE object_id = ?
                """, (row['adres'], row['postcode'], row['plaats'], woning_type, row['kluis_1'], row['kluis_2'], row['object_id']))
                updated_count += 1
            else:
                cursor.execute("""
                    INSERT INTO huizen (object_id, adres, postcode, plaats, woning_type, kluis_code_1, kluis_code_2, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
                """, (row['object_id'], row['adres'], row['postcode'], row['plaats'], woning_type, row['kluis_1'], row['kluis_2']))
                inserted_count += 1
                
        conn.commit()
        conn.close()
        
        print(f"✅ Update Complete!")
        print(f"   - Updated: {updated_count}")
        print(f"   - Inserted: {inserted_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_properties()
