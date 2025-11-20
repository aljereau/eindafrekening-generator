#!/usr/bin/env python3
"""
Test script for pot-based bar visualization with edge cases

Tests all scenarios:
- Zero usage
- Low/medium/high underuse
- Perfect fit
- Small/large/extreme overflow
"""

import sys
from datetime import date
from entities import (
    Client, Object, Period, Deposit, GWEMeterReading, GWERegel,
    GWETotalen, Cleaning, DamageRegel, DamageTotalen, GWEMeterstanden
)
from viewmodels import build_viewmodels_from_data
from template_renderer import TemplateRenderer
import os


def create_test_case(name: str, borg_pot: float, borg_used: float, 
                     gwe_pot: float, gwe_used: float,
                     clean_pot: float, clean_used: float) -> dict:
    """Create a test case with specified values"""
    
    # Calculate derived values
    borg_terug = max(0, borg_pot - borg_used)
    gwe_terug = max(0, gwe_pot - gwe_used)
    gwe_extra = max(0, gwe_used - gwe_pot)
    
    # For cleaning, used represents total euros (pot + extra if overfilled)
    if clean_used <= clean_pot:
        clean_terug = clean_pot - clean_used
        clean_extra = 0
        clean_total_hours = 5 * (clean_used / clean_pot) if clean_pot > 0 else 0
    else:
        clean_terug = 0
        clean_extra = clean_used - clean_pot
        clean_total_hours = 5 + (clean_extra / 50)  # Assuming €50/hr extra
    
    return {
        'name': name,
        'client': Client(
            name=f"Test Case: {name}",
            contact_person="Test User",
            email="test@example.com",
            phone="06-12345678"
        ),
        'object': Object(
            address="Teststraat 123",
            unit="A1",
            postal_code="1234AB",
            city="Teststad",
            object_id="TEST-001"
        ),
        'period': Period(
            checkin_date=date(2024, 8, 1),
            checkout_date=date(2024, 8, 15),
            days=14
        ),
        'deposit': Deposit(
            voorschot=borg_pot,
            gebruikt=borg_used,
            terug=borg_terug,
            restschade=0
        ),
        'gwe_meterstanden': GWEMeterstanden(
            stroom=GWEMeterReading(begin=10000, eind=10500, verbruik=500),
            gas=GWEMeterReading(begin=5000, eind=5100, verbruik=100)
        ),
        'gwe_regels': [
            GWERegel("Stroom", 500, 0.28, 140),
            GWERegel("Gas", 100, 1.15, 115)
        ],
        'gwe_totalen': GWETotalen(
            totaal_excl=gwe_used / 1.21,
            btw=gwe_used - (gwe_used / 1.21),
            totaal_incl=gwe_used
        ),
        'gwe_voorschot': gwe_pot,
        'cleaning': Cleaning(
            pakket_type="5_uur",
            inbegrepen_uren=5,
            totaal_uren=clean_total_hours,
            extra_uren=max(0, clean_total_hours - 5),
            uurtarief=50,
            extra_bedrag=clean_extra,
            voorschot=clean_pot
        ),
        'damage_regels': [],
        'damage_totalen': DamageTotalen(totaal_excl=0, btw=0, totaal_incl=0)
    }


