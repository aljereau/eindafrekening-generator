import openpyxl

wb = openpyxl.load_workbook('src/input_template.xlsx', data_only=True)
ws = wb['Schoonmaak']
print("Inspecting Schoonmaak sheet (rows 1-20):")
for i, row in enumerate(ws.iter_rows(min_row=1, max_row=20, min_col=1, max_col=5, values_only=True)):
    print(f"Row {1+i}: {row}")
