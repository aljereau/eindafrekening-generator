import openpyxl
import sys

file_path = '/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/Shared/Sources/Houses List.xlsx'

try:
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb.active
    print(f"Sheet Name: {sheet.title}")
    
    # Print first few rows
    for i, row in enumerate(sheet.iter_rows(values_only=True)):
        print(row)
        if i >= 5:
            break
except Exception as e:
    print(f"Error: {e}")
