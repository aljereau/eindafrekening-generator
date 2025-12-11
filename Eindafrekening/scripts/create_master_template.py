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
        ("Adres", None), 
        ("Type", None), 
        ("Klantnaam", None), 
        ("Object ID", header_blue), # D
        ("Klant Nr (Auto)", header_blue), # E
        ("RR Inspecteur", header_blue), # F
        ("Folder Link", header_blue),   # G
        
        # BASIS (Blue)
        ("Check-in", header_blue),        # H
        ("Check-out", header_blue),       # I
        ("Borg (€)", header_blue),        # J
        ("GWE Beheer", header_blue),      # K
        ("GWE Maandbedrag (€)", header_blue), # L
        ("Voorschot GWE (Auto)", header_blue), # M
        
        ("Meterbeheerder", header_blue),  # N
        ("Leverancier", header_blue),     # O
        ("Leverancier Nr (Auto)", header_blue), # P
        ("Contractnr", header_blue),      # Q
        ("Extra Voorschot (€)", header_blue), # R
        ("Extra Voor. Omschr.", header_blue), # S
        
        # GWE Readings (Orange) (Cols T-Y)
        ("Elek Begin", header_orange),    # T
        ("Elek Eind", header_orange),     # U
        ("Gas Begin", header_orange),     # V
        ("Gas Eind", header_orange),      # W
        ("Water Begin", header_orange),   # X
        ("Water Eind", header_orange),    # Y
        
        # SCHOONMAAK (Gold) (Cols Z-AE)
        ("Schoon Maak Pakket", header_gold), # Z
        ("Schoon Uren", header_gold),     # AA
        ("Uurtarief (€)", header_gold),   # AB
        ("Totaal Excl (€)", header_gold), # AC
        ("BTW %", header_gold),           # AD
        ("BTW Bedrag (€)", header_gold),  # AE
        ("Totaal Incl (€)", header_gold), # AF
        
        # ITEMS (Red) (Cols AG-AO)
        ("Kosten Type", header_red),      # AG
        ("Eenheid", header_red),          # AH
        ("Beschrijving", header_red),     # AI
        ("Aantal", header_red),           # AJ
        ("Prijs/Stuk (€)", header_red),   # AK
        ("Totaal Excl (€)", header_red),  # AL
        ("BTW %", header_red),            # AM
        ("BTW Bedrag (€)", header_red),   # AN
        ("Totaal Incl (€)", header_red)   # AO
    ]

    # Write Headers
    count = 1
    for item in columns_config:
        name, fill = item
        if not fill:
            fill = PatternFill(start_color="5B5B5B", end_color="5B5B5B", fill_type="solid")
            
        cell = ws.cell(row=1, column=count)
        cell.value = name
        cell.fill = fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        ws.column_dimensions[openpyxl.utils.get_column_letter(count)].width = 15
        count += 1

    # Specific widths
    ws.column_dimensions['A'].width = 25 
    ws.column_dimensions['C'].width = 25 
    ws.column_dimensions['G'].width = 30 # Folder Link
    ws.column_dimensions['AI'].width = 30 # Beschrijving

    # ==================== FORMULAS & VALIDATION ====================

    # Row Type
    dv_type = DataValidation(type="list", formula1='"Basis,GWE,GWE_Item,Schoonmaak,Schade,Extra"', allow_blank=False)
    ws.add_data_validation(dv_type)
    dv_type.add('B2:B5000')

    # Addresses
    dv_adres = DataValidation(type="list", formula1='=Lists!$A$2:$A$5000', allow_blank=True)
    ws.add_data_validation(dv_adres)
    dv_adres.add('A2:A5000')

    # Clients (Col C)
    dv_client = DataValidation(type="list", formula1='=Lists!$C$2:$C$5000', allow_blank=True)
    ws.add_data_validation(dv_client)
    dv_client.add('C2:C5000')

    # GWE Beheer (Col K)
    dv_gwe = DataValidation(type="list", formula1='"Via RyanRent,Eigen Beheer"', allow_blank=True)
    ws.add_data_validation(dv_gwe)
    dv_gwe.add('K2:K5000')

    # Schoonmaak Pakket (Col Z)
    dv_clean = DataValidation(type="list", formula1='"Basis Schoonmaak,Intensief Schoonmaak,Geen Schoonmaak,Achteraf Betaald"', allow_blank=True)
    ws.add_data_validation(dv_clean)
    dv_clean.add('Z2:Z5000')

    # Kosten Type (Col AG)
    dv_kosten = DataValidation(type="list", formula1='"Elektra,Gas,Water,Overig"', allow_blank=True)
    ws.add_data_validation(dv_kosten)
    dv_kosten.add('AG2:AG5000')

    # Styles
    grey_fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")

    # Prefill Formulas
    for r in range(2, 202):
        # D: ObjID -> VLOOKUP Address in Lists A:B -> 2
        ws[f'D{r}'] = f'=IF(A{r}="","",VLOOKUP(A{r},Lists!$A:$B,2,FALSE))'
        ws[f'D{r}'].fill = grey_fill 
        
        # E: Klant Nr -> VLOOKUP ClientName(C) in Lists C:D -> 2
        ws[f'E{r}'] = f'=IF(C{r}="","",VLOOKUP(C{r},Lists!$C:$D,2,FALSE))'
        ws[f'E{r}'].fill = grey_fill
        
        # F & G Meta
        ws[f'F{r}'].fill = grey_fill
        ws[f'G{r}'].fill = grey_fill

        # J: Borg (€) - Pre-fill from Lists Column H (Index 8)
        ws[f'J{r}'] = f'=IF(A{r}="","",IFERROR(VLOOKUP(A{r},Lists!$A:$H,8,FALSE),0))'
        ws[f'J{r}'].number_format = '€ #,##0.00'

        # L: GWE Maandbedrag - PREFILL from Lists Col G (Index 7)
        ws[f'L{r}'] = f'=IF(A{r}="","",IFERROR(VLOOKUP(A{r},Lists!$A:$H,7,FALSE),0))'
        ws[f'L{r}'].number_format = '€ #,##0.00'

        # M: GWE Voorschot (Auto) = IF(GWE Beheer="Eigen Beheer", 0, (Maandbedrag * 12 / 365) * Dagen)
        # K = GWE Beheer, L = Maandbedrag, I = Checkout, H = Checkin
        # Using commas for formula standard (Excel converts to semicolon based on locale)
        ws[f'M{r}'] = f'=IF(K{r}="Eigen Beheer",0,IF(AND(ISNUMBER(L{r}),I{r}<>"",H{r}<>""),(L{r}*12/365)*(I{r}-H{r}),0))'
        ws[f'M{r}'].number_format = '€ #,##0.00'
        ws[f'M{r}'].fill = grey_fill 
        
        # P: Lev Nr -> VLOOKUP LevName(O) in Lists E:F -> 2
        ws[f'P{r}'] = f'=IF(O{r}="","",VLOOKUP(O{r},Lists!$E:$F,2,FALSE))'
        ws[f'P{r}'].fill = grey_fill 
        
        # Schoonmaak Calculations
        # AC (TotEx) = AA(Uren) * AB(Tarief)
        ws[f'AC{r}'] = f'=IF(AND(AA{r}<>"",AB{r}<>""),AA{r}*AB{r},"")'
        ws[f'AC{r}'].fill = fill_calc
        ws[f'AC{r}'].number_format = '€ #,##0.00'
        
        # AD (BTW%)
        ws[f'AD{r}'].number_format = '0%'

        # AE (BTW€) = AC * AD
        ws[f'AE{r}'] = f'=IF(AND(AC{r}<>"",AD{r}<>""),AC{r}*AD{r},"")'
        ws[f'AE{r}'].fill = fill_calc
        ws[f'AE{r}'].number_format = '€ #,##0.00'
        
        # AF (TotInc) = AC + AE
        ws[f'AF{r}'] = f'=IF(AND(AC{r}<>"",AE{r}<>""),AC{r}+AE{r},"")'
        ws[f'AF{r}'].fill = fill_calc
        ws[f'AF{r}'].number_format = '€ #,##0.00'
        
        # ITEM CALCULATIONS
        # AJ (Aantal) - SMART LOOKUP
        # GWE Indices: ElekBegin=T, ElekEind=U, GasBegin=V, GasEind=W, WaterBegin=X, WaterEind=Y
        f_elek = f'SUMIFS($U:$U,$A:$A,$A{r},$B:$B,"GWE")-SUMIFS($T:$T,$A:$A,$A{r},$B:$B,"GWE")'
        f_gas = f'SUMIFS($W:$W,$A:$A,$A{r},$B:$B,"GWE")-SUMIFS($V:$V,$A:$A,$A{r},$B:$B,"GWE")'
        f_water = f'SUMIFS($Y:$Y,$A:$A,$A{r},$B:$B,"GWE")-SUMIFS($X:$X,$A:$A,$A{r},$B:$B,"GWE")'
        
        f_smart = f'IF($AG{r}="Elektra",{f_elek},IF($AG{r}="Gas",{f_gas},IF($AG{r}="Water",{f_water},"")))'
        
        ws[f'AJ{r}'] = f'=IF($B{r}="GWE_Item",{f_smart},"")'
        
        # AL (TotEx) = AJ * AK
        ws[f'AL{r}'] = f'=IF(AND(AJ{r}<>"",AK{r}<>""),AJ{r}*AK{r},"")'
        ws[f'AL{r}'].fill = fill_calc
        ws[f'AL{r}'].number_format = '€ #,##0.00'
        
        # AM (BTW%)
        ws[f'AM{r}'].number_format = '0%'

        # AN (BTW€) = AL * AM
        ws[f'AN{r}'] = f'=IF(AND(AL{r}<>"",AM{r}<>""),AL{r}*AM{r},"")'
        ws[f'AN{r}'].fill = fill_calc
        ws[f'AN{r}'].number_format = '€ #,##0.00'
        
        # AO (TotInc) = AL + AN
        ws[f'AO{r}'] = f'=IF(AND(AL{r}<>"",AN{r}<>""),AL{r}+AN{r},"")'
        ws[f'AO{r}'].fill = fill_calc
        ws[f'AO{r}'].number_format = '€ #,##0.00'

    # Conditional Formatting
    ws.conditional_formatting.add('D2:S5000', FormulaRule(formula=['$B2<>"Basis"'], stopIfTrue=True, fill=grey_fill))
    ws.conditional_formatting.add('T2:Y5000', FormulaRule(formula=['$B2<>"GWE"'], stopIfTrue=True, fill=grey_fill))
    ws.conditional_formatting.add('Z2:AF5000', FormulaRule(formula=['$B2<>"Schoonmaak"'], stopIfTrue=True, fill=grey_fill))
    ws.conditional_formatting.add('AG2:AO5000', FormulaRule(formula=['AND($B2<>"Schade",$B2<>"Extra",$B2<>"GWE_Item")'], stopIfTrue=True, fill=grey_fill))

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
    ws['C1'] = "Clients (Name)"
    ws['D1'] = "Clients (ID)"
    ws['E1'] = "Leveranciers (Name)"
    ws['F1'] = "Leveranciers (ID)"
    ws['G1'] = "GWE Voorschot (Default)"
    ws['H1'] = "Borg (Default)"
    
    try:
        db = Database()
        conn = db.get_connection()
        
        # Houses with GWE info and Borg
        cursor = conn.execute("""
            SELECT adres, object_id, voorschot_gwe, borg
            FROM huizen 
            WHERE status='active' AND object_id IS NOT NULL AND object_id != ''
            ORDER BY adres
        """)
        houses = cursor.fetchall()

        # Clients
        cursor = conn.execute("SELECT naam, id FROM relaties WHERE is_klant=1 ORDER BY naam")
        clients = cursor.fetchall()
        
        # Suppliers (Leveranciers)
        cursor = conn.execute("SELECT naam, id FROM leveranciers ORDER BY naam")
        suppliers = cursor.fetchall()
        
        conn.close()
        
        for i, (addr, obj_id, gwe_val, borg_val) in enumerate(houses, 2):
            ws[f'A{i}'] = addr
            ws[f'B{i}'] = obj_id if obj_id else ""
            ws[f'G{i}'] = gwe_val if gwe_val else 0
            ws[f'H{i}'] = borg_val if borg_val else 0
            
        for i, (name, c_id) in enumerate(clients, 2):
            ws[f'C{i}'] = name
            ws[f'D{i}'] = c_id
            
        for i, (name, l_id) in enumerate(suppliers, 2):
            ws[f'E{i}'] = name
            ws[f'F{i}'] = l_id
            
        print(f"📊 Added {len(houses)} houses, {len(clients)} clients, {len(suppliers)} suppliers to lists")
            
    except Exception as e:
        print(f"⚠️ Could not fetch data: {e}")
        # Valid Fallback for development
        ws['A2'] = "Test Address 1"
        ws['B2'] = "OBJ-001"
        ws['G2'] = 50.00
        ws['H2'] = 500.00
        ws['C2'] = "Test Client"

if __name__ == "__main__":
    create_master_template()
