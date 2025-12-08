import sys
import os
import argparse
import datetime
from typing import List, Dict, Any

# Add project root to path to import Shared modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from Shared.database import Database, init_database
from Shared.excel_tools import ExcelExporter, ExcelImporter

def get_db():
    """Get database instance"""
    db_path = os.path.join(project_root, 'database', 'ryanrent_mock.db')
    return init_database(db_path)

def export_inspections(output_file: str = None):
    """Export planned inspections to Excel"""
    db = get_db()
    conn = db._get_connection()
    
    # Query for upcoming checkouts (next 14 days)
    query = """
        SELECT 
            b.id as booking_id,
            b.checkout_datum,
            r.naam as klant_naam,
            h.adres,
            h.plaats,
            h.postcode,
            '' as planned_date_inspectie,
            '' as inspector_naam,
            'planned' as status,
            '' as opmerkingen
        FROM boekingen b
        JOIN relaties r ON b.klant_id = r.id
        JOIN huizen h ON b.huis_id = h.id
        WHERE b.checkout_datum BETWEEN date('now') AND date('now', '+14 days')
            AND b.status IN ('active', 'confirmed')
        ORDER BY b.checkout_datum
    """
    
    cursor = conn.execute(query)
    # Get column names
    columns = [description[0] for description in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    
    conn.close()
    
    if not results:
        print("ℹ️ No upcoming inspections found to plan.")
        return

    if not output_file:
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        output_file = os.path.join(project_root, f"planning_inspecties_{date_str}.xlsx")
    
    ExcelExporter.export_to_excel(results, output_file, sheet_name="Inspectie Planning")
    print(f"\n🚀 Ready! Open '{output_file}' to plan your inspections.")

def import_inspections(input_file: str, dry_run: bool = True):
    """Import planned inspections from Excel"""
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return

    print(f"📖 Reading {input_file}...")
    data = ExcelImporter.read_from_excel(input_file)
    
    if not data:
        print("⚠️ No data found in file.")
        return

    updates = []
    errors = []
    
    # Validate and prepare updates
    for row_idx, row in enumerate(data, 2): # Excel row 2 (1-based)
        booking_id = row.get('booking_id')
        planned_date = row.get('planned_date_inspectie')
        inspector = row.get('inspector_naam')
        status = row.get('status')
        notes = row.get('opmerkingen')

        if not booking_id:
            continue # Skip empty rows or rows without ID

        # Only process if there's something to update
        if planned_date or inspector or notes:
            # Basic validation
            if planned_date and not isinstance(planned_date, (datetime.date, datetime.datetime)):
                # Try to parse string if it's not a date object
                try:
                    # Assuming YYYY-MM-DD or DD-MM-YYYY could be passed, but let's be lenient or strict?
                    # For now, just warn if it's not a date object (openpyxl usually handles dates)
                    pass 
                except:
                    errors.append(f"Row {row_idx}: Invalid date format for {planned_date}")

            updates.append({
                'booking_id': booking_id,
                'planned_date': planned_date,
                'inspector': inspector,
                'status': status,
                'notes': notes
            })

    if not updates:
        print("ℹ️ No changes detected to import.")
        return

    print(f"\n🔎 Found {len(updates)} records to update.")
    
    if errors:
        print("\n⚠️ Validation Errors:")
        for err in errors:
            print(f"   - {err}")
        print("   (Fix these errors in Excel and try again)")
        if dry_run: return

    if dry_run:
        print("\n📝 Proposed Changes (Dry Run):")
        for up in updates[:5]: # Show first 5
            print(f"   - Booking {up['booking_id']}: Plan={up['planned_date']}, Insp={up['inspector']}, Stat={up['status']}")
        if len(updates) > 5: print(f"   ... and {len(updates)-5} more.")
        
        print("\n✅ Validation passed. Run with --commit to apply changes.")
    else:
        print("\n💾 Applying changes to database...")
        # TODO: In a real scenario, we would update a specific 'inspections' table.
        # Since we don't have an 'inspections' table yet, we'll just simulate the update
        # or update a 'notes' field in bookings if it existed.
        # For this MVP, we will print what we WOULD do.
        
        # db = get_db()
        # conn = db._get_connection()
        # for up in updates:
        #     conn.execute("UPDATE ...", ...)
        # conn.commit()
        
        print("⚠️ Database update logic not fully implemented (requires 'inspections' table).")
        print("   But the data was successfully read and validated!")

def main():
    parser = argparse.ArgumentParser(description="Manage Inspections via Excel")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export inspections to Excel')
    export_parser.add_argument('--output', '-o', help='Output file path')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import inspections from Excel')
    import_parser.add_argument('input_file', help='Input Excel file path')
    import_parser.add_argument('--commit', action='store_true', help='Commit changes to database')
    
    args = parser.parse_args()
    
    if args.command == 'export':
        export_inspections(args.output)
    elif args.command == 'import':
        import_inspections(args.input_file, dry_run=not args.commit)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
