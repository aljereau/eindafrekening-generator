import openpyxl
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.formatting.rule import FormulaRule
import os
import sys

# Add Shared to path for Database
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(os.path.join(root_dir, 'Shared'))
from database import Database

def create_master_template(output_path=None):
    if output_path is None:
        output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "input_master.xlsx")

    wb = openpyxl.Workbook()
    
    # Create Lists sheet first (for dropdowns & lookups)
    create_lists_sheet(wb)
    
    # Create Input sheet
    ws = wb.active
    ws.title = "Input"
    
    # ==================== STYLES ====================
    header_blue = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_orange = PatternFill(start_color="ED7D31", end_color="ED7D31", fill_type="solid")
    header_gold = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
    header_red = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
    fill_calc = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    # ==================== COLUMNS CONFIGURATION ====================
    columns_config = [
        # GLOBAL
        ("Adres", None), ("Type", None), ("Klantnaam", None), ("Object ID", header_blue),
        
        # BASIS (Blue)
        ("Check-in", header_blue), ("Check-out", header_blue), ("Borg (€)", header_blue), 
        ("GWE Beheer", header_blue), ("Meterbeheerder", header_blue), ("Leverancier", header_blue), ("Contractnr", header_blue), 
        ("Extra Voorschot (€)", header_blue), ("Extra Voor. Omschr.", header_blue),
        
        # GWE Readings (Orange) (Cols N-S)
        ("Elek Begin", header_orange), ("Elek Eind", header_orange), 
        ("Gas Begin", header_orange), ("Gas Eind", header_orange), 
        ("Water Begin", header_orange), ("Water Eind", header_orange),
        
        # SCHOONMAAK (Gold) (Cols T-Z)
        ("Schoon Maak Pakket", header_gold), "Schoon Uren", "Uurtarief (€)", "Totaal Excl (€)", "BTW %", "BTW Bedrag (€)", "Totaal Incl (€)",
        
        # ITEMS (Red) (Cols AA-AI)
        # Added: Kosten Type, Eenheid
        ("Kosten Type", header_red), ("Eenheid", header_red),
        ("Beschrijving", header_red), ("Aantal", header_red), ("Prijs/Stuk (€)", header_red), 
        ("Totaal Excl (€)", header_red), "BTW %", "BTW Bedrag (€)", "Totaal Incl (€)"
    ]
    
    # Write Headers
    # Simplify loop to handle tuple or string
    count = 1
    for item in columns_config:
        if isinstance(item, tuple):
            name, fill = item
        else:
            name, fill = item, PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid") # Default Gold/Red hack

        # Fix fill logic:
        # Schoonmaak strings -> Gold
        # Items strings -> Red
        if not isinstance(item, tuple):
             if "Schoon" in name or "Uurtarief" in name or "Incl" in name or "Excl" in name: 
                 if count >= 20 and count <= 26: fill = header_gold
                 elif count >= 27: fill = header_red
        
        cell = ws.cell(row=1, column=count)
        cell.value = name
        if fill:
            cell.fill = fill
            cell.font = header_font
        else:
            cell.fill = PatternFill(start_color="5B5B5B", end_color="5B5B5B", fill_type="solid")
            cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        ws.column_dimensions[openpyxl.utils.get_column_letter(count)].width = 15
        count += 1

    # Specific widths
    ws.column_dimensions['A'].width = 25 
    ws.column_dimensions['C'].width = 25 
    ws.column_dimensions['AC'].width = 30 # Beschrijving (New Index AA -> AC)
    
    # ==================== FORMULAS & VALIDATION ====================
    # Indices Mapping:
    # ...
    # Z (26) = Schoon TotIncl
    # AA (27) = Kosten Type
    # AB (28) = Eenheid
    # AC (29) = Beschrijving
    # AD (30) = Aantal
    # AE (31) = Prijs
    # AF (32) = TotEx
    # AG (33) = BTW%
    # AH (34) = BTW€
    # AI (35) = TotInc
    
    # Row Type
    dv_type = DataValidation(type="list", formula1='"Basis,GWE,GWE_Item,Schoonmaak,Schade,Extra"', allow_blank=False)
    ws.add_data_validation(dv_type)
    dv_type.add('B2:B5000')
    
    # Addresses & Clients
    dv_adres = DataValidation(type="list", formula1='=Lists!$A$2:$A$5000', allow_blank=True)
    ws.add_data_validation(dv_adres)
    dv_adres.add('A2:A5000')

    dv_client = DataValidation(type="list", formula1='=Lists!$C$2:$C$5000', allow_blank=True)
    ws.add_data_validation(dv_client)
    dv_client.add('C2:C5000')
    
    # GWE Beheer
    dv_gwe = DataValidation(type="list", formula1='"Via RyanRent,Eigen Beheer"', allow_blank=True)
    ws.add_data_validation(dv_gwe)
    dv_gwe.add('H2:H5000')
    
    # Schoonmaak Pakket
    dv_clean = DataValidation(type="list", formula1='"Basis Schoonmaak,Intensief Schoonmaak,Geen Schoonmaak,Achteraf Betaald"', allow_blank=True)
    ws.add_data_validation(dv_clean)
    dv_clean.add('T2:T5000')
    
    # Kosten Type (New)
    dv_kosten = DataValidation(type="list", formula1='"Elektra,Gas,Water,Overig"', allow_blank=True)
    ws.add_data_validation(dv_kosten)
    # Apply to Col AA (27)
    dv_kosten.add('AA2:AA5000')

    # Prefill Formulas
    for r in range(2, 202):
        # ObjID
        ws[f'D{r}'] = f'=IF(A{r}="","",VLOOKUP(A{r},Lists!$A:$B,2,FALSE))'
        
        # Schoonmaak Calculations
        # W (TotEx) = U*V
        ws[f'W{r}'] = f'=IF(AND(U{r}<>"",V{r}<>""),U{r}*V{r},"")'
        ws[f'W{r}'].fill = fill_calc
        ws[f'W{r}'].number_format = '€ #,##0.00'
        # Y (BTW€) = W*X
        ws[f'Y{r}'] = f'=IF(AND(W{r}<>"",X{r}<>""),W{r}*X{r},"")'
        ws[f'Y{r}'].fill = fill_calc
        ws[f'Y{r}'].number_format = '€ #,##0.00'
        # Z (TotInc) = W+Y
        ws[f'Z{r}'] = f'=IF(AND(W{r}<>"",Y{r}<>""),W{r}+Y{r},"")'
        ws[f'Z{r}'].fill = fill_calc
        ws[f'Z{r}'].number_format = '€ #,##0.00'
        
        # ITEM CALCULATIONS
        # AD (Aantal) - SMART LOOKUP
        # If GWE_Item + Elektra/Gas/Water -> Fetch Consumption from GWE row
        # Formula uses SUMIFS to find the GWE row for the SAME address
        # Elek: O(Eind) - N(Begin)
        # Gas: Q(Eind) - P(Begin)
        # Water: S(Eind) - R(Begin)
        
        # Construct the formula parts (Removed outer parens)
        f_elek = f'SUMIFS($O:$O,$A:$A,$A{r},$B:$B,"GWE")-SUMIFS($N:$N,$A:$A,$A{r},$B:$B,"GWE")'
        f_gas = f'SUMIFS($Q:$Q,$A:$A,$A{r},$B:$B,"GWE")-SUMIFS($P:$P,$A:$A,$A{r},$B:$B,"GWE")'
        f_water = f'SUMIFS($S:$S,$A:$A,$A{r},$B:$B,"GWE")-SUMIFS($R:$R,$A:$A,$A{r},$B:$B,"GWE")'
        
        # Main Logic
        f_smart = f'IF($AA{r}="Elektra",{f_elek},IF($AA{r}="Gas",{f_gas},IF($AA{r}="Water",{f_water},"")))'
        
        ws[f'AD{r}'] = f'=IF($B{r}="GWE_Item",{f_smart},"")'
        
        # AF (TotEx) = AD (Aantal) * AE (Prijs)
        ws[f'AF{r}'] = f'=IF(AND(AD{r}<>"",AE{r}<>""),AD{r}*AE{r},"")'
        ws[f'AF{r}'].fill = fill_calc
        ws[f'AF{r}'].number_format = '€ #,##0.00'
        
        # AH (BTW€) = AF * AG
        ws[f'AH{r}'] = f'=IF(AND(AF{r}<>"",AG{r}<>""),AF{r}*AG{r},"")'
        ws[f'AH{r}'].fill = fill_calc
        ws[f'AH{r}'].number_format = '€ #,##0.00'
        
        # AI (TotInc) = AF + AH
        ws[f'AI{r}'] = f'=IF(AND(AF{r}<>"",AH{r}<>""),AF{r}+AH{r},"")'
        ws[f'AI{r}'].fill = fill_calc
        ws[f'AI{r}'].number_format = '€ #,##0.00'

    # Conditional Formatting
    grey_fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
    
    # Basis: D-M -> Basis
    ws.conditional_formatting.add('D2:M5000', FormulaRule(formula=['$B2<>"Basis"'], stopIfTrue=True, fill=grey_fill))
    # GWE: N-S -> GWE (Readings)
    ws.conditional_formatting.add('N2:S5000', FormulaRule(formula=['$B2<>"GWE"'], stopIfTrue=True, fill=grey_fill))
    # Cleaning: T-Z -> Schoonmaak
    ws.conditional_formatting.add('T2:Z5000', FormulaRule(formula=['$B2<>"Schoonmaak"'], stopIfTrue=True, fill=grey_fill))
    # Items: AA-AI -> Schade OR Extra OR GWE_Item
    ws.conditional_formatting.add('AA2:AI5000', FormulaRule(formula=['AND($B2<>"Schade",$B2<>"Extra",$B2<>"GWE_Item")'], stopIfTrue=True, fill=grey_fill))

    ws.freeze_panes = 'A2'
    
    # Dashboard
    create_dashboard_sheet(wb, ws) 

    wb.save(output_path)
    print(f"✅ Generated Universal Master Template: {output_path}")

