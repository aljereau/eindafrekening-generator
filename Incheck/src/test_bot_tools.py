import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.bot import RyanRentBot

def test_bot_tools():
    print("🤖 Testing Bot Tools...")
    
    # Load env
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY") or "dummy"
    
    # Init Bot (mocking API key if needed, we just want to test tools)
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Shared', 'database', 'ryanrent_core.db')
    bot = RyanRentBot(api_key, db_path=db_path, provider="openai")
    
    # 1. Test get_upcoming_transitions
    print("\n1. Testing 'get_upcoming_transitions'...")
    result = bot._execute_tool("get_upcoming_transitions", {"days_lookahead": 60})
    
    if isinstance(result, list) and len(result) > 0:
        print(f"✅ Success! Found {len(result)} transitions.")
        print(f"   First item: {result[0]['property']} - {result[0]['client']}")
        if 'details' in result[0]:
            print(f"   Enriched details present: {result[0]['details']}")
        else:
            print("❌ Enriched details MISSING!")
    else:
        print(f"❌ Failed or empty result: {result}")

    # 2. Test generate_planning_report (without filters)
    print("\n2. Testing 'generate_planning_report'...")
    result = bot._execute_tool("generate_planning_report", {"days_lookahead": 60})
    
    if isinstance(result, dict) and result.get('status') == 'success':
        print(f"✅ Success! Report generated at: {result['path']}")
    else:
        print(f"❌ Failed: {result}")

    # 3. Test generate_planning_report with filters (missing pre-inspection)
    print("\n3. Testing 'generate_planning_report' with filters (missing pre-inspection)...")
    report_path = bot._execute_tool("generate_planning_report", {
        "days_lookahead": 30,
        "filters": {"missing_pre_inspection": True}
    })
    if "planning_report" in str(report_path):
        print(f"✅ Success! Filtered report generated at: {report_path}")
    else:
        print(f"❌ Failed: {report_path}")

    # 4. Testing 'update_booking'
    print("\n4. Testing 'update_booking'...")
    # First get a booking to update
    transitions = bot._execute_tool("get_upcoming_transitions", {"days_lookahead": 30})
    if transitions:
        target_booking = transitions[0]
        b_id = target_booking['booking_id']
        old_date = target_booking['date']
        
        # Change date by 1 day
        new_date_obj = datetime.strptime(old_date, "%Y-%m-%d") + timedelta(days=1)
        new_date = new_date_obj.strftime("%Y-%m-%d")
        
        print(f"   Updating Booking {b_id}: {old_date} -> {new_date}")
        
        result = bot._execute_tool("update_booking", {
            "booking_id": b_id,
            "checkout_date": new_date
        })
        
        if result.get("success"):
            print(f"✅ Success! {result['message']}")
            
            # Revert change
            print(f"   Reverting change...")
            bot._execute_tool("update_booking", {
                "booking_id": b_id,
                "checkout_date": old_date
            })
        else:
            print(f"❌ Failed: {result}")
    else:
        print("⚠️ No bookings found to test update.")

    # 5. Test generate_planning_report with filters (has_next_tenant)
    print("\n5. Testing 'generate_planning_report' with filters (has_next_tenant)...")
    filters = {
        "has_next_tenant": True
    }
    result = bot._execute_tool("generate_planning_report", {"days_lookahead": 60, "filters": filters})
    
    if isinstance(result, dict) and result.get('status') == 'success':
        print(f"✅ Success! Filtered report generated at: {result['path']}")
    else:
        print(f"❌ Failed: {result}")

if __name__ == "__main__":
    test_bot_tools()
