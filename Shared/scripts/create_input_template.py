import pandas as pd
import os

# Define the columns for the input sheet
columns = [
    'Object ID (e.g. 0099)',
    'Adres',
    'Postcode',
    'Plaats',
    'Aantal Slaapkamers',
    'Aantal Personen',
    'Eigenaar (Naam)',
    'Inhuur Prijs (Kale huur)',
    'Huurder (Naam)',
    'Verhuur Prijs (Kale huur)',
    'Start Datum (YYYY-MM-DD)',
    'Eind Datum (YYYY-MM-DD)',
    'Kluis Code 1',
    'Kluis Code 2',
    'Opmerkingen'
]

# Create a DataFrame with empty rows or example data
data = [
    ['0099', 'Voorbeeldstraat 1', '1234 AB', 'Amsterdam', 3, 4, 'Vastgoed BV', 1200, 'Expats Inc', 1800, '2024-01-01', '2024-12-31', '1234', '5678', 'Voorbeeld rij']
]

df = pd.DataFrame(data, columns=columns)

# Ensure directory exists
output_dir = os.path.join(os.path.dirname(__file__), '..', 'Templates')
os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(output_dir, 'RyanRent_Input_Template.xlsx')

# Write to Excel
try:
    df.to_excel(output_file, index=False)
    print(f"✅ Template created successfully at: {os.path.abspath(output_file)}")
except Exception as e:
    print(f"❌ Error creating template: {e}")
