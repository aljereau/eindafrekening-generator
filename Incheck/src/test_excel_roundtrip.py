import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.bot import RyanRentBot

def test_excel_roundtrip():
    print("🤖 Testing Excel Roundtrip Workflow...")
    
    # Initialize Bot
    # Using core db as we are testing the real flow (or mock if preferred, but let's use core for now as it has data)
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_core.db')
    bot = RyanRentBot(api_key="test_key", db_path=db_path)
    
    # 1. Generate Excel
    print("\n1. Generating Excel Export...")
    # filters = {"missing_pre_inspection": True} # Commented out to ensure we get data
    result = bot._execute_tool("generate_planning_excel", {"days_lookahead": 60})
    
    if result.get('status') != 'success':
        print(f"❌ Generation Failed: {result}")
        return
        
    excel_path = result['path']
    print(f"✅ Excel generated at: {excel_path}")
    
    # 2. Simulate User Editing
    print("\n2. Simulating User Edits...")
    df = pd.read_excel(excel_path)
    
    if df.empty:
        print("⚠️ Excel is empty! Cannot test update.")
        return
        
    # Pick the first row and update inspection
    first_row_idx = df.index[0]
    booking_id = int(df.at[first_row_idx, 'Booking ID'])
    
    new_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
    new_inspector = "Jessica Test"
    
    print(f"   Updating Booking {booking_id}: Voorinspectie on {new_date} by {new_inspector}")
    
    df.at[first_row_idx, 'Voorinspectie Datum'] = new_date
    df.at[first_row_idx, 'Voorinspectie Inspecteur'] = new_inspector
    
    # Save back
    df.to_excel(excel_path, index=False)
    print("✅ Excel file updated.")
    
    # 3. Import Update
    print("\n3. Importing Updates...")
    update_result = bot._execute_tool("update_planning_from_excel", {"file_path": excel_path})
    print(f"✅ Import Result: {update_result['message']}")
    
    # 4. Verify Database
    print("\n4. Verifying Database...")
    conn = bot.api._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT geplande_datum, inspecteur 
        FROM inspecties 
        WHERE boeking_id = ? AND inspectie_type = 'voorinspectie'
    """, (booking_id,))
    
    row = cursor.fetchone()
    if row:
        db_date = row[0]
        db_inspector = row[1]
        print(f"   DB Data: Date={db_date}, Inspector={db_inspector}")
        
        if db_date == new_date and db_inspector == new_inspector:
            print("✅ Verification Successful! Database matches Excel update.")
        else:
            print("❌ Verification Failed! Data mismatch.")
    else:
        print("❌ Verification Failed! No inspection record found.")
        
    conn.close()

if __name__ == "__main__":
    test_excel_roundtrip()
