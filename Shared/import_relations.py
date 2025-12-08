import pandas as pd
import sys
import os

# Add parent directory to path to import database
# Script is in Shared/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_database

def import_relations(excel_path):
    print(f"🚀 Starting import from {excel_path}")
    
    # Initialize DB (runs migrations)
    db = init_database()
    
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"❌ Error reading Excel: {e}")
        return

    print(f"📊 Found {len(df)} rows")
    
    count = 0
    updated = 0
    
    for index, row in df.iterrows():
        try:
            if pd.isna(row['Code']):
                continue
                
            code = int(row['Code'])
            naam = str(row['Naam']).strip()
            
            # Map columns
            kwargs = {
                'adres': str(row['Adres']) if pd.notna(row['Adres']) else None,
                'postcode': str(row['Postcode']) if 'Postcode' in df.columns and pd.notna(row['Postcode']) else None,
                'plaats': str(row['Plaats']) if pd.notna(row['Plaats']) else None,
                'land': str(row['Land']) if pd.notna(row['Land']) else None,
                'email': str(row['E-mailadres']) if pd.notna(row['E-mailadres']) else None,
                'iban': str(row['Bankrekening']) if pd.notna(row['Bankrekening']) else None,
                'kvk_nummer': str(row['Kamer van Koophandel']) if pd.notna(row['Kamer van Koophandel']) else None,
                'is_klant': 1 if str(row['Klant']).strip() == 'V' else 0,
                'is_leverancier': 1 if str(row['Leverancier']).strip() == 'V' else 0
            }
            
            db.upsert_relation(code, naam, **kwargs)
            count += 1
            
        except Exception as e:
            print(f"⚠️  Error processing row {index}: {e}")
            
    print(f"✅ Successfully imported/updated {count} relations.")

if __name__ == "__main__":
    # Path relative to project root (assuming run from project root)
    # Or absolute path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Shared/Sources/Klant+Leverancier.xlsx
    source_path = os.path.join(script_dir, "Sources", "Klant+Leverancier.xlsx")
    
    if not os.path.exists(source_path):
        # Try relative to CWD
        source_path = "Shared/Sources/Klant+Leverancier.xlsx"
        
    if os.path.exists(source_path):
        import_relations(source_path)
    else:
        print(f"❌ Source file not found: {source_path}")
