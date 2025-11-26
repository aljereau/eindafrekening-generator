import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.intelligence_api import IntelligenceAPI

def run_tests():
    print("🤖 Testing Intelligence API with Mock Data...")
    
    # Use the Mock DB
    api = IntelligenceAPI("database/ryanrent_mock.db")
    
    # 1. Status Overview
    print("\n📊 1. Status Overview")
    stats = api.get_status_overview()
    print(f"   - Total Houses: {stats['total_houses']}")
    print(f"   - Occupied Now: {stats['occupied_houses']}")
    print(f"   - Expiring Contracts: {stats['expiring_contracts']}")
    print(f"   - Missing Checkouts: {stats['missing_checkouts']}")
    
    # 2. Expiring Contracts
    print("\n⏳ 2. Expiring Contracts (Next 30 days)")
    expiring = api.get_houses_near_contract_end(30)
    if expiring:
        for item in expiring[:5]: # Show top 5
            print(f"   - {item['adres']} (Ends: {item['end_date']})")
        if len(expiring) > 5: print(f"   ... and {len(expiring)-5} more.")
    else:
        print("   (None)")
        
    # 3. Missing Checkouts
    print("\n👻 3. Missing Checkouts")
    missing = api.get_bookings_without_checkout()
    if missing:
        for item in missing[:5]:
            print(f"   - Booking {item['booking_id']}: {item['adres']} (Ended: {item['checkout_datum']})")
        if len(missing) > 5: print(f"   ... and {len(missing)-5} more.")
    else:
        print("   (None)")
        
    # 4. Open Deposits
    print("\n💰 4. Open Deposits by Client")
    deposits = api.get_open_deposits_by_client()
    if deposits:
        for item in deposits[:5]:
            print(f"   - {item['client']}: €{item['open_balance']:.2f} ({item['active_deposit_count']} active)")
        if len(deposits) > 5: print(f"   ... and {len(deposits)-5} more.")
    else:
        print("   (None)")

if __name__ == "__main__":
    run_tests()
