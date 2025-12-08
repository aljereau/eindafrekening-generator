import pandas as pd
import sys
import os
from datetime import datetime, date

# Add parent directory to path to import database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import init_database

def import_payments(excel_path):
    print(f"🚀 Starting Payment Import from {excel_path}")
    db = init_database()
    conn = db.get_connection()
    
    try:
        # Read Excel, skipping header rows
        df = pd.read_excel(excel_path, header=None, skiprows=12)
        
        current_client_id = None
        snapshot_date = date.today()
        count = 0
        
        for index, row in df.iterrows():
            col0 = str(row[0]).strip() if pd.notna(row[0]) else ""
            col1 = row[1]
            
            # Debug
            if index < 20:
               print(f"Row {index}: Col0='{col0}', Col1='{col1}'")

            # 1. Detect Client Header
            # Format: "Name - ID" in Col 0, Col 1 is NaN
            if pd.isna(col1) and ' - ' in str(col0):
                try:
                    # Extract ID from end of string
                    parts = str(col0).strip().rsplit(' - ', 1)
                    if len(parts) == 2:
                        possible_id = parts[1].strip()
                        if possible_id.isdigit():
                            current_client_id = int(possible_id)
                            # print(f"   👤 Found Client: {current_client_id}")
                except ValueError:
                    pass
                continue
                
            # 2. Detect Invoice Row
            # Col 0 is Invoice Nr (numeric), Col 1 is Date
            if str(col0).isdigit() and pd.notna(col1) and str(col1) != 'Subtotaal':
                if current_client_id is None:
                    continue
                    
                try:
                    invoice_nr = str(col0)
                    factuur_datum = row[1]
                    verval_datum = row[6]
                    oorspronkelijk = float(row[9]) if pd.notna(row[9]) else 0.0
                    openstaand = float(row[10]) if pd.notna(row[10]) else 0.0
                    
                    # Handle dates
                    if isinstance(factuur_datum, datetime):
                        factuur_datum = factuur_datum.date()
                    if isinstance(verval_datum, datetime):
                        verval_datum = verval_datum.date()
                        
                    # Calculate stats
                    dagen_openstaand = 0
                    status = 'Open'
                    
                    if openstaand > 0:
                        if verval_datum and snapshot_date > verval_datum:
                            dagen_openstaand = (snapshot_date - verval_datum).days
                            status = 'Te Laat'
                    else:
                        status = 'Betaald'

                    # Insert
                    conn.execute("""
                        INSERT INTO debiteuren_standen (
                            relatie_id, factuur_nummer, factuur_datum, verval_datum,
                            oorspronkelijk_bedrag, openstaand_bedrag, 
                            dagen_openstaand, status, snapshot_datum
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        current_client_id, invoice_nr, factuur_datum, verval_datum,
                        oorspronkelijk, openstaand, dagen_openstaand, status, snapshot_date
                    ))
                    count += 1
                    
                except Exception as e:
                    print(f"   ⚠️ Error parsing row {index}: {e}")
                    continue

        conn.commit()
        print(f"✅ Successfully imported {count} payment records.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Default path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(script_dir, "Sources", "Copy of RyanRent Debiteuren Saldo per 24-11-2025.xlsx")
    
    if not os.path.exists(source_path):
        # Try relative
        source_path = "Shared/Sources/Copy of RyanRent Debiteuren Saldo per 24-11-2025.xlsx"
        
    if os.path.exists(source_path):
        import_payments(source_path)
    else:
        print(f"❌ Source file not found: {source_path}")
