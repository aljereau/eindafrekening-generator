#!/usr/bin/env python3
"""
Verification script for RyanRent Eindafrekening Generator
Tests specific scenarios:
1. No Cleaning Package
2. Extra Voorschot
"""

import os
import sys
import shutil
from excel_reader import read_excel
from calculator import recalculate_all, Calculator
from viewmodels import build_viewmodels_from_data
from template_renderer import TemplateRenderer
from entities import ExtraVoorschot, Cleaning

def generate_output(data, output_subdir):
    """Generate HTML output for the given data"""
    output_dir = os.path.join('output', output_subdir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Build viewmodels
    onepager_vm, detail_vm = build_viewmodels_from_data(data)
    
    # Render HTML
    renderer = TemplateRenderer(template_dir=".")
    onepager_html = renderer.render_onepager(onepager_vm)
    detail_html = renderer.render_detail(detail_vm)
    
    # Save HTML files
    with open(os.path.join(output_dir, "onepager.html"), "w") as f:
        f.write(onepager_html)
        
    with open(os.path.join(output_dir, "detail.html"), "w") as f:
        f.write(detail_html)
        
    print(f"   ✓ Generated output in {output_dir}")

def test_no_cleaning():
    print("\n🧪 TEST 1: No Cleaning Package")
    
    # Read fresh data
    data = read_excel('input_template.xlsx')
    
    # Modify for no cleaning
    old_cleaning = data['cleaning']
    data['cleaning'] = Cleaning(
        pakket_type='geen',
        pakket_naam='Geen pakket',
        inbegrepen_uren=0.0,
        totaal_uren=0.0,
        extra_uren=0.0,
        uurtarief=old_cleaning.uurtarief,
        extra_bedrag=0.0,
        voorschot=0.0
    )
    
    # Recalculate
    data = recalculate_all(data)
    
    # Calculate settlement for verification
    calc = Calculator()
    settlement = calc.calculate_settlement(
        borg=data['deposit'],
        gwe_voorschot=data.get('gwe_voorschot', 0.0), # Might be missing if not in excel reader
        gwe_totalen=data['gwe_totalen'],
        cleaning=data['cleaning'],
        damage_totalen=data['damage_totalen'],
        extra_voorschot=data.get('extra_voorschot')
    )
    
    print(f"   Cleaning Package: {data['cleaning'].pakket_type}")
    print(f"   Cleaning Cost: €{data['cleaning'].extra_bedrag}")
    
    generate_output(data, "test_no_cleaning")

def test_extra_voorschot():
    print("\n🧪 TEST 2: Extra Voorschot")
    
    # Read fresh data
    data = read_excel('input_template.xlsx')
    
    # Inject extra voorschot
    data['extra_voorschot'] = ExtraVoorschot(
        voorschot=150.0,
        omschrijving='Tuinonderhoud',
        gebruikt=50.0,
        terug=100.0,
        restschade=0.0
    )
    
    # Recalculate
    data = recalculate_all(data)
    
    print(f"   Extra Voorschot: €{data['extra_voorschot'].voorschot}")
    print(f"   Omschrijving: {data['extra_voorschot'].omschrijving}")
    print(f"   Terug: €{data['extra_voorschot'].terug}")
    
    generate_output(data, "test_extra_voorschot")

def main():
    print("🚀 Starting Verification Tests...")
    
    # Ensure input file exists
    if not os.path.exists('input_template.xlsx'):
        print("❌ Error: input_template.xlsx not found")
        return
        
    try:
        test_no_cleaning()
        test_extra_voorschot()
        print("\n✅ Verification Complete!")
        print(f"Open output/test_no_cleaning/onepager.html to verify no cleaning logic")
        print(f"Open output/test_extra_voorschot/onepager.html to verify extra voorschot logic")
        
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
