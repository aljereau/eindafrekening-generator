
import openpyxl
from datetime import date
import os
import sys

# Add scripts path to import create_master_template
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from create_master_template import create_master_template

def create_test_data():
    # Generate fresh template
    output_path = "Eindafrekening/input_master_test.xlsx"
    create_master_template(output_path)
    
    wb = openpyxl.load_workbook(output_path)
    ws = wb.active
    
    # Existing Address (from DB scan earlier)
    # We'll use a likely existing address or just a string if DB fallback used
    adres = "Zuidzijde 13" # Looking at previous file view, this might exist or "Voorstraat 10"
    
    # Row 2: Basis
    # 0:Adres, 1:Type, 2:Klant, 3:ObjID
    # 4:In, 5:Out, 6:Borg, 7:GWE_Type, 8:Meter, 9:Prov, 10:Contr, 11:ExVr, 12:ExDesc
    ws.append([
        adres, "Basis", "Test Klant BV", "OBJ-001",
        date(2024,1,1), date(2024,1,31), 500.00,
        "Via RyanRent", "Liander", "Vattenfall", "C-123",
        100.00, "Extra Borgtb"
    ])
    
    # Row 3: GWE
    # Cols N-S (Indices 13-18): ElB, ElE, GaB, GaE, WaB, WaE
    # Padding A-M (13 cols)
    ws.append([
        adres, "GWE"
    ] + [None]*11 + [
        1000, 1100, 500, 550, 200, 210
    ])
    
    # Row 4: Schoonmaak
    # Cols T-Z (Indices 19-25)
    # 19:Pakket, 20:Uren, 21:Tarief, 22:TotEx, 23:BTW%, 24:BTW€, 25:TotInc
    # Padding A-S (19 cols)
    ws.append([
        adres, "Schoonmaak"
    ] + [None]*17 + [
        "Basis Schoonmaak", 5, 50.00, None, 0.21
    ])
    
    # Row 5: GWE Item
    # Cols AA-AI (Indices 26-34)
    # 26:Type, 27:Unit, 28:Desc, 29:Aant, 30:Prijs, 31:Ex, 32:BTW%, 33:BTW, 34:Inc
    # Padding A-Z (26 cols)
    ws.append([
        adres, "GWE_Item"
    ] + [None]*24 + [
        "Water", "mnd", "Vaste Levering", 1, 10.00, None, 0.09
    ])
    
    # Row 6: Schade
    # Same columns as GWE Item
    ws.append([
        adres, "Schade"
    ] + [None]*24 + [
        None, None, "Gebroken Lamp", 1, 15.00, None, 0.21
    ])

    wb.save(output_path)
    print(f"✅ Created populated test file: {output_path}")

if __name__ == "__main__":
    create_test_data()
