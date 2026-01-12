#!/usr/bin/env python3
"""
Export v_property_overview to Excel with Dutch number formatting.
Numbers use comma as decimal separator (e.g., 1234,56).
"""
import sqlite3
import pandas as pd
from datetime import datetime
import os

db_path = "database/ryanrent_mock.db"
output_dir = "Eindafrekening/output"
os.makedirs(output_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
output_file = f"{output_dir}/property_overview_{timestamp}.xlsx"

print("📊 Exporting v_property_overview to Excel...")

# Connect and fetch data
conn = sqlite3.connect(db_path)
df = pd.read_sql_query("SELECT * FROM v_property_overview", conn)
conn.close()

print(f"   Loaded {len(df)} rows")

# Create Excel writer with Dutch locale formatting
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Property Overview', index=False)
    
    # Get worksheet and format numbers
    ws = writer.sheets['Property Overview']
    
    # Define monetary columns (by name)
    monetary_cols = [
        'marge', 'verhuur_incl_btw', 'verhuur_excl_btw', 'verhuur_pppw',
        'kale_verhuurprijs', 'voorschot_gwe', 'overige_kosten', 'afval',
        'inhuur_incl_btw', 'inhuur_excl_btw', 'kale_inhuurprijs', 'inhuur_pppw'
    ]
    
    # Get column indices
    col_indices = {}
    for col_idx, col_name in enumerate(df.columns, start=1):
        if col_name in monetary_cols:
            col_indices[col_name] = col_idx
    
    # Apply Dutch number format to monetary columns
    # Format: #.##0,00 (thousand separator = dot, decimal = comma)
    dutch_format = '#.##0,00'
    
    for col_name, col_idx in col_indices.items():
        for row_idx in range(2, len(df) + 2):  # Skip header row
            cell = ws.cell(row=row_idx, column=col_idx)
            if cell.value is not None:
                try:
                    # Convert string back to float if needed
                    if isinstance(cell.value, str):
                        cell.value = float(cell.value)
                    cell.number_format = dutch_format
                except (ValueError, TypeError):
                    pass
    
    # Auto-fit column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

print(f"✅ Exported to: {output_file}")
print(f"   Numbers formatted with Dutch locale (comma decimal)")