def create_dashboard_sheet(wb, input_ws):
    ws = wb.create_sheet("Dashboard", 0) 
    ws.sheet_properties.tabColor = "00B050" 
    
    ws['A1'] = "COMPLETENESS DASHBOARD"
    ws['A1'].font = Font(size=14, bold=True)
    
    headers = ["Adres", "Basis?", "GWE?", "Schoonmaak?", "STATUS"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col)
        cell.value = header
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="364E6F", fill_type="solid")
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15
        
    ws.column_dimensions['A'].width = 30
    
    # Use _xlfn. prefix for dynamic array functions to ensure compatibility
    ws['A4'] = '=_xlfn.UNIQUE(_xlfn.FILTER(Input!A2:A5000, Input!A2:A5000<>""))'
    
    for i in range(4, 54): 
        ws[f'B{i}'] = f'=IF(A{i}="","",IF(COUNTIFS(Input!$A:$A, A{i}, Input!$B:$B, "Basis")>0, "OK", "MISSING"))'
        ws[f'C{i}'] = f'=IF(A{i}="","",IF(COUNTIFS(Input!$A:$A, A{i}, Input!$B:$B, "GWE")>0, "OK", "MISSING"))'
        ws[f'D{i}'] = f'=IF(A{i}="","",IF(COUNTIFS(Input!$A:$A, A{i}, Input!$B:$B, "Schoonmaak")>0, "OK", "MISSING"))'
        ws[f'E{i}'] = f'=IF(A{i}="","",IF(AND(B{i}="OK",C{i}="OK",D{i}="OK"), "✅ READY", "⚠️ INCOMPLETE"))'
    
    green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    
    ws.conditional_formatting.add('E4:E54', FormulaRule(formula=['E4="✅ READY"'], stopIfTrue=True, fill=green_fill))
    ws.conditional_formatting.add('E4:E54', FormulaRule(formula=['E4="⚠️ INCOMPLETE"'], stopIfTrue=True, fill=red_fill))
    ws.conditional_formatting.add('B4:D54', FormulaRule(formula=['B4="MISSING"'], stopIfTrue=True, fill=red_fill))
    ws.conditional_formatting.add('B4:D54', FormulaRule(formula=['B4="OK"'], stopIfTrue=True, fill=green_fill))

def create_lists_sheet(wb):
    ws = wb.create_sheet("Lists")
    ws.sheet_state = 'hidden'
    ws['A1'] = "Address"
    ws['B1'] = "Object ID"
    ws['C1'] = "Clients"
    
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.execute("""
            SELECT adres, object_id 
            FROM huizen 
            WHERE status='active' AND object_id IS NOT NULL AND object_id != ''
            ORDER BY adres
        """)
        houses = cursor.fetchall()
        cursor = conn.execute("SELECT naam FROM relaties WHERE is_klant=1 ORDER BY naam")
        clients = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        for i, (addr, obj_id) in enumerate(houses, 2):
            ws[f'A{i}'] = addr
            ws[f'B{i}'] = obj_id if obj_id else ""
        for i, name in enumerate(clients, 2):
            ws[f'C{i}'] = name
            
        print(f"📊 Added {len(houses)} houses and {len(clients)} clients to lists")
            
    except Exception as e:
        print(f"⚠️ Could not fetch data: {e}")
        ws['A2'] = "Test Address 1"
        ws['B2'] = "OBJ-001"
        ws['C2'] = "Test Client"

if __name__ == "__main__":
    create_master_template()
