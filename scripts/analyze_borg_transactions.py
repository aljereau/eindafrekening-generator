#!/usr/bin/env python3
"""
Analyze all financial transactions to identify borg (deposit) payments.
Cross-reference with the huizen table to find discrepancies.
"""

import pandas as pd
import sqlite3
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
TRANSACTION_FILE = BASE_DIR / "Shared/Sources/excel_data/FinTransactionSearch (2).csv"
DB_PATH = BASE_DIR / "database/ryanrent_v2.db"

def load_transactions():
    """Load transaction data with proper UTF-16 encoding"""
    print(f"Loading transactions from {TRANSACTION_FILE}...")
    df = pd.read_csv(TRANSACTION_FILE, sep=';', encoding='utf-16le')
    print(f"Loaded {len(df):,} transactions")
    print(f"Date range: {df['EntryDate'].min()} to {df['EntryDate'].max()}")
    return df

def load_database_info():
    """Load houses and relaties from database"""
    print(f"\nLoading data from database...")
    conn = sqlite3.connect(DB_PATH)
    
    huizen = pd.read_sql_query("""
        SELECT id as house_id, object_id, adres, plaats, borg_standaard as borg
        FROM huizen ORDER BY object_id
    """, conn)
    print(f"Loaded {len(huizen)} houses from database")
    
    relaties = pd.read_sql_query("SELECT id as relatie_id, naam FROM relaties", conn)
    print(f"Loaded {len(relaties)} relaties from database")
    
    contracts = pd.read_sql_query("""
        SELECT vc.id, vc.relatie_id, vc.house_id, vc.start_date, vc.end_date, 
               vc.borg_override, h.object_id, r.naam as relatie_naam
        FROM verhuur_contracten vc
        JOIN huizen h ON vc.house_id = h.id
        JOIN relaties r ON vc.relatie_id = r.id
    """, conn)
    print(f"Loaded {len(contracts)} contracts from database")
    
    conn.close()
    return huizen, relaties, contracts

def convert_amount(amount_str):
    """Convert Dutch number format to float"""
    if pd.isna(amount_str):
        return 0.0
    return float(str(amount_str).replace('.', '').replace(',', '.').strip())

