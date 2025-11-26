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

# Add current directory to path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Add Shared directory to path (2 levels up from src: src -> Eindafrekening -> Root -> Shared)
# Actually, src is inside Eindafrekening, so:
# __file__ = .../Eindafrekening/src/generate.py
# dirname = .../Eindafrekening/src
# dirname(dirname) = .../Eindafrekening
# dirname(dirname(dirname)) = .../Root
# Shared = .../Root/Shared
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
shared_dir = os.path.join(root_dir, 'Shared')
sys.path.append(shared_dir)

# Import modules
from excel_reader import read_excel
from calculator import recalculate_all
from viewmodels import build_viewmodels_from_data, save_viewmodels_to_json
from template_renderer import TemplateRenderer
from pdf_generator import render_and_generate_pdfs
from database import init_database


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
    
    # Determine project root
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        # sys.executable is the path to the .exe
        # We want the folder containing the .exe
        application_path = os.path.dirname(sys.executable)
        project_root = application_path
        
        # In frozen mode, assets are in sys._MEIPASS
        # But we want input/output to be relative to the exe (project_root)
        # However, default templates/assets might be bundled.
        # Let's assume input/output are local to exe, but templates are internal.
        bundle_dir = sys._MEIPASS
    else:
        # Running from source
        # __file__ = .../Eindafrekening/src/generate.py
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bundle_dir = project_root
    
    # Default paths
    # Input/Output should be relative to where the user runs the app (project_root)
    default_input = os.path.join(project_root, 'input_template.xlsx')
    default_output = os.path.join(project_root, 'output')
    
    # Assets/Templates might be in the bundle (if frozen) or project root (if source)
    # But wait, we want the user to be able to edit input_template.xlsx? 
    # Yes, so input_template should be external.
    # Templates are internal (bundled).
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='RyanRent Eindafrekening Generator V2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/generate.py                           # Use default input_template.xlsx
  python src/generate.py --input custom.xlsx       # Use custom Excel file
  python src/generate.py --no-pause                # Non-interactive mode
  python src/generate.py --save-json               # Save intermediate JSON files
        """
    )
    parser.add_argument('--input', default=default_input,
                       help=f'Path to Excel input file (default: {default_input})')
    parser.add_argument('--output-dir', default=default_output,
                       help=f'Output directory for generated files (default: {default_output})')
    parser.add_argument('--no-pause', action='store_true',
                       help='Skip pause at end (for scripts)')
    parser.add_argument('--save-json', action='store_true',
                       help='Save intermediate JSON viewmodels')
    parser.add_argument('--html-only', action='store_true',
                       help='Skip PDF generation, only create HTML')
    parser.add_argument('--auto-open', action='store_true',
                       help='Auto-open generated HTML files in browser')

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
            # Fallback to current working directory if not found
            local_input = 'input_template.xlsx'
            if os.path.exists(local_input):
                print(f"   ⚠️  Niet gevonden op verwachte locatie, gebruik lokaal bestand: {local_input}")
                args.input = local_input
            else:
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
        from excel_reader import ExcelReader
        with ExcelReader(args.input) as reader:
            gwe_voorschot = reader.get_float('Voorschot_GWE', default=0.0)
        
        data['gwe_voorschot'] = gwe_voorschot
        
        # Add logo (base64 encoded)
        import base64
        # Logo is bundled, so use bundle_dir
        logo_path = os.path.join(bundle_dir, 'assets', 'ryanrent_co.jpg')
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
            damage_totalen=data['damage_totalen'],
            extra_voorschot=data.get('extra_voorschot')
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
        
        # Templates are bundled, so use bundle_dir
        template_dir = os.path.join(bundle_dir, 'templates')
        renderer = TemplateRenderer(template_dir=template_dir)
        
        try:
            onepager_html = renderer.render_onepager(onepager_vm)
            print(f"   ✓ OnePager HTML gegenereerd")
        except Exception as e:
            print(f"   ⚠️  OnePager template fout: {e}")
            print(f"      Zorg dat 'templates/template_onepager.html' bestaat.")
            raise
        
        try:
            detail_html = renderer.render_detail(detail_vm)
            print(f"   ✓ Detail HTML gegenereerd")
        except Exception as e:
            print(f"   ⚠️  Detail template fout: {e}")
            print(f"      Zorg dat 'templates/template_detail.html' bestaat.")
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
            base_url=project_root  # Base URL for assets
        )
        
        # ==================== STEP 6: SAVE TO DATABASE ====================
        print(f"\n💾 STAP 6: Opslaan in database...")
        
        try:
            # Database is now in Shared/database
            db_path = os.path.join(shared_dir, 'database', 'ryanrent_core.db')
            db = init_database(db_path)
            
            # Determine version
            version, is_new = db.get_next_version(
                data['client'].name,
                data['period'].checkin_date,
                data['period'].checkout_date
            )
            
            # Prepare data for storage (convert viewmodel to dict)
            # For simplicity, we store the raw data dict + settlement info
            storage_data = {
                'client': str(data['client']),
                'period': str(data['period']),
                'settlement': str(settlement)
            }
            
            # Save
            db.save_eindafrekening(
                client_name=data['client'].name,
                checkin_date=data['period'].checkin_date,
                checkout_date=data['period'].checkout_date,
                version=version,
                version_reason="Generated via script",
                data_json=storage_data,
                object_address=data['object'].address,
                period_days=data['period'].days,
                borg_terug=data['deposit'].terug,
                gwe_totaal_incl=data['gwe_totalen'].totaal_incl,
                totaal_eindafrekening=settlement.totaal_eindafrekening,
                file_path=result['onepager']['pdf'] if result['onepager']['is_pdf'] else result['onepager']['html']
            )
            
        except Exception as e:
            print(f"   ⚠️  Kon niet opslaan in database: {e}")
        
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

        # Auto-open in browser if requested
        if args.auto_open:
            import webbrowser
            print(f"\n🌐 Browser openen...")

            # Open OnePager
            if result['onepager']['html']:
                onepager_path = os.path.abspath(result['onepager']['html'])
                webbrowser.open(f'file://{onepager_path}')
                print(f"   ✓ OnePager geopend")

            # Open Detail
            if result['detail']['html']:
                detail_path = os.path.abspath(result['detail']['html'])
                webbrowser.open(f'file://{detail_path}')
                print(f"   ✓ Detail geopend")

            print(f"\n💡 TIP: Gebruik Cmd+P (Mac) of Ctrl+P (Windows) om te printen")
            print(f"         Kies 'Opslaan als PDF' in het printvenster")
        
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
