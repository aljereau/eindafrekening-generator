#!/usr/bin/env python3
"""
Generate P&L overview per Kostenplaats (property).
Aggregates financial transactions into:
- Huur Inkomsten (8105)
- Huur Kosten (7100)
- GWE Kosten (7105)
- Overige Kosten (7106-7112)
- Netto Marge
"""
import pandas as pd
import re
from datetime import datetime

# Read data
print("📊 Loading financial data...")
df = pd.read_excel('Shared/Sources/Copy of RR-example-CoHousingNL_B.V.-07-01-2026-FinTransactionSearch (1).xlsx', sheet_name='Sheet1')
print(f"   Loaded {len(df)} rows")

# Clean up NaN
df['d'] = df['d'].fillna(0)
df['c'] = df['c'].fillna(0)

# Filter only rows WITH Kostenplaats
df_with_kp = df[df['Kostenplaats'].notna()].copy()
print(f"   Rows with Kostenplaats: {len(df_with_kp)}")

# Extract Object ID from Kostenplaats (e.g., "0135 - Amperestraat 36A" -> "0135")
def extract_object_id(kp):
    if pd.isna(kp):
        return None
    match = re.match(r'^(A-)?(\d+)', str(kp))
    if match:
        prefix = match.group(1) or ''
        num = match.group(2)
        return f"{prefix}{num.zfill(4)}"
    return None

df_with_kp['object_id'] = df_with_kp['Kostenplaats'].apply(extract_object_id)

# Define account categories
INCOME_ACCOUNTS = {
    '8105 - Omzet laag': 'Huur Inkomsten',
    '8100 - Omzet hoog': 'Overige Inkomsten',
    '8109 - Omzet Schoonmaak en inspecties': 'Schoonmaak Inkomsten',
    '8110 - Omzet reparatie, onderhoud en schades': 'Schade Inkomsten',
    '8115 - Omzet GWE': 'GWE Inkomsten',
}

COST_ACCOUNTS = {
    '7100 - Huur woningen': 'Huur Kosten',
    '7105 - Gas Water Electra inkoop': 'GWE Kosten',
    '7106 - Vuilcontainers': 'Afval Kosten',
    '7107 - Internet': 'Internet Kosten',
    '7109 - Schoonmaakkosten': 'Schoonmaak Kosten',
    '7110 - Schade\'s/onderhoud woningen': 'Schade Kosten',
    '7112 - Overige kosten': 'Overige Kosten',
}

# Create summary per Kostenplaats
print("\n🔄 Aggregating per Kostenplaats...")

summary_data = []

for kp, group in df_with_kp.groupby('Kostenplaats'):
    obj_id = extract_object_id(kp)
    adres = str(kp).split(' - ', 1)[1] if ' - ' in str(kp) else str(kp)
    
    row = {
        'Object ID': obj_id,
        'Adres': adres[:50],
        'Kostenplaats': kp,
    }
    
    # Calculate income (credit = income)
    total_income = 0
    for acc, label in INCOME_ACCOUNTS.items():
        acc_data = group[group['Grootboekrekening'] == acc]
        amount = acc_data['c'].sum() - acc_data['d'].sum()  # Net credit
        row[label] = round(amount, 2)
        total_income += amount
    row['Totaal Inkomsten'] = round(total_income, 2)
    
    # Calculate costs (debit = cost)
    total_costs = 0
    for acc, label in COST_ACCOUNTS.items():
        acc_data = group[group['Grootboekrekening'] == acc]
        amount = acc_data['d'].sum() - acc_data['c'].sum()  # Net debit
        row[label] = round(amount, 2)
        total_costs += amount
    row['Totaal Kosten'] = round(total_costs, 2)
    
    # Margin
    row['Bruto Marge'] = round(total_income - total_costs, 2)
    
    # Count transactions
    row['Aantal Transacties'] = len(group)
    
    summary_data.append(row)

summary_df = pd.DataFrame(summary_data)

# Sort by Object ID
summary_df = summary_df.sort_values('Object ID')

# Output statistics
print(f"\n📈 Summary Statistics:")
print(f"   Unique Kostenplaatsen: {len(summary_df)}")
print(f"   Total Inkomsten: € {summary_df['Totaal Inkomsten'].sum():,.2f}")
print(f"   Total Kosten: € {summary_df['Totaal Kosten'].sum():,.2f}")
print(f"   Total Marge: € {summary_df['Bruto Marge'].sum():,.2f}")

# Show top 10 by income
print(f"\n📊 Top 10 by Huur Inkomsten:")
top10 = summary_df.nlargest(10, 'Huur Inkomsten')[['Object ID', 'Adres', 'Huur Inkomsten', 'Huur Kosten', 'Bruto Marge']]
print(top10.to_string(index=False))

# Show properties with negative margin
negative_margin = summary_df[summary_df['Bruto Marge'] < 0]
print(f"\n⚠️  Properties with NEGATIVE margin: {len(negative_margin)}")
if len(negative_margin) > 0:
    print(negative_margin[['Object ID', 'Adres', 'Totaal Inkomsten', 'Totaal Kosten', 'Bruto Marge']].head(10).to_string(index=False))

# Export to Excel
output_file = 'Eindafrekening/output/kostenplaats_overview.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    summary_df.to_excel(writer, sheet_name='P&L per Kostenplaats', index=False)
    
    # Add summary sheet
    totals = pd.DataFrame([{
        'Metric': 'Totaal Inkomsten',
        'Bedrag': summary_df['Totaal Inkomsten'].sum()
    }, {
        'Metric': 'Totaal Kosten',
        'Bedrag': summary_df['Totaal Kosten'].sum()
    }, {
        'Metric': 'Bruto Marge',
        'Bedrag': summary_df['Bruto Marge'].sum()
    }, {
        'Metric': 'Aantal Kostenplaatsen',
        'Bedrag': len(summary_df)
    }])
    totals.to_excel(writer, sheet_name='Totalen', index=False)

print(f"\n✅ Exported to: {output_file}")
