import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import date

# Adjust path to find master_reader
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '../src')
sys.path.append(src_dir)

# We need to ensure master_reader can import 'database'
# It adds Shared to path, but we can also mock it to be safe
# But since we want to test the logic inside, we can let it import if possible, 
# or mock sys.modules 'database' if we don't want real DB dependency.

# Let's mock database module to avoid path issues or real DB usage
sys.modules['database'] = MagicMock()

from master_reader import MasterReader

class TestGWETotals(unittest.TestCase):
    def test_gwe_totals_calculation(self):
        # Mock database class in master_reader namespace if needed (already mocked module)
        # But master_reader creates self.db = Database()
        
        # Instantiate reader
        reader = MasterReader("dummy.xlsx")
        
        # Override process_booking_rows dependencies if any
        # It calls _fetch_property_details, we should mock it
        reader._fetch_property_details = MagicMock(return_value={
            'object_id': 'OBJ-001', 'postcode': '1000AA', 'plaats': 'TestCity'
        })
        
        # Construct Rows
        # Row size padding 50 
        def create_row(type_val, **kwargs):
            row = [None] * 50
            row[0] = "TestAdres"
            row[1] = type_val
            
            # Helper to map kwargs to indices (based on master_reader logic)
            # Basis: 7:Checkin, 8:Checkout, 9:Borg
            if type_val == "Basis":
                row[7] = kwargs.get('checkin', date(2024,1,1))
                row[8] = kwargs.get('checkout', date(2024,1,10))
                
            # GWE_Item: 34:Type, 36:Desc, 37:Aant, 38:Prijs, 39:TotEx, 40:BTW
            if type_val == "GWE_Item":
                row[34] = kwargs.get('type', 'Overig')
                row[36] = kwargs.get('desc', 'Desc')
                row[37] = kwargs.get('qty', 0)
                row[38] = kwargs.get('price', 0)
                row[39] = kwargs.get('total_excl', 0)
                row[40] = kwargs.get('btw', 0.21)
                
            return tuple(row)
            
        rows = []
        rows.append(create_row("Basis"))
        
        # Item 1: 10.00 Excl
        rows.append(create_row("GWE_Item", desc="Item 1", total_excl=10.0, btw=0.21))
        
        # Item 2: 20.00 Excl
        rows.append(create_row("GWE_Item", desc="Item 2", total_excl=20.0, btw=0.21))
        
        # Execute
        result = reader._process_booking_rows("TestAdres", rows)
        
        # Check result
        self.assertIsNotNone(result)
        gwe_totalen = result['gwe_totalen']
        
        print(f"Result Totals: Excl={gwe_totalen.totaal_excl}, Incl={gwe_totalen.totaal_incl}")
        
        # Assertions
        # 10 + 20 = 30.0
        self.assertEqual(gwe_totalen.totaal_excl, 30.0, "Total Excl should be sum of items")
        # 30 * 1.21 = 36.3
        self.assertAlmostEqual(gwe_totalen.totaal_incl, 36.3, places=2, msg="Total Incl should include BTW")

if __name__ == '__main__':
    unittest.main()
