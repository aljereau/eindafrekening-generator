import openpyxl
import sys
import os

template_path = "Eindafrekening/src/input_template.xlsx"
wb = openpyxl.load_workbook(template_path)
ws = wb['Lists']

print("--- Lists Sheet (First 10 rows) ---")
for row in ws.iter_rows(min_row=1, max_row=10, max_col=6):
    row_data = [str(cell.value) for cell in row]
    print(" | ".join(row_data))
