import openpyxl
import sqlite3
import os

# Configuration
EXCEL_PATH = '/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/Shared/Sources/Houses List.xlsx'
DB_PATH = 'database/ryanrent_core.db'

def update_properties():
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ Excel file not found: {EXCEL_PATH}")
        return

    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return

    print(f"📂 Reading Excel: {EXCEL_PATH}")
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    sheet = wb.active

    print(f"📂 Connecting to Database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updated_count = 0
    not_found_count = 0
    skipped_count = 0

    # Iterate rows, skipping header
    for i, row in enumerate(sheet.iter_rows(values_only=True)):
        if i == 0:
            continue  # Skip header

        # Extract data (Columns: OBJECT, Straat, Postcode, Plaats, Kluis 1, Kluis 2)
        object_id_raw = row[0]
        adres = row[1]
        postcode = row[2]
        plaats = row[3]
        kluis_1 = row[4]
        kluis_2 = row[5]

        if not object_id_raw:
            continue

        object_id = str(object_id_raw).strip()
        
        # Normalize data
        adres = str(adres).strip() if adres else None
        postcode = str(postcode).strip() if postcode else None
        plaats = str(plaats).strip() if plaats else None
        kluis_1 = str(kluis_1).strip() if kluis_1 else None
        kluis_2 = str(kluis_2).strip() if kluis_2 else None

        # Check if property exists
        cursor.execute("SELECT id FROM huizen WHERE object_id = ?", (object_id,))
        result = cursor.fetchone()

        if result:
            # Update property
            try:
                cursor.execute("""
                    UPDATE huizen 
                    SET adres = ?, postcode = ?, plaats = ?, kluis_code_1 = ?, kluis_code_2 = ?, gewijzigd_op = CURRENT_TIMESTAMP
                    WHERE object_id = ?
                """, (adres, postcode, plaats, kluis_1, kluis_2, object_id))
                updated_count += 1
                print(f"✅ Updated {object_id}: {adres}, {postcode} {plaats}")
            except Exception as e:
                print(f"❌ Error updating {object_id}: {e}")
        else:
            print(f"⚠️  Property not found in DB: {object_id} ({adres})")
            not_found_count += 1

    conn.commit()
    conn.close()

    print("\n========================================")
    print(f"✨ Update Complete")
    print(f"   Updated: {updated_count}")
    print(f"   Not Found: {not_found_count}")
    print("========================================")

if __name__ == "__main__":
    update_properties()
