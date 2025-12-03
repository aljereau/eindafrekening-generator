import pandas as pd
import sys

file_path = "Shared/Sources/Houses List.xlsx"
try:
    df = pd.read_excel(file_path)
    print("Columns found:", df.columns.tolist())
    print("First 5 rows:")
    print(df.head(5).to_string())
    print("Rows with 'A' in Code:")
    print(df[df['Code'].astype(str).str.contains('A', na=False)].head(10).to_string())
except Exception as e:
    print(f"Error reading file: {e}")
