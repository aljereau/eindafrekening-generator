import openpyxl

def inspect_excel(filepath='input.xlsx'):
    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
        print(f"Sheet names: {wb.sheetnames}")
        
        if 'Hoofdgegevens' in wb.sheetnames:
            sheet = wb['Hoofdgegevens']
            print("\n--- Hoofdgegevens ---")
            for row in sheet.iter_rows(values_only=True):
                print(row)
        else:
            print("Sheet 'Hoofdgegevens' not found!")

        if 'Schades Detail' in wb.sheetnames:
            sheet = wb['Schades Detail']
            print("\n--- Schades Detail ---")
            for row in sheet.iter_rows(values_only=True):
                print(row)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_excel()
