#!/usr/bin/env python3
"""
Create a chronological borg timeline per property showing:
- First borg = RyanRent → Owner payment
- Subsequent borgs = Tenant companies paying/receiving borg over the rental periods
"""

import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).parent.parent
TRANSACTION_FILE = BASE_DIR / "Shared/Sources/excel_data/FinTransactionSearch (2).csv"
DB_PATH = BASE_DIR / "database/ryanrent_v2.db"
OUTPUT_DIR = BASE_DIR / "Shared/Output"
OUTPUT_DIR.mkdir(exist_ok=True)

def convert_amount(amount_str):
    """Convert Dutch number format to float"""
    if pd.isna(amount_str):
        return 0.0
    return float(str(amount_str).replace('.', '').replace(',', '.').strip())

def parse_date(date_str):
    """Parse Dutch date format DD-MM-YYYY"""
    if pd.isna(date_str):
        return None
    try:
        return datetime.strptime(str(date_str).strip(), '%d-%m-%Y')
    except:
        return None

def main():
    print("🔍 BORG TIMELINE ANALYSIS - Per Property, Per Company, Per Year")
    print("="*80)
    
    # Load transactions
    print("Loading transactions...")
    df = pd.read_csv(TRANSACTION_FILE, sep=';', encoding='utf-16le')
    df['Amount'] = df['AmountDC'].apply(convert_amount)
    df['Date'] = df['EntryDate'].apply(parse_date)
    df['Year'] = df['Date'].apply(lambda x: x.year if x else None)
    df['Month'] = df['Date'].apply(lambda x: x.month if x else None)
    
    # Filter borg transactions (GL code 1165)
    borg_df = df[df['GLAccountCodeDescriptionCode'] == 1165].copy()
    print(f"Found {len(borg_df):,} borg transactions")
    
    # Load database info
    print("Loading database...")
    conn = sqlite3.connect(DB_PATH)
    huizen = pd.read_sql_query("""
        SELECT id as house_id, object_id, adres, plaats, borg_standaard 
        FROM huizen ORDER BY object_id
    """, conn)
    conn.close()
    
    # ========================================
    # CREATE TIMELINE PER PROPERTY
    # ========================================
    print("\n" + "="*80)
    print("CREATING PROPERTY TIMELINES")
    print("="*80)
    
    # Sort by property and date
    borg_df = borg_df.sort_values(['CostCenterCodeDescriptionCode', 'Date'])
    
    # Group by property
    properties = borg_df.groupby(['CostCenterCodeDescriptionCode', 'CostCenterCodeDescriptionDescription'])
    
    timelines = []
    
    for (cc_code, cc_desc), prop_df in properties:
        # Normalize object_id
        obj_id = str(cc_code).zfill(4) if str(cc_code).isdigit() else str(cc_code)
        
        # Get DB info if exists
        db_match = huizen[huizen['object_id'] == obj_id]
        db_adres = db_match['adres'].iloc[0] if len(db_match) > 0 else cc_desc
        db_plaats = db_match['plaats'].iloc[0] if len(db_match) > 0 else ''
        db_borg = db_match['borg_standaard'].iloc[0] if len(db_match) > 0 else 0
        
        # Get all borg transactions for this property
        for _, row in prop_df.iterrows():
            relatie = str(row['AccountCodeNameDescription']) if pd.notna(row['AccountCodeNameDescription']) else 'Unknown'
            amount = row['Amount']
            date = row['Date']
            year = row['Year']
            
            # Determine transaction type based on amount sign
            # Negative = RyanRent paid out (to owner or borg return)
            # Positive = RyanRent received (from tenant)
            if amount > 0:
                trans_type = "RECEIVED (from tenant)"
            else:
                trans_type = "PAID OUT (to owner/return)"
            
            timelines.append({
                'object_id': obj_id,
                'adres': db_adres,
                'plaats': db_plaats,
                'db_borg_standaard': db_borg,
                'date': date,
                'year': year,
                'month': row['Month'],
                'relatie': relatie[:60] if relatie else '',
                'amount': amount,
                'type': trans_type,
                'invoice': row.get('InvoiceNumber', ''),
                'your_ref': row.get('YourRef', '')
            })
    
    timeline_df = pd.DataFrame(timelines)
    timeline_df = timeline_df.sort_values(['object_id', 'date'])
    
    print(f"Created timeline with {len(timeline_df)} entries across {timeline_df['object_id'].nunique()} properties")
    
    # ========================================
    # PIVOT VIEW - Years as Columns
    # ========================================
    print("\n" + "="*80)
    print("CREATING PIVOT VIEW (Properties x Relaties x Years)")
    print("="*80)
    
    # Create summary per property, relatie, and year
    pivot_data = timeline_df.groupby(['object_id', 'adres', 'relatie', 'year']).agg({
        'amount': 'sum',
        'date': ['min', 'max']
    }).reset_index()
    pivot_data.columns = ['object_id', 'adres', 'relatie', 'year', 'total_borg', 'first_date', 'last_date']
    
    # Create wide format with years as columns
    pivot_wide = pivot_data.pivot_table(
        index=['object_id', 'adres', 'relatie'],
        columns='year',
        values='total_borg',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # ========================================
    # SHOW EXAMPLES
    # ========================================
    print("\n" + "="*80)
    print("EXAMPLE TIMELINES (Top 10 Properties by Transaction Count)")
    print("="*80)
    
    top_props = timeline_df.groupby('object_id').size().nlargest(10).index
    
    for obj_id in top_props:
        prop_timeline = timeline_df[timeline_df['object_id'] == obj_id]
        adres = prop_timeline['adres'].iloc[0]
        db_borg = prop_timeline['db_borg_standaard'].iloc[0]
        
        print(f"\n📍 {obj_id}: {adres}")
        print(f"   DB borg_standaard: €{db_borg:,.2f}")
        print(f"   Timeline:")
        
        for _, row in prop_timeline.iterrows():
            date_str = row['date'].strftime('%b %Y') if row['date'] else 'N/A'
            amount_str = f"€{row['amount']:+,.2f}"
            print(f"      {date_str}: {amount_str:>12} | {row['relatie'][:40]}")
        
        # Show net position
        net = prop_timeline['amount'].sum()
        print(f"   ─────────────────────────────")
        print(f"   NET BORG POSITION: €{net:,.2f}")
    
    # ========================================
    # FULL REPORT BY PROPERTY
    # ========================================
    print("\n" + "="*80)
    print("SUMMARY BY PROPERTY (All Tenants Through Time)")
    print("="*80)
    
    prop_summary = timeline_df.groupby(['object_id', 'adres']).agg({
        'amount': 'sum',
        'relatie': lambda x: list(x.unique()),
        'year': lambda x: f"{int(min(x))}-{int(max(x))}" if len(x) > 0 else 'N/A',
        'db_borg_standaard': 'first'
    }).reset_index()
    prop_summary.columns = ['object_id', 'adres', 'net_borg', 'tenants', 'period', 'db_borg']
    prop_summary['num_tenants'] = prop_summary['tenants'].apply(len)
    
    # Show properties with multiple tenants
    multi_tenant = prop_summary[prop_summary['num_tenants'] > 1].sort_values('num_tenants', ascending=False)
    
    print(f"\nProperties with MULTIPLE tenants (showing tenant turnover):")
    for _, row in multi_tenant.head(20).iterrows():
        print(f"\n   {row['object_id']}: {row['adres'][:40]}")
        print(f"      Period: {row['period']} | DB Borg: €{row['db_borg']:,.2f} | Net: €{row['net_borg']:,.2f}")
        print(f"      Tenants ({row['num_tenants']}):")
        for tenant in row['tenants'][:5]:
            print(f"         - {tenant[:50]}")
        if len(row['tenants']) > 5:
            print(f"         ... and {len(row['tenants']) - 5} more")
    
    # ========================================
    # EXPORT
    # ========================================
    print("\n" + "="*80)
    print("EXPORTING FILES")
    print("="*80)
    
    # Full timeline
    timeline_df.to_csv(OUTPUT_DIR / "borg_timeline_full.csv", index=False, encoding='utf-8-sig')
    print(f"✅ borg_timeline_full.csv - Complete chronological timeline")
    
    # Pivot view (years as columns)
    pivot_wide.to_csv(OUTPUT_DIR / "borg_pivot_by_year.csv", index=False, encoding='utf-8-sig')
    print(f"✅ borg_pivot_by_year.csv - Property x Relatie with year columns")
    
    # Property summary with tenant list
    prop_summary['tenants'] = prop_summary['tenants'].apply(lambda x: ' | '.join(x[:10]))
    prop_summary.to_csv(OUTPUT_DIR / "borg_property_summary.csv", index=False, encoding='utf-8-sig')
    print(f"✅ borg_property_summary.csv - Summary per property with all tenants")
    
    print("\n" + "="*80)
    print("✨ TIMELINE ANALYSIS COMPLETE!")
    print("="*80)

if __name__ == "__main__":
    main()
