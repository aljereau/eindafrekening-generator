import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import shutil

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.bot import RyanRentBot

from dotenv import load_dotenv

def test_file_exchange():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY") or "dummy_key"
    
    print("🤖 Initializing Bot...")
    bot = RyanRentBot(api_key=api_key, provider="openai") # Provider doesn't matter for tool execution
    
    print("\n1. Testing 'generate_excel_template' (Checkout Update)...")
    result = bot._execute_tool("generate_excel_template", {
        "template_type": "checkout_update"
    })
    
    if result.get("success"):
        template_path = result['message'].split(": ")[1].split(". Please")[0]
        print(f"✅ Template generated: {template_path}")
        
        # Verify file exists
        if os.path.exists(template_path):
            print("   File exists on disk.")
            
            # 2. Simulate User Input
            print("\n2. Simulating User Input...")
            df = pd.read_excel(template_path)
            
            if not df.empty:
                # Update the first row
                target_booking_id = df.iloc[0]['BookingID']
                current_date = df.iloc[0]['CurrentCheckout']
                new_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
                
                print(f"   Modifying Booking {target_booking_id}: {current_date} -> {new_date}")
                
                df.at[0, 'NewCheckout'] = new_date
                
                # Save to Input folder
                input_filename = "filled_update.xlsx"
                input_path = os.path.join(bot.file_exchange.input_dir, input_filename)
                df.to_excel(input_path, index=False)
                print(f"   Saved filled file to: {input_path}")
                
                # 3. Process File
                print("\n3. Testing 'process_excel_update'...")
                process_result = bot._execute_tool("process_excel_update", {
                    "filename": input_filename,
                    "request_type": "checkout_update"
                })
                
                print(f"   Result: {process_result}")
                
                if process_result.get("success_count", 0) > 0:
                    print("✅ Processing successful!")
                else:
                    print("❌ Processing failed or no rows updated.")
                    
            else:
                print("⚠️ Template is empty, cannot test update.")
        else:
            print("❌ File not found on disk.")
    else:
        print(f"❌ Failed to generate template: {result}")

if __name__ == "__main__":
    test_file_exchange()
