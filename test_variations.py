#!/usr/bin/env python3
"""
Test script to generate variation outputs with different usage scenarios
"""

from entities import *
from viewmodels import build_onepager_viewmodel, add_bar_chart_data
from template_renderer import TemplateRenderer
from datetime import date
import os

def create_test_data(borg_used, gwe_used, cleaning_used, scenario_name):
    """Create test data for a specific scenario"""
    
    # Base data
    client = Client(name="Test Family", contact_person="John Test", email="test@example.com", phone="+31612345678")
    object_data = Object(address="Teststraat 123, Amsterdam", object_id="TEST001")
    period = Period(checkin_date=date(2025, 11, 1), checkout_date=date(2025, 11, 8), days=7)
    
    # Deposit
    deposit = Deposit(
        voorschot=500.0,
        gebruikt=borg_used,
        terug=max(0, 500.0 - borg_used),
        restschade=max(0, borg_used - 500.0)
    )
    
    # GWE (Utilities)
    stroom_verbruik = int(gwe_used / 0.30)
    gas_verbruik = int(gwe_used / 1.50)
    
    gwe_meterstanden = GWEMeterstanden(
        stroom=GWEMeterReading(begin=10000, eind=10000 + stroom_verbruik, verbruik=stroom_verbruik),
        gas=GWEMeterReading(begin=5000, eind=5000 + gas_verbruik, verbruik=gas_verbruik)
    )
    
    gwe_regels = [
        GWERegel(omschrijving="Elektriciteit", verbruik_of_dagen=stroom_verbruik, tarief_excl=0.30, kosten_excl=gwe_used * 0.4),
        GWERegel(omschrijving="Gas", verbruik_of_dagen=gas_verbruik, tarief_excl=1.50, kosten_excl=gwe_used * 0.4),
        GWERegel(omschrijving="Water", verbruik_of_dagen=7, tarief_excl=2.00, kosten_excl=gwe_used * 0.2)
    ]
    
    gwe_excl = gwe_used / 1.21
    gwe_btw = gwe_used - gwe_excl
    gwe_totalen = GWETotalen(
        totaal_excl=gwe_excl,
        btw=gwe_btw,
        totaal_incl=gwe_used
    )
    
    # Cleaning
    pakket_type = "5_uur"  # Use literal value
    extra_uren = cleaning_used / 50.0  # €50 per hour
    cleaning = Cleaning(
        pakket_type=pakket_type,  # type: ignore
        voorschot=250.0,
        inbegrepen_uren=5.0,
        totaal_uren=5.0 + extra_uren,
        extra_uren=extra_uren,
        uurtarief=50.0,
        extra_bedrag=cleaning_used
    )
    
    # Damage (always zero for these tests)
    damage_regels = []
    damage_totalen = DamageTotalen(totaal_excl=0.0, btw=0.0, totaal_incl=0.0)
    
    # Settlement
    # Calculate total: positive = amount client gets back, negative = amount client owes
    voorschot_totaal = 500.0 + 250.0 + 250.0  # Borg + GWE + Cleaning prepaid
    gebruikt_totaal = borg_used + gwe_used + cleaning_used
    settlement = Settlement(
        borg=deposit,
        gwe_totalen=gwe_totalen,
        cleaning=cleaning,
        damage_totalen=damage_totalen,
        totaal_eindafrekening=voorschot_totaal - gebruikt_totaal
    )
    
    return {
        'client': client,
        'object': object_data,
        'period': period,
        'deposit': deposit,
        'gwe_meterstanden': gwe_meterstanden,
        'gwe_regels': gwe_regels,
        'gwe_totalen': gwe_totalen,
        'cleaning': cleaning,
        'damage_regels': damage_regels,
        'damage_totalen': damage_totalen,
        'settlement': settlement,
        'scenario_name': scenario_name
    }

def generate_variation(data, output_filename):
    """Generate a onepager for the given data"""
    # Prepare data dict for viewmodel
    data_dict = {
        'client': data['client'],
        'object': data['object'],
        'period': data['period'],
        'borg': data['deposit'],
        'gwe_meterstanden': data['gwe_meterstanden'],
        'gwe_regels': data['gwe_regels'],
        'gwe_totalen': data['gwe_totalen'],
        'cleaning': data['cleaning'],
        'damage_regels': data['damage_regels'],
        'damage_totalen': data['damage_totalen']
    }
    
    viewmodel = build_onepager_viewmodel(data_dict, data['settlement'])
    
    # CRITICAL: Add bar chart SVG data
    viewmodel = add_bar_chart_data(viewmodel)
    
    renderer = TemplateRenderer(template_dir=".")
    html_output = renderer.render_onepager(viewmodel, 'template_onepager.html')
    
    output_dir = "output/variations"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"✓ Generated: {output_path}")
    return output_path

if __name__ == "__main__":
    print("=" * 60)
    print("🎨 GENERATING BAR VARIATIONS")
    print("=" * 60)
    
    scenarios = [
        # (borg_used, gwe_used, cleaning_used, scenario_name, filename)
        (250, 125, 0, "All Underuse (50%)", "1_all_underuse.html"),
        (500, 250, 0, "All Perfect Fit (100%)", "2_all_perfect.html"),
        (550, 275, 50, "Small Overflow (110%)", "3_small_overflow.html"),
        (750, 375, 150, "Large Overflow (150%)", "4_large_overflow.html"),
        (1000, 500, 250, "Extreme Overflow (200%)", "5_extreme_overflow.html"),
        (0, 0, 0, "Zero Usage", "6_zero_usage.html"),
        (250, 275, 150, "Mixed (Under/Over/Over)", "7_mixed_scenario.html"),
    ]
    
    print("\nGenerating variations...\n")
    
    for borg, gwe, cleaning, name, filename in scenarios:
        print(f"📊 {name}")
        data = create_test_data(borg, gwe, cleaning, name)
        generate_variation(data, filename)
        print()
    
    print("=" * 60)
    print("✅ ALL VARIATIONS GENERATED")
    print("=" * 60)
    print(f"\nOpen files in: output/variations/")
    print("Files: 1_all_underuse.html → 7_mixed_scenario.html")

