import sqlite3
import os

db_path = '/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/database/ryanrent_mock.db'

try:
    if not os.path.exists(db_path):
        print(f"File not found: {db_path}")
        exit(1)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables in {db_path}:")
    for table in tables:
        print(table[0])
        
        if table[0] == 'RentalProperty':
            print(f"\nSchema for {table[0]}:")
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            for col in columns:
                print(col)
        
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