def run_tests():
    """Run all test cases"""
    
    print("=" * 80)
    print("🧪 POT-BASED BAR VISUALIZATION TEST SUITE")
    print("=" * 80)
    
    # Initialize template renderer
    renderer = TemplateRenderer()
    
    test_cases = [
        # Test 1: Zero usage (€800 pot, €0 used)
        create_test_case(
            "Zero Usage",
            borg_pot=800, borg_used=0,
            gwe_pot=350, gwe_used=0,
            clean_pot=250, clean_used=0
        ),
        
        # Test 2: Low usage (€800 pot, €50 used)
        create_test_case(
            "Low Underuse",
            borg_pot=800, borg_used=50,
            gwe_pot=350, gwe_used=45,
            clean_pot=250, clean_used=30
        ),
        
        # Test 3: Medium usage (€350 pot, €90 used)
        create_test_case(
            "Medium Underuse",
            borg_pot=350, borg_used=90,
            gwe_pot=350, gwe_used=180,
            clean_pot=250, clean_used=125
        ),
        
        # Test 4: High usage (€250 pot, €230 used)
        create_test_case(
            "High Underuse",
            borg_pot=250, borg_used=230,
            gwe_pot=250, gwe_used=235,
            clean_pot=250, clean_used=245
        ),
        
        # Test 5: Perfect fit (€250 pot, €250 used)
        create_test_case(
            "Perfect Fit",
            borg_pot=250, borg_used=250,
            gwe_pot=250, gwe_used=250,
            clean_pot=250, clean_used=250
        ),
        
        # Test 6: Small overflow (€250 pot, €275 used)
        create_test_case(
            "Small Overflow",
            borg_pot=250, borg_used=250,  # Borg doesn't overflow
            gwe_pot=250, gwe_used=275,
            clean_pot=250, clean_used=275
        ),
        
        # Test 7: Large overflow (€250 pot, €450 used)
        create_test_case(
            "Large Overflow",
            borg_pot=250, borg_used=250,  # Borg doesn't overflow
            gwe_pot=250, gwe_used=450,
            clean_pot=250, clean_used=450
        ),
        
        # Test 8: Extreme overflow (€100 pot, €5000 used)
        create_test_case(
            "Extreme Overflow",
            borg_pot=100, borg_used=100,  # Borg doesn't overflow
            gwe_pot=100, gwe_used=5000,
            clean_pot=100, clean_used=5000
        ),
    ]
    
    # Ensure output directory exists
    os.makedirs("output/test_cases", exist_ok=True)
    
    for i, test_data in enumerate(test_cases, 1):
        test_name = test_data['name']
        print(f"\n{'=' * 80}")
        print(f"Test {i}: {test_name}")
        print(f"{'=' * 80}")
        
        # Print test values
        print(f"\n📊 Test Values:")
        print(f"   BORG:     Pot €{test_data['deposit'].voorschot:.0f} | Used €{test_data['deposit'].gebruikt:.0f}")
        print(f"   GWE:      Pot €{test_data['gwe_voorschot']:.0f} | Used €{test_data['gwe_totalen'].totaal_incl:.0f}")
        print(f"   CLEANING: Pot €{test_data['cleaning'].voorschot:.0f} | Used €{(test_data['cleaning'].voorschot + test_data['cleaning'].extra_bedrag):.0f}")
        
        # Build viewmodels
        onepager_vm, detail_vm = build_viewmodels_from_data(test_data)
        
        # Print generated captions
        print(f"\n💬 Generated Captions:")
        print(f"   BORG:     {onepager_vm['financial']['borg']['caption']}")
        print(f"   GWE:      {onepager_vm['financial']['gwe']['caption']}")
        print(f"   CLEANING: {onepager_vm['financial']['cleaning']['caption']}")
        
        # Render templates
        onepager_html = renderer.render_onepager(onepager_vm)
        
        # Save test case HTML
        test_filename = test_name.lower().replace(" ", "_")
        onepager_path = f"output/test_cases/{test_filename}_onepager.html"
        
        with open(onepager_path, 'w', encoding='utf-8') as f:
            f.write(onepager_html)
        
        print(f"\n✅ Saved: {onepager_path}")
    
    print(f"\n{'=' * 80}")
    print("✅ ALL TESTS COMPLETED!")
    print(f"{'=' * 80}")
    print(f"\n📂 Test results saved to: output/test_cases/")
    print(f"   Open the HTML files in your browser to verify visual appearance")
    print(f"\n🔍 What to check:")
    print(f"   • All BORG/GWE/CLEANING bars should be exactly 400px wide (pot size)")
    print(f"   • Overflow bars should show pot (400px) + small extension (50px)")
    print(f"   • Captions should be human-readable and match the scenario")
    print(f"   • Visual consistency across all test cases")


if __name__ == "__main__":
    run_tests()

