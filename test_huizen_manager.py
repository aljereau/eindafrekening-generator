from datetime import date
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from HuizenManager.src.manager import HuizenManager
from Shared.entities import Huis, Eigenaar, InhuurContract

def test_huizen_manager():
    print("--- Testing HuizenManager ---")
    manager = HuizenManager()
    
    # 1. Add Owner
    print("\n1. Adding Owner...")
    eigenaar = Eigenaar(
        id=None,
        naam="Test Eigenaar BV",
        email="test@eigenaar.nl",
        telefoonnummer="0612345678",
        iban="NL99BANK0123456789"
    )
    eigenaar_id = manager.add_eigenaar(eigenaar)
    print(f"   -> Added Owner ID: {eigenaar_id}")
    
    # 2. Add House
    print("\n2. Adding House...")
    huis = Huis(
        id=None,
        object_id="TEST-001",
        address="Teststraat 1",
        postal_code="1234AB",
        city="Teststad",
        property_type="Appartement",
        surface_area=85.5,
        bedrooms=2,
        capacity=4,
        status="active"
    )
    huis_id = manager.add_huis(huis)
    print(f"   -> Added House ID: {huis_id}")
    
    # 3. Add Contract
    print("\n3. Adding Contract...")
    contract = InhuurContract(
        id=None,
        property_id=huis_id,
        eigenaar_id=eigenaar_id,
        start_date=date(2024, 1, 1),
        end_date=None,
        kale_huur=1000.0,
        servicekosten=50.0,
        voorschot_gwe=150.0,
        totale_huur=1200.0
    )
    contract_id = manager.add_contract(contract)
    print(f"   -> Added Contract ID: {contract_id}")
    
    # 4. Verify Retrieval
    print("\n4. Verifying Retrieval...")
    retrieved_huis = manager.get_huis(huis_id)
    active_contract = manager.get_active_contract(huis_id)
    
    print(f"   -> Retrieved House: {retrieved_huis.address} (ID: {retrieved_huis.object_id})")
    if active_contract:
        print(f"   -> Active Contract Rent: €{active_contract.totale_huur}")
        print(f"   -> Contract Start Date: {active_contract.start_date}")
    else:
        print("   -> ❌ No active contract found!")

    if retrieved_huis.object_id == "TEST-001" and active_contract.totale_huur == 1200.0:
        print("\n✅ TEST PASSED")
    else:
        print("\n❌ TEST FAILED")

if __name__ == "__main__":
    test_huizen_manager()