def main():
    print("🔍 BORG RECONCILIATION ANALYSIS")
    print("="*80)
    
    # Load all data
    df = load_transactions()
    huizen, relaties, contracts = load_database_info()
    
    # Convert amounts
    df['Amount'] = df['AmountDC'].apply(convert_amount)
    
    # Filter borg transactions (GL code 1165)
    borg_df = df[df['GLAccountCodeDescriptionCode'] == 1165].copy()
    print(f"\n✅ Found {len(borg_df):,} borg transactions (GL 1165)")
    
    # ========================================
    # BORG BY PROPERTY (COST CENTER)
    # ========================================
    print("\n" + "="*80)
    print("BORG BY PROPERTY")
    print("="*80)
    
    borg_by_prop = borg_df.groupby(['CostCenterCodeDescriptionCode', 'CostCenterCodeDescriptionDescription']).agg({
        'Amount': ['sum', 'count'],
        'AccountCodeNameDescription': lambda x: ', '.join([str(v) for v in x.dropna().unique()[:3]]),
        'EntryDate': ['min', 'max']
    }).reset_index()
    borg_by_prop.columns = ['cc_code', 'cc_desc', 'total_borg', 'num_trans', 'relaties', 'first_date', 'last_date']
    
    print(f"\nProperties with borg transactions: {len(borg_by_prop)}")
    print("\nTop 20 by borg amount (absolute):")
    top20 = borg_by_prop.reindex(borg_by_prop['total_borg'].abs().sort_values(ascending=False).index).head(20)
    for _, row in top20.iterrows():
        print(f"   {row['cc_code']}: {row['cc_desc'][:40]}")
        print(f"      Total: €{row['total_borg']:,.2f} | Trans: {row['num_trans']} | Relatie: {row['relaties'][:50]}")
    
    # ========================================
    # BORG BY RELATIE (COMPANY)  
    # ========================================
    print("\n" + "="*80)
    print("BORG BY RELATIE (COMPANY)")
    print("="*80)
    
    borg_by_rel = borg_df.groupby(['AccountCodeNameCode', 'AccountCodeNameDescription']).agg({
        'Amount': ['sum', 'count'],
        'CostCenterCodeDescriptionCode': 'nunique',
        'EntryDate': ['min', 'max']
    }).reset_index()
    borg_by_rel.columns = ['rel_code', 'rel_naam', 'total_borg', 'num_trans', 'num_props', 'first_date', 'last_date']
    
    print(f"\nRelaties with borg transactions: {len(borg_by_rel)}")
    print("\nTop 20 relaties by borg amount (absolute):")
    top20_rel = borg_by_rel.reindex(borg_by_rel['total_borg'].abs().sort_values(ascending=False).index).head(20)
    for _, row in top20_rel.iterrows():
        rel_code = str(row['rel_code']).strip() if pd.notna(row['rel_code']) else 'N/A'
        rel_naam = str(row['rel_naam'])[:50] if pd.notna(row['rel_naam']) else 'N/A'
        print(f"   {rel_code}: {rel_naam}")
        print(f"      Total: €{row['total_borg']:,.2f} | Trans: {row['num_trans']} | Properties: {row['num_props']}")
    
    # ========================================
    # CROSS-REFERENCE WITH DATABASE
    # ========================================
    print("\n" + "="*80)
    print("CROSS-REFERENCE WITH DATABASE")
    print("="*80)
    
    # Normalize cost center codes to match object_id format
    borg_by_prop['object_id'] = borg_by_prop['cc_code'].astype(str).str.zfill(4)
    
    # Merge with huizen
    merged = huizen.merge(borg_by_prop[['object_id', 'total_borg', 'num_trans', 'relaties']], 
                          on='object_id', how='outer', indicator=True)
    
    # Calculate discrepancy
    merged['db_borg'] = merged['borg'].fillna(0)
    merged['trans_borg'] = merged['total_borg'].fillna(0)
    merged['discrepancy'] = merged['db_borg'] - merged['trans_borg'].abs()  # trans_borg is often negative
    
    print(f"\n📊 SUMMARY:")
    print(f"   Houses in database: {len(huizen)}")
    print(f"   Houses with borg_standaard set: {(huizen['borg'] > 0).sum()}")
    print(f"   Total DB borg: €{huizen['borg'].sum():,.2f}")
    print(f"   Properties with borg transactions: {len(borg_by_prop)}")
    print(f"   Total transaction borg (abs): €{borg_by_prop['total_borg'].abs().sum():,.2f}")
    
    # Properties in transactions but not in DB  
    in_trans_not_db = merged[merged['_merge'] == 'right_only']
    print(f"\n⚠️  In transactions but NOT in database: {len(in_trans_not_db)}")
    if len(in_trans_not_db) > 0:
        for _, row in in_trans_not_db.head(10).iterrows():
            print(f"   {row['object_id']}: €{row['trans_borg']:,.2f} ({row.get('relaties', 'N/A')})")
    
    # Large discrepancies
    big_diff = merged[(merged['_merge'] == 'both') & (abs(merged['discrepancy']) > 100)]
    print(f"\n⚠️  Discrepancies > €100: {len(big_diff)}")
    for _, row in big_diff.sort_values('discrepancy', key=abs, ascending=False).head(15).iterrows():
        print(f"   {row['object_id']}: {row['adres'][:30]}")
        print(f"      DB: €{row['db_borg']:,.2f} | Trans: €{row['trans_borg']:,.2f} | Diff: €{row['discrepancy']:,.2f}")
    
    # ========================================
    # BORG BY YEAR
    # ========================================
    print("\n" + "="*80)
    print("BORG TRANSACTIONS BY YEAR")
    print("="*80)
    
    borg_df['Year'] = borg_df['ReportingYearPeriod'].str.extract(r'(\d{4})')[0]
    borg_by_year = borg_df.groupby('Year').agg({
        'Amount': ['sum', 'count'],
        'CostCenterCodeDescriptionCode': 'nunique'
    }).reset_index()
    borg_by_year.columns = ['year', 'total', 'count', 'num_props']
    
    for _, row in borg_by_year.iterrows():
        print(f"   {row['year']}: €{row['total']:,.2f} | {row['count']} transactions | {row['num_props']} properties")
    
    # ========================================
    # EXPORT RESULTS
    # ========================================
    output_dir = BASE_DIR / "Shared/Output"
    output_dir.mkdir(exist_ok=True)
    
    # Export borg transactions
    borg_df.to_csv(output_dir / "borg_transactions.csv", index=False, encoding='utf-8-sig')
    
    # Export property summary
    borg_by_prop.to_csv(output_dir / "borg_by_property.csv", index=False, encoding='utf-8-sig')
    
    # Export cross-reference
    merged.to_csv(output_dir / "borg_crossref.csv", index=False, encoding='utf-8-sig')
    
    print(f"\n✅ Exported to {output_dir}")
    print("\n" + "="*80)
    print("✨ ANALYSIS COMPLETE!")
    print("="*80)

if __name__ == "__main__":
    main()
