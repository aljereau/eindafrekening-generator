#!/usr/bin/env python3
"""
RyanRent Eindafrekening Generator - V2.0
Generates visual eindafrekening PDFs from Excel template

Complete rebuild with modular architecture:
- excel_reader.py: Reads Excel using named ranges
- calculator.py: Business logic calculations
- viewmodels.py: Transform to OnePager and Detail formats
- template_renderer.py: Jinja2 HTML rendering
- pdf_generator.py: PDF conversion with HTML fallback

Output: 2 PDFs (or HTML fallback) - OnePager + Detail
"""

import argparse
import os
import sys
from datetime import datetime

# Import modules
from excel_reader import read_excel
from calculator import recalculate_all
from viewmodels import build_viewmodels_from_data, save_viewmodels_to_json
from template_renderer import TemplateRenderer
from pdf_generator import render_and_generate_pdfs


def build_output_basename(client_name: str, checkin_date: str, checkout_date: str) -> str:
    """
    Build output filename base from client info
    
    Args:
        client_name: Client name
        checkin_date: Check-in date string
        checkout_date: Check-out date string
        
    Returns:
        Safe filename base (e.g., "eindafrekening_jansen_2024-08-01_2024-08-13")
    """
    # Sanitize client name for filename
    safe_name = client_name.lower().replace(' ', '_').replace('.', '').replace(',', '')
    
    # Remove "fam." prefix if present
    if safe_name.startswith('fam_'):
        safe_name = safe_name[4:]
    
    # Build filename
    basename = f"eindafrekening_{safe_name}_{checkin_date}_{checkout_date}"
    
    return basename


