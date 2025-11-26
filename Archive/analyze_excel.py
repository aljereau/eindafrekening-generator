import pandas as pd
import os

def analyze_excel(file_path):
    print(f"--- Analyzing: {os.path.basename(file_path)} ---")
    try:
        xl = pd.ExcelFile(file_path)
        print(f"Sheets: {xl.sheet_names}")
        
        for sheet in xl.sheet_names:
            print(f"\nSheet: {sheet}")
            # Skip rows until we find the header "Code"
            df = pd.read_excel(file_path, sheet_name=sheet, header=None)
            
            # Find the header row
            header_row_idx = df[df.iloc[:, 0] == 'Code'].index[0]
            
            # Reload with correct header
            df = pd.read_excel(file_path, sheet_name=sheet, skiprows=header_row_idx+1, header=None)
            df.columns = ['Code', 'Omschrijving']
            
            # Search for A- codes
            archived = df[df['Code'].astype(str).str.startswith('A-', na=False)]
            print(f"Found {len(archived)} archived codes:")
            print(archived.head())
            print("-" * 50)
            
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

analyze_excel("/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/HuizenManager/1-CoHousingNL_B.V.-26-11-2025-HRMCostCenters.xlsx")
