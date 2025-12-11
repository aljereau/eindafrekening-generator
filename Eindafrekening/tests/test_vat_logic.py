
import unittest
from datetime import date
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Shared')))

from entities import Period, GWERegel
from generate import preprocess_gwe_tax_changes

class TestVATLogic(unittest.TestCase):
    def test_water_split_2026(self):
        # Period spanning 2025-2026
        # Dec 22, 2025 to Jan 11, 2026 (20 days total)
        # 10 days in 2025 (Dec 22-31 + Jan 1 is transition)
        # Wait, checkin Dec 22, checkout Jan 11.
        # Days = 20.
        # Transition Jan 1.
        # Days 2025: Dec 22 to Jan 1 = 10 days? (31-22+1 = 10).
        # Days 2026: Jan 1 to Jan 11 = 10 days?
        # Let's verify logic in generate.py:
        # days_2025 = (transition_date - checkin).days
        # days_2026 = (checkout - transition_date).days
        
        checkin = date(2025, 12, 22)
        checkout = date(2026, 1, 11)
        period = Period(checkin, checkout, 20)
        
        # Water line
        water_regel = GWERegel(
            omschrijving="Waterverbruik",
            verbruik_of_dagen=20, # 20 days
            tarief_excl=1.0,
            kosten_excl=20.0,
            btw_percentage=0.09,
            type="Water",
            eenheid="Dagen"
        )
        
        # Other line
        other_regel = GWERegel(
            omschrijving="Elektra",
            verbruik_of_dagen=100,
            tarief_excl=0.5,
            kosten_excl=50.0,
            btw_percentage=0.21,
            type="Elektra",
            eenheid="kWh"
        )
        
        data = {
            'period': period,
            'gwe_regels': [water_regel, other_regel]
        }
        
        # Run split
        preprocess_gwe_tax_changes(data)
        
        regels = data['gwe_regels']
        
        # Should have 3 lines now (Water 2025, Water 2026, Elektra)
        self.assertEqual(len(regels), 3)
        
        # Verify Water 2025
        w2025 = regels[0]
        self.assertIn("2025", w2025.omschrijving)
        self.assertAlmostEqual(w2025.verbruik_of_dagen, 10.0)
        self.assertAlmostEqual(w2025.kosten_excl, 10.0)
        self.assertEqual(w2025.btw_percentage, 0.09)
        
        # Verify Water 2026
        w2026 = regels[1]
        self.assertIn("2026", w2026.omschrijving)
        self.assertAlmostEqual(w2026.verbruik_of_dagen, 10.0)
        self.assertAlmostEqual(w2026.kosten_excl, 10.0)
        self.assertEqual(w2026.btw_percentage, 0.21)
        
        # Verify Elektra unchanged
        elek = regels[2]
        self.assertEqual(elek.omschrijving, "Elektra")
        self.assertEqual(elek.kosten_excl, 50.0)

if __name__ == '__main__':
    unittest.main()
