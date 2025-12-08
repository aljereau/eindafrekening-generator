import sqlite3
import pandas as pd
import os
from datetime import datetime

def generate_excel():
    # Determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    db_path = os.path.join(project_root, 'database', 'ryanrent_mock.db')
    output_path = os.path.join(project_root, 'voor_inspecties_invullijst.xlsx')

    print(f"Connecting to database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        
        query = """
        SELECT 
            b.id as "Booking ID",
            h.adres as "Adres",
            h.plaats as "Plaats",
            k.naam as "Klant",
            b.checkout_datum as "Checkout Datum",
            CAST(julianday(b.checkout_datum) - julianday('now') AS INTEGER) as "Dagen tot Checkout"
        FROM boekingen b
        JOIN huizen h ON b.huis_id = h.id
        LEFT JOIN relaties k ON b.klant_id = k.id
        WHERE b.status = 'active'
        AND b.checkout_datum >= date('now')
        AND b.checkout_datum <= date('now', '+60 days')
        AND NOT EXISTS (
            SELECT 1 
            FROM inspections i 
            WHERE i.booking_id = b.id 
            AND i.inspection_type = 'voor_inspectie'
        )
        ORDER BY b.checkout_datum ASC
        """
        
        print("Executing query...")
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("No bookings found requiring pre-inspection.")
            return

        # Add empty columns for user input
        df['Inspectie Datum'] = ''
        df['Inspecteur'] = ''
        df['Notities'] = ''

        print(f"Found {len(df)} bookings. Generating Excel...")
        
        # Create Excel writer with formatting
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Te Plannen Inspecties')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Te Plannen Inspecties']
            for idx, col in enumerate(df.columns):
                max_len = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = max_len

        print(f"Successfully created: {output_path}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    generate_excel()
