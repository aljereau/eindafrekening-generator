import sqlite3
import calendar
import base64
import os
from datetime import datetime
from pathlib import Path
from .contract_app.src.prefill_contract import get_db_connection, fetch_standalone_data, format_currency

BASE_DIR = Path(__file__).parent / "contract_app"
TEMPLATE_PATH = BASE_DIR / "templates" / "contract_template.md"

class ContractService:
    def __init__(self):
        pass

    def get_dropdown_data(self):
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Fetch Klanten (Relaties)
        cursor.execute("SELECT id, naam FROM relaties ORDER BY naam ASC")
        klanten = [dict(row) for row in cursor.fetchall()]
        
        # Fetch Huizen
        cursor.execute("SELECT object_id, adres, plaats FROM huizen WHERE status = 'active' ORDER BY object_id ASC")
        huizen = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return {"clients": klanten, "houses": huizen}

    def get_prefilled_contract(self, klant_id, object_id, overrides=None):
        data = fetch_standalone_data(klant_id, object_id)
        if not data:
            return None
        
        if overrides:
            data.update(overrides)

        # Refresh calculations if overrides provided
        total_factuur = float(data.get("totale_huur_factuur") or 0)
        gwe_excl = float(data.get("voorschot_gwe") or 0)
        
        rent_excl = total_factuur - gwe_excl
        rent_btw = rent_excl * 0.09
        rent_incl = rent_excl + rent_btw
        
        gwe_btw = gwe_excl * 0.21
        gwe_incl = gwe_excl + gwe_btw

        # Formatting KVK
        kvk = str(data["kvk_nummer"]) if data["kvk_nummer"] else "[KVK NUMMER]"
        if kvk.endswith(".0"):
            kvk = kvk[:-2]

        # Month end logic
        eind_deze_maand = "[EIND DATUM MAAND]"
        if data.get("checkin_datum"):
            try:
                start_date = datetime.strptime(data["checkin_datum"], "%Y-%m-%d")
                last_day = calendar.monthrange(start_date.year, start_date.month)[1]
                eind_deze_maand = start_date.replace(day=last_day).strftime("%d %B %Y")
            except:
                pass

        # Handle Logo Base64
        assets_dir = Path(__file__).parent.parent / "Eindafrekening" / "assets"
        logo_path = assets_dir / "ryanrent_co1.jpg"
        if not logo_path.exists():
            logo_path = assets_dir / "ryanrent_co.jpg"
            
        logo_base64 = ""
        if logo_path.exists():
            with open(logo_path, "rb") as image_file:
                logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        
        logo_md = f"data:image/jpeg;base64,{logo_base64}" if logo_base64 else ""

        replacements = {
            "[LOGO_BASE64]": logo_md,
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

        with open(TEMPLATE_PATH, 'r') as f:
            content = f.read()

        for placeholder, value in replacements.items():
            content = content.replace(placeholder, str(value))

        return {
            "markdown": content,
            "data": data # Return data for form sync
        }

    def list_generated_contracts(self):
        """Lists all files in the ryan_v2/contracts directory."""
        contracts_dir = Path(__file__).parent / "contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)
        
        files = []
        for entry in os.scandir(contracts_dir):
            if entry.is_file():
                stats = entry.stat()
                files.append({
                    "name": entry.name,
                    "size": stats.st_size,
                    "created": stats.st_ctime
                })
        
        # Sort by creation time, newest first
        files.sort(key=lambda x: x['created'], reverse=True)
        return {"contracts": files}

    def get_contract_file_path(self, filename: str):
        """Returns the absolute path to a contract file if it exists."""
        contracts_dir = Path(__file__).parent / "contracts"
        file_path = contracts_dir / filename
        
        # Security check
        if ".." in filename or "/" in filename:
            return None
            
        return file_path

    def save_contract(self, filename: str, content: str):
        """Saves a contract markdown to a file."""
        contracts_dir = Path(__file__).parent / "contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure extension
        if not filename.endswith('.md'):
            filename += '.md'
            
        file_path = contracts_dir / filename
        with open(file_path, 'w') as f:
            f.write(content)
        return True


