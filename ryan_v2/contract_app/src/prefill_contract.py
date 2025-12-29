
import sqlite3
import re
import subprocess
from pathlib import Path
import argparse
from datetime import datetime

# Path Configuration
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR.parent.parent / "database" / "ryanrent_mock.db"
TEMPLATE_PATH = BASE_DIR / "templates" / "contract_template.md"
OUTPUT_DIR = BASE_DIR / "generated"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def fetch_booking_data(booking_id):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
    SELECT 
        b.id as booking_id,
        b.checkin_datum,
        b.checkout_datum,
        b.totale_huur_factuur,
        b.betaalde_borg,
        h.object_id,
        h.adres as house_adres,
        h.postcode as house_postcode,
        h.plaats as house_plaats,
        h.voorschot_gwe,
        h.eindschoonmaak,
        r.naam as tenant_name,
        r.kvk_nummer,
        r.adres as tenant_adres,
        r.email as tenant_email,
        r.telefoonnummer as tenant_phone,
        r.contactpersoon,
        r.email as tenant_email_invoice
    FROM boekingen b
    JOIN huizen h ON b.object_id = h.object_id
    JOIN relaties r ON b.klant_id = r.id
    WHERE b.id = ?
    """
    
    cursor.execute(query, (booking_id,))
    data = cursor.fetchone()
    conn.close()
    return dict(data) if data else None

def fetch_standalone_data(klant_id, object_id):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Init base data dict
    data = {
        "booking_id": "STANDALONE",
        "checkin_datum": None,
        "checkout_datum": None,
        "totale_huur_factuur": 0,
        "betaalde_borg": 0,
        "object_id": object_id,
        "house_adres": None,
        "house_postcode": None,
        "house_plaats": None,
        "voorschot_gwe": 0,
        "eindschoonmaak": 0,
        "tenant_name": None,
        "kvk_nummer": None,
        "tenant_adres": None,
        "tenant_email": None,
        "tenant_phone": None,
        "contactpersoon": None,
        "tenant_email_invoice": None
    }

    # Fetch House Data
    cursor.execute("SELECT * FROM huizen WHERE object_id = ?", (object_id,))
    house = cursor.fetchone()
    if house:
        data.update({
            "house_adres": house["adres"],
            "house_postcode": house["postcode"],
            "house_plaats": house["plaats"],
            "voorschot_gwe": house["voorschot_gwe"],
            "eindschoonmaak": house["eindschoonmaak"],
            "betaalde_borg": house["borg"]
        })

    # Fetch Relatie Data
    cursor.execute("SELECT * FROM relaties WHERE id = ?", (klant_id,))
    relatie = cursor.fetchone()
    if relatie:
        data.update({
            "tenant_name": relatie["naam"],
            "kvk_nummer": relatie["kvk_nummer"],
            "tenant_adres": relatie["adres"],
            "tenant_email": relatie["email"],
            "tenant_phone": relatie["telefoonnummer"],
            "contactpersoon": relatie["contactpersoon"],
            "tenant_email_invoice": relatie["email"]
        })

    # Optional: Try to find a recent contract for pricing
    cursor.execute("""
        SELECT kale_huur, voorschot_gwe 
        FROM verhuur_contracten 
        WHERE object_id = ? AND klant_id = ? 
        ORDER BY start_datum DESC LIMIT 1
    """, (object_id, klant_id))
    contract = cursor.fetchone()
    if contract:
        data["voorschot_gwe"] = contract["voorschot_gwe"] or 0
        # For pre-filling purposes, we assume totale_huur_factuur is the sum of known components
        data["totale_huur_factuur"] = (contract["kale_huur"] or 0) + (contract["voorschot_gwe"] or 0)
    
    conn.close()
    return data

def format_currency(val):
    if val is None:
        return "0,00"
    try:
        return f"{float(val):.2f}".replace('.', ',')
    except (ValueError, TypeError):
        return "0,00"

def prefill_template(data):
    if not data:
        print("No data found for the given booking ID.")
        return None

    with open(TEMPLATE_PATH, 'r') as f:
        template_content = f.read()

    # Calculate GWE components
    gwe_excl = data["voorschot_gwe"] or 0
    gwe_btw = gwe_excl * 0.21
    gwe_incl = gwe_excl + gwe_btw

    # Calculate Rent components
    total_factuur = data["totale_huur_factuur"] or 0
    rent_excl = total_factuur - gwe_excl
    rent_btw = rent_excl * 0.09
    rent_incl = rent_excl + rent_btw

    # Formatting KVK (remove .0 if it's a float)
    kvk = str(data["kvk_nummer"]) if data["kvk_nummer"] else "[KVK NUMMER]"
    if kvk.endswith(".0"):
        kvk = kvk[:-2]

    # Calculate End of Month
    try:
        start_date = datetime.strptime(data["checkin_datum"], "%Y-%m-%d")
        import calendar
        last_day = calendar.monthrange(start_date.year, start_date.month)[1]
        eind_deze_maand = start_date.replace(day=last_day).strftime("%d %B %Y")
    except:
        eind_deze_maand = "[EIND DATUM MAAND]"

    # Mapping placeholders to data
    replacements = {
        "[DATUM ONDERTEKENING]": datetime.now().strftime("%d %B %Y"),
        "[NAAM HUURDER / BEDRIJF]": data["tenant_name"] or "[NAAM HUURDER]",
        "[KVK NUMMER]": kvk,
        "[ADRES HUURDER]": data["tenant_adres"] or "[ADRES HUURDER]",
        "[TELEFOONNUMMER]": data["tenant_phone"] or "[TELEFOONNUMMER]",
        "[EMAILADRES]": data["tenant_email"] or "[EMAILADRES]",
        "[EMAIL FACTURATIE]": data["tenant_email_invoice"] or "[EMAIL FACTURATIE]",
        "[NAAM VERTEGENWOORDIGER]": data["contactpersoon"] or "[NAAM VERTEGENWOORDIGER]",
        "[ADRES GEHUURDE]": data["house_adres"] or "[ADRES GEHUURDE]",
        "[POSTCODE EN PLAATS GEHUURDE]": f"{data['house_postcode'] or ''} {data['house_plaats'] or ''}".strip() or "[POSTCODE EN PLAATS]",
        "[STARTDATUM]": data["checkin_datum"] or "[STARTDATUM]",
        "[EINDDATUM]": data["checkout_datum"] or "[EINDDATUM]",
        "[JAAR]": datetime.now().year,
        "[JAAR+1]": datetime.now().year + 1,
        "[SCHOONMAAK KOSTEN]": format_currency(data["eindschoonmaak"]),
        "[BORG BEDRAG]": format_currency(data["betaalde_borg"]),
        "[KALE HUUR]": format_currency(rent_excl),
        "[BTW HUUR]": format_currency(rent_btw),
        "[INCL HUUR]": format_currency(rent_incl),
        "[GWE BEDRAG]": format_currency(gwe_excl),
        "[BTW GWE]": format_currency(gwe_btw),
        "[INCL GWE]": format_currency(gwe_incl),
        "[TOTAAL BEDRAG]": format_currency(total_factuur),
        "[TOTAAL EXCL]": format_currency(rent_excl + gwe_excl),
        "[TOTAAL BTW]": format_currency(rent_btw + gwe_btw),
        "[TOTAAL INCL]": format_currency(rent_incl + gwe_incl),
        "[EIND DEZE MAAND]": eind_deze_maand,
        "[PLAATS]": "Oostvoorne",
        "[DATUM]": datetime.now().strftime("%d %B %Y"),
        "[NAAM HUURDER]": data["tenant_name"] or "[NAAM HUURDER]",
    }

    for placeholder, value in replacements.items():
        template_content = template_content.replace(str(placeholder), str(value))

    return template_content

def convert_to_docx(md_content, output_name):
    OUTPUT_DIR.mkdir(exist_ok=True)
    md_file = OUTPUT_DIR / f"{output_name}.md"
    docx_file = OUTPUT_DIR / f"{output_name}.docx"

    with open(md_file, 'w') as f:
        f.write(md_content)

    try:
        subprocess.run(["pandoc", str(md_file), "-o", str(docx_file)], check=True)
        print(f"Contract generated successfully: {docx_file}")
        return docx_file
    except subprocess.CalledProcessError as e:
        print(f"Error during Pandoc conversion: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-fill contract template from database.")
    parser.add_argument("--booking_id", type=int, help="Database ID of the booking.")
    parser.add_argument("--klant_id", type=int, help="Database ID of the client/leverancier.")
    parser.add_argument("--object_id", type=str, help="Object ID of the house (e.g., 0063).")
    args = parser.parse_args()

    data = None
    output_filename = ""

    if args.booking_id:
        print(f"Generating contract for Booking ID: {args.booking_id}...")
        data = fetch_booking_data(args.booking_id)
        output_filename = f"Contract_Booking_{args.booking_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    elif args.klant_id and args.object_id:
        print(f"Generating standalone contract for Klant ID: {args.klant_id} and Object ID: {args.object_id}...")
        data = fetch_standalone_data(args.klant_id, args.object_id)
        output_filename = f"Contract_Klant{args.klant_id}_Huis{args.object_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:
        parser.print_help()
        print("\nError: Please provide either --booking_id OR both --klant_id and --object_id.")
        exit(1)

    if data:
        filled_md = prefill_template(data)
        if filled_md:
            convert_to_docx(filled_md, output_filename)
    else:
        print(f"Could not find sufficient data for the provided parameters.")
