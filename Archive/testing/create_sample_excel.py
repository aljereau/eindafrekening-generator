import openpyxl
from openpyxl import Workbook

def create_sample_excel():
    wb = Workbook()
    
    # --- Sheet 1: Hoofdgegevens ---
    ws1 = wb.active
    ws1.title = "Hoofdgegevens"
    
    data1 = [
        ("Gast Naam", "Fam. Jansen"),
        ("Property Naam", "Vakantiewoning Zeezicht"),
        ("Property Adres", "Strandweg 42, Zandvoort"),
        ("Periode Start", "01-08-2023"),
        ("Periode Eind", "12-08-2023"),
        ("Aantal Dagen", 12),
        ("", ""),
        ("BORG", ""),
        ("Borg Voorschot", 800),
        ("Borg Gebruikt", 600),
        ("", ""),
        ("GWE", ""),
        ("GWE Voorschot", 350),
        ("GWE Verbruik Totaal", 450),
        ("Gas Euro", 275),
        ("Water Euro", 75),
        ("Electra Euro", 100),
        ("Electra kWh", 10000),
        ("", ""),
        ("SCHOONMAAK", ""),
        ("Schoonmaak Voorschot", 250),
        ("Schoonmaak Gebruikt", 400),
        ("Schoonmaak Extra", 150),
    ]
    
    for row in data1:
        ws1.append(row)
        
    # --- Sheet 2: Schades Detail ---
    ws2 = wb.create_sheet("Schades Detail")
    
    data2 = [
        ("Schade Omschrijving", "Bedrag"),
        ("Reparatie deur keuken", 30),
        ("Schoonmaak extra keuken", 30),
        ("Vervangen lamp", 25),
        ("Reparatie tegelwerk", 30),
        ("Schoonmaak vloerbedekking", 30),
        ("Reparatie wasmachine", 30),
        ("Vervangen gordijn", 30),
        ("Schilderwerk schade", 30),
        # Total should be around 235, but let's just put sample data
        # The main script uses the total from Sheet 1 for calculation, 
        # and just lists these as details.
    ]
    
    for row in data2:
        ws2.append(row)
    
    wb.save("input.xlsx")
    print("Created input.xlsx")

if __name__ == "__main__":
    create_sample_excel()
