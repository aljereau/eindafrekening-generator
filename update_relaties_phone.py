#!/usr/bin/env python3
"""
Update relaties table with phone numbers from CSV
"""
import csv
import sqlite3
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "Shared/Sources/excel_data/data-checker-for database-updating.csv"
DB_FILE = BASE_DIR / "database/ryanrent_v2.db"

def update_phone_numbers():
    """Read CSV and update relaties table with phone numbers"""
    
    # Read CSV data
    phone_data = {}
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            relatie_id = row.get('relatie_id', '').strip()
            telefoon = row.get('Telefoonnummer', '').strip()
            
            # Only add if we have both relatie_id and a non-zero phone number
            if relatie_id and telefoon and telefoon != '0':
                phone_data[relatie_id] = telefoon
    
    print(f"📊 Found {len(phone_data)} phone numbers to update")
    
    # Update database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    updated_count = 0
    for relatie_id, telefoon in phone_data.items():
        cursor.execute("""
            UPDATE relaties 
            SET telefoonnummer = ? 
            WHERE id = ?
        """, (telefoon, relatie_id))
        
        if cursor.rowcount > 0:
            updated_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated {updated_count} relaties with phone numbers")
    print(f"📱 Phone data will now appear in export_sales_data.py output")
    
if __name__ == "__main__":
    update_phone_numbers()
