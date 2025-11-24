import sys
import os
from excel_reader import read_excel

def debug_excel_data(filename):
    print(f"Reading {filename}...")
    try:
        data = read_excel(filename)
        
        print("\n--- GWE Meterstanden Debug ---")
        if 'gwe_meterstanden' in data:
            ms = data['gwe_meterstanden']
            print(f"Stroom: {ms.stroom}")
            print(f"Gas: {ms.gas}")
            print(f"Water: {ms.water}")
        else:
            print("KEY 'gwe_meterstanden' NOT FOUND in data!")
            
    except Exception as e:
        print(f"Error reading excel: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_excel_data("input_template.xlsx")