def main():
    """Main generator function - orchestrates the complete flow"""
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='RyanRent Eindafrekening Generator V2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate.py                           # Use default input_template.xlsx
  python generate.py --input custom.xlsx       # Use custom Excel file
  python generate.py --no-pause                # Non-interactive mode
  python generate.py --save-json               # Save intermediate JSON files
        """
    )
    parser.add_argument('--input', default='input_template.xlsx',
                       help='Path to Excel input file (default: input_template.xlsx)')
    parser.add_argument('--output-dir', default='output',
                       help='Output directory for generated files (default: output)')
    parser.add_argument('--no-pause', action='store_true',
                       help='Skip pause at end (for scripts)')
    parser.add_argument('--save-json', action='store_true',
                       help='Save intermediate JSON viewmodels')
    parser.add_argument('--html-only', action='store_true',
                       help='Skip PDF generation, only create HTML')
    
    args = parser.parse_args()
    
    # Print header
    print("\n" + "=" * 70)
    print("🏠 RyanRent Eindafrekening Generator V2.0")
    print("=" * 70)
    
    try:
        # ==================== STEP 1: READ EXCEL ====================
        print(f"\n📊 STAP 1: Excel data inlezen...")
        print(f"   Bestand: {args.input}")
        
        if not os.path.exists(args.input):
            raise FileNotFoundError(f"Excel bestand '{args.input}' niet gevonden.")
        
        data = read_excel(args.input)
        
        print(f"   ✓ Client: {data['client'].name}")
        print(f"   ✓ Object: {data['object'].address}")
        print(f"   ✓ Periode: {data['period'].checkin_date} → {data['period'].checkout_date}")
        print(f"   ✓ GWE regels: {len(data['gwe_regels'])}")
        print(f"   ✓ Schade regels: {len(data['damage_regels'])}")
        
        # ==================== STEP 2: CALCULATIONS ====================
        print(f"\n🔢 STAP 2: Berekeningen uitvoeren...")
        
        # Get GWE voorschot from Excel (should be read by excel_reader)
        # For now, we'll need to add this to the reader or pass it manually
        # Let's read it from the Excel reader's get_named_value
        from excel_reader import ExcelReader
        with ExcelReader(args.input) as reader:
            gwe_voorschot = reader.get_float('Voorschot_GWE', default=0.0)
        
        data['gwe_voorschot'] = gwe_voorschot
        
        # Add logo (base64 encoded)
        import base64
        logo_path = os.path.join('assets', 'ryanrent_co.jpg')
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                data['logo_b64'] = f"data:image/jpeg;base64,{encoded_string}"
        else:
            data['logo_b64'] = None
            print(f"   ⚠️  Logo niet gevonden: {logo_path}")
        
        # Validate Excel calculations against Python logic
        from calculator import validate_excel_calculations
        validation_warnings = validate_excel_calculations(data)
        
        if validation_warnings:
            print(f"\n   ⚠️  WAARSCHUWING: Excel formulas komen niet overeen met verwachte berekeningen:")
            for warning in validation_warnings:
                print(f"      • {warning}")
            print(f"\n   Python zal alle waarden herberekenen en corrigeren...")
        
        # Recalculate everything to ensure consistency
        data = recalculate_all(data)
        
        # Calculate net settlement amount for display
        from calculator import Calculator
        calc = Calculator()
        settlement = calc.calculate_settlement(
            borg=data['deposit'],
            gwe_voorschot=gwe_voorschot,
            gwe_totalen=data['gwe_totalen'],
            cleaning=data['cleaning'],
            damage_totalen=data['damage_totalen']
        )
        
        print(f"   ✓ Borg terug: €{data['deposit'].terug:.2f}")
        print(f"   ✓ GWE totaal: €{data['gwe_totalen'].totaal_incl:.2f}")
        print(f"   ✓ Schoonmaak extra: €{data['cleaning'].extra_bedrag:.2f}")
        print(f"   ✓ Schade totaal: €{data['damage_totalen'].totaal_incl:.2f}")
        
        netto_msg = "terug" if settlement.totaal_eindafrekening >= 0 else "bijbetalen"
        print(f"   ✓ NETTO: €{abs(settlement.totaal_eindafrekening):.2f} {netto_msg}")
        
        # ==================== STEP 3: BUILD VIEWMODELS ====================
        print(f"\n🏗️  STAP 3: ViewModels genereren...")
        
        onepager_vm, detail_vm = build_viewmodels_from_data(data)
        
        print(f"   ✓ OnePager viewmodel gebouwd")
        print(f"   ✓ Detail viewmodel gebouwd")
        
        # Save JSON if requested
        if args.save_json:
            save_viewmodels_to_json(
                onepager_vm, 
                detail_vm,
                onepager_path=os.path.join(args.output_dir, "onepager.json"),
                detail_path=os.path.join(args.output_dir, "detail.json")
            )
        
        # ==================== STEP 4: RENDER HTML ====================
        print(f"\n🎨 STAP 4: HTML templates renderen...")
        
        renderer = TemplateRenderer(template_dir=".")
        
        try:
            onepager_html = renderer.render_onepager(onepager_vm)
            print(f"   ✓ OnePager HTML gegenereerd")
        except Exception as e:
            print(f"   ⚠️  OnePager template fout: {e}")
            print(f"      Zorg dat 'template_onepager.html' bestaat.")
            raise
        
        try:
            detail_html = renderer.render_detail(detail_vm)
            print(f"   ✓ Detail HTML gegenereerd")
        except Exception as e:
            print(f"   ⚠️  Detail template fout: {e}")
            print(f"      Zorg dat 'template_detail.html' bestaat.")
            raise
        
        # ==================== STEP 5: GENERATE OUTPUT ====================
        print(f"\n📄 STAP 5: Output genereren...")
        
        # Build output basename
        basename = build_output_basename(
            data['client'].name,
            str(data['period'].checkin_date),
            str(data['period'].checkout_date)
        )
        
        # Generate PDFs (or HTML fallback)
        result = render_and_generate_pdfs(
            onepager_html=onepager_html,
            detail_html=detail_html,
            output_dir=args.output_dir,
            basename=basename,
            base_url="."
        )
        
        # ==================== SUMMARY ====================
        print(f"\n" + "=" * 70)
        print("✅ GENERATIE VOLTOOID!")
        print("=" * 70)
        
        print(f"\n📂 Output bestanden:")
        
        # OnePager
        if result['onepager']['is_pdf']:
            print(f"   ✓ OnePager PDF: {result['onepager']['pdf']}")
        else:
            print(f"   ⚠️  OnePager HTML: {result['onepager']['html']} (PDF niet beschikbaar)")
        
        # Detail
        if result['detail']['is_pdf']:
            print(f"   ✓ Detail PDF: {result['detail']['pdf']}")
        else:
            print(f"   ⚠️  Detail HTML: {result['detail']['html']} (PDF niet beschikbaar)")
        
        # Show absolute paths
        output_dir_abs = os.path.abspath(args.output_dir)
        print(f"\n📍 Locatie: {output_dir_abs}")
        
        # Summary
        print(f"\n💰 Eindafrekening samenvatting:")
        print(f"   Client: {data['client'].name}")
        print(f"   Periode: {data['period'].days} dagen")
        netto = settlement.totaal_eindafrekening
        if netto >= 0:
            print(f"   ✓ Terug naar klant: €{netto:.2f}")
        else:
            print(f"   ✓ Bijbetaling klant: €{abs(netto):.2f}")
        
        print(f"\n✨ Gereed voor verzending naar klant!")
        
    except FileNotFoundError as e:
        print(f"\n❌ FOUT: {e}")
        print(f"   Controleer of het bestand bestaat en het pad correct is.")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ ONVERWACHTE FOUT: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Pause if interactive
    if not args.no_pause:
        input("\n👉 Druk op Enter om af te sluiten...")


if __name__ == "__main__":
    main()
