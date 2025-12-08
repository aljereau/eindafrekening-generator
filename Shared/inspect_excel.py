import openpyxl
import sys

file_path = '/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/Shared/Sources/Houses List.xlsx'

try:
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb.active
    print(f"Sheet Name: {sheet.title}")
    
    headers = []
    for cell in sheet[1]:
        headers.append(cell.value)
    print(f"Headers: {headers}")
    
    print("\nFirst 3 rows:")
    for i, row in enumerate(sheet.iter_rows(min_row=2, max_row=4, values_only=True)):
        print(f"Row {i+1}: {row}")
        
except Exception as e:
    print(f"Error: {e}")
