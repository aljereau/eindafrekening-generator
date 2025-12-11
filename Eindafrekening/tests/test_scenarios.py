
import sys
import os
from datetime import date
import logging

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Shared')))

from entities import (
    Client, RentalProperty, Period, Deposit, GWEMeterReading, GWERegel,
    GWETotalen, Cleaning, DamageRegel, DamageTotalen, GWEMeterstanden
)
from generate import generate_eindafrekening_from_data

def run_scenarios():
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../output/test_scenarios'))
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"🚀 Running Test Scenarios...")
    print(f"📂 Output directory: {output_dir}")

    # ==================== SCENARIO 1: 2026 VAT SPLIT ====================
    print("\n🧪 Scenario 1: 2026 Water VAT Split")
    
    client1 = Client("Fam. Test 2026", "Jan Test", "jan@test.com", "0612345678")
    period1 = Period(date(2025, 12, 22), date(2026, 1, 11), 20) # 20 days
    
    data1 = {
        'client': client1,
        'object': RentalProperty("Toekomstlaan 1", "A1", "1000AA", "Amsterdam", "OBJ-2026"),
        'period': period1,
        'deposit': Deposit(500, 0, 500, 0),
        'gwe_meterstanden': GWEMeterstanden(
            stroom=GWEMeterReading(1000, 1100, 100),
            gas=GWEMeterReading(500, 550, 50),
            water=GWEMeterReading(100, 120, 20)
        ),
        'gwe_regels': [
            GWERegel("Waterverbruik", 20, 1.0, 20.0, 0.09, "Water", "m3"), # Should split
            GWERegel("Elektra", 100, 0.5, 50.0, 0.21, "Elektra", "kWh")
        ],
        'gwe_totalen': GWETotalen(70, 12.3, 82.3), # Dummy totals, will be recalculated
        'gwe_voorschot': 100.0,
        'cleaning': Cleaning("geen", "Geen pakket", 0, 0, 0, 50, 0, 0, 0.21),
        'damage_regels': [],
        'damage_totalen': DamageTotalen(0, 0, 0),
        'extra_voorschot': None
    }
    
    try:
        # We need to mock bundle_dir and shared_dir
        bundle_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        shared_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Shared'))
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        
        generate_eindafrekening_from_data(
            data1, output_dir, bundle_dir, shared_dir, project_root, save_json=True
        )
        print("✅ Scenario 1 completed")
    except Exception as e:
        print(f"❌ Scenario 1 failed: {e}")
        import traceback
        traceback.print_exc()

    # ==================== SCENARIO 2: NEW COLUMNS & CLEANING VAT ====================
    print("\n🧪 Scenario 2: New Columns & Cleaning VAT")
    
    client2 = Client("Fam. Details", "Piet Precies", "piet@test.com", "0687654321")
    period2 = Period(date(2025, 6, 1), date(2025, 6, 15), 14)
    
    data2 = {
        'client': client2,
        'object': RentalProperty("Detailstraat 5", "B2", "2000BB", "Rotterdam", "OBJ-DTL"),
        'period': period2,
        'deposit': Deposit(800, 100, 700, 0),
        'gwe_meterstanden': GWEMeterstanden(
            stroom=GWEMeterReading(2000, 2200, 200),
            gas=GWEMeterReading(1000, 1050, 50)
        ),
        'gwe_regels': [
            GWERegel("Gas verbruik", 50, 1.20, 60.0, 0.21, "Gas", "m3"),
            GWERegel("Vaste levering water", 14, 2.50, 35.0, 0.09, "Water", "Dagen"),
            GWERegel("Elektra verbruik", 200, 0.30, 60.0, 0.21, "Elektra", "kWh"),
            GWERegel("Overige kosten", 1, 10.0, 10.0, 0.21, "Overig", "Stuk")
        ],
        'gwe_totalen': GWETotalen(165, 30, 195), # Dummy
        'gwe_voorschot': 200.0,
        'cleaning': Cleaning(
            "5_uur", "Basis Schoonmaak", 5, 7, 2, 50, 100, 250, 0.21
        ),
        'damage_regels': [
            DamageRegel("Gebroken glas", 1, 15, 15, 0.21)
        ],
        'damage_totalen': DamageTotalen(15, 3.15, 18.15),
        'extra_voorschot': None
    }
    
    try:
        generate_eindafrekening_from_data(
            data2, output_dir, bundle_dir, shared_dir, project_root, save_json=True
        )
        print("✅ Scenario 2 completed")
    except Exception as e:
        print(f"❌ Scenario 2 failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_scenarios()
