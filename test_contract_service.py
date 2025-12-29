
from ryan_v2.contract_service import ContractService

service = ContractService()

# 1. Test Dropdown Data
print("Fetching dropdown data...")
data = service.get_dropdown_data()
print(f"Clients: {len(data['clients'])}")
print(f"Houses: {len(data['houses'])}")

# 2. Test Prefill
if data['clients'] and data['houses']:
    cid = data['clients'][0]['id']
    oid = data['houses'][0]['object_id']
    print(f"\nTesting prefill for Client {cid} and House {oid}...")
    result = service.get_prefilled_contract(cid, oid)
    if result:
        print("Prefill successful.")
        print("Preview (First 500 chars):")
        print(result['markdown'][:500])
    else:
        print("Prefill failed (no result).")
else:
    print("Could not find clients or houses to test prefill.")
