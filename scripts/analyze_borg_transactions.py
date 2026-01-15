#!/usr/bin/env python3
"""
Analyze all financial transactions to identify borg (deposit) payments.
Cross-reference with the huizen table to find discrepancies.
"""

import pandas as pd
import sqlite3
from pathlib import Path
import re

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
    print(f"Columns: {list(df.columns)}")
    return df

def load_database_info():
    """Load houses and relaties from database"""
    print(f"\nLoading data from database...")
    conn = sqlite3.connect(DB_PATH)
    
    # Get houses with borg
    huizen_query = """
    SELECT 
        h.id as house_id,
        h.object_id,
        h.adres,
        h.plaats,
        h.borg_standaard as borg
    FROM huizen h
    ORDER BY h.object_id
    """
    huizen = pd.read_sql_query(huizen_query, conn)
    print(f"Loaded {len(huizen)} houses from database")
    
    # Get relaties (companies)
    relaties_query = """
    SELECT 
        r.id as relatie_id,
        r.naam
    FROM relaties r
    """
    relaties = pd.read_sql_query(relaties_query, conn)
    print(f"Loaded {len(relaties)} relaties from database")
    
    # Get contracts linking houses to relaties
    contracts_query = """
    SELECT 
        vc.id as contract_id,
        vc.relatie_id,
        vc.house_id,
        vc.start_date,
        vc.end_date,
        vc.borg_override,
        h.object_id,
        r.naam as relatie_naam
    FROM verhuur_contracten vc
    JOIN huizen h ON vc.house_id = h.id
    JOIN relaties r ON vc.relatie_id = r.id
    """
    contracts = pd.read_sql_query(contracts_query, conn)
    print(f"Loaded {len(contracts)} contracts from database")
    
    conn.close()
    return huizen, relaties, contracts

def identify_borg_transactions(df):
    """Find all potential borg-related transactions using GL accounts"""
    print("\n" + "="*80)
    print("ANALYZING TRANSACTIONS FOR BORG PAYMENTS")
    print("="*80)
    
    # First, let's see all unique GL accounts to understand the data
    print("\nUnique GL Account Descriptions containing 'borg' or deposit-related terms:")
    
    borg_keywords = ['borg', 'waarborgsom', 'deposit', 'zekerheid', 'garantie', '1530']
    pattern = '|'.join(borg_keywords)
    
    # Search in GL account descriptions
    gl_mask = df['GLAccountCodeDescriptionDescription'].str.contains(pattern, case=False, na=False)
    gl_code_mask = df['GLAccountCodeDescriptionCode'].str.contains('1530|2450', na=False)  # Common borg GL codes
    
    # Combined mask
    borg_mask = gl_mask | gl_code_mask
    
    borg_trans = df[borg_mask].copy()
    
    if len(borg_trans) == 0:
        print("No direct borg transactions found. Let's look at all GL accounts...")
        gl_summary = df.groupby(['GLAccountCodeDescriptionCode', 'GLAccountCodeDescriptionDescription']).size()
        print("\nAll GL accounts (first 50):")
        for (code, desc), count in gl_summary.head(50).items():
            print(f"   {code}: {desc} ({count} transactions)")
        return borg_trans
    
    print(f"\nFound {len(borg_trans)} potential borg transactions")
    
    # Convert amount to numeric
    borg_trans['Amount'] = borg_trans['AmountDC'].str.replace('.', '').str.replace(',', '.').astype(float)
    
    return borg_trans

def analyze_by_cost_center(df):
    """Analyze transactions by cost center (property)"""
    print("\n" + "="*80)
    print("ANALYZING BY COST CENTER (PROPERTY)")
    print("="*80)
    
    # Convert amount
    df_copy = df.copy()
    df_copy['Amount'] = df_copy['AmountDC'].str.replace('.', '').str.replace(',', '.').astype(float)
    
    # Group by cost center
    summary = df_copy.groupby(['CostCenterCodeDescriptionCode', 'CostCenterCodeDescriptionDescription']).agg({
        'Amount': ['sum', 'count', 'mean'],
        'EntryDate': ['min', 'max']
    }).reset_index()
    
    summary.columns = ['_'.join(col).strip('_') for col in summary.columns]
    summary = summary.rename(columns={
        'CostCenterCodeDescriptionCode_': 'object_id',
        'CostCenterCodeDescriptionDescription_': 'description',
        'Amount_sum': 'total_amount',
        'Amount_count': 'num_transactions',
        'Amount_mean': 'avg_amount',
        'EntryDate_min': 'first_date',
        'EntryDate_max': 'last_date'
    })
    
    print(f"\nFound {len(summary)} unique cost centers (properties)")
    print("\nTop 20 cost centers by total amount:")
    for idx, row in summary.nlargest(20, 'total_amount').iterrows():
        print(f"   {row['object_id']}: {row['description']}")
        print(f"      Total: €{row['total_amount']:,.2f} | Transactions: {row['num_transactions']:,}")
    
    return summary

def analyze_by_relatie(df):
    """Analyze transactions by relatie (company/person)"""
    print("\n" + "="*80)
    print("ANALYZING BY RELATIE (COMPANY/PERSON)")
    print("="*80)
    
    # Convert amount
    df_copy = df.copy()
    df_copy['Amount'] = df_copy['AmountDC'].str.replace('.', '').str.replace(',', '.').astype(float)
    
    # Group by account (relatie)
    summary = df_copy.groupby(['AccountCodeNameCode', 'AccountCodeNameDescription']).agg({
        'Amount': ['sum', 'count'],
        'EntryDate': ['min', 'max'],
        'CostCenterCodeDescriptionCode': 'nunique'  # Number of unique properties
    }).reset_index()
    
    summary.columns = ['_'.join(col).strip('_') for col in summary.columns]
    summary = summary.rename(columns={
        'AccountCodeNameCode_': 'relatie_code',
        'AccountCodeNameDescription_': 'relatie_naam',
        'Amount_sum': 'total_amount',
        'Amount_count': 'num_transactions',
        'EntryDate_min': 'first_date',
        'EntryDate_max': 'last_date',
        'CostCenterCodeDescriptionCode_nunique': 'num_properties'
    })
    
    print(f"\nFound {len(summary)} unique relaties (companies/persons)")
    print("\nTop 20 relaties by total amount:")
    for idx, row in summary.nlargest(20, 'total_amount').iterrows():
        print(f"   {row['relatie_code'].strip()}: {row['relatie_naam']}")
        print(f"      Total: €{row['total_amount']:,.2f} | Transactions: {row['num_transactions']:,} | Properties: {row['num_properties']}")
    
    return summary

def analyze_gl_accounts(df):
    """Analyze all GL accounts to understand transaction types"""
    print("\n" + "="*80)
    print("GL ACCOUNT ANALYSIS")
    print("="*80)
    
    # Convert amount
    df_copy = df.copy()
    df_copy['Amount'] = df_copy['AmountDC'].str.replace('.', '').str.replace(',', '.').astype(float)
    
    # Group by GL account
    summary = df_copy.groupby(['GLAccountCodeDescriptionCode', 'GLAccountCodeDescriptionDescription']).agg({
        'Amount': ['sum', 'count']
    }).reset_index()
    
    # Flatten column names properly
    summary.columns = ['gl_code', 'gl_desc', 'total_amount', 'num_transactions']
    
    print(f"\nFound {len(summary)} unique GL accounts")
    
    # Look for borg-related accounts
    borg_accounts = summary[
        summary['gl_desc'].str.contains('borg|waarborgsom|deposit|zekerheid', case=False, na=False) |
        summary['gl_code'].isin(['1530', '2450', '1531', '2451'])  # Common borg codes
    ]
    
    if len(borg_accounts) > 0:
        print("\n🔍 BORG-RELATED GL ACCOUNTS FOUND:")
        for idx, row in borg_accounts.iterrows():
            print(f"   {row['gl_code']}: {row['gl_desc']}")
            print(f"      Total: €{row['total_amount']:,.2f} | Transactions: {row['num_transactions']:,}")
    else:
        print("\n⚠️  No direct borg GL accounts found. Searching for balance sheet accounts...")
        # Balance sheet accounts typically in 1xxx or 2xxx range
        balance_accounts = summary[summary['gl_code'].str.match(r'^[12]\d{3}$', na=False)]
        print("\nBalance sheet accounts (potential borg locations):")
        for idx, row in balance_accounts.nlargest(30, 'total_amount').iterrows():
            print(f"   {row['gl_code']}: {row['gl_desc']} - €{row['total_amount']:,.2f}")
    
    return summary

def find_borg_by_amount(df, huizen):
    """Try to find borg transactions by matching standard borg amounts"""
    print("\n" + "="*80)
    print("SEARCHING FOR BORG BY AMOUNT MATCHING")
    print("="*80)
    
    # Get standard borg amounts from database
    standard_borgs = huizen[huizen['borg'] > 0]['borg'].unique()
    print(f"\nStandard borg amounts in database: {sorted(standard_borgs)}")
    
    # Convert transaction amounts
    df_copy = df.copy()
    df_copy['Amount'] = df_copy['AmountDC'].str.replace('.', '').str.replace(',', '.').astype(float)
    
    # Look for exact matches
    matches = df_copy[df_copy['Amount'].isin(standard_borgs)]
    
    if len(matches) > 0:
        print(f"\nFound {len(matches)} transactions matching standard borg amounts:")
        amount_summary = matches.groupby(['Amount', 'GLAccountCodeDescriptionCode', 'GLAccountCodeDescriptionDescription']).size()
        for (amount, gl_code, gl_desc), count in amount_summary.items():
            print(f"   €{amount:,.2f} | {gl_code}: {gl_desc} | {count} transactions")
    else:
        print("No exact matches found for standard borg amounts")
    
    return matches

def generate_comprehensive_report(df, huizen, relaties, contracts):
    """Generate a comprehensive cross-reference report"""
    print("\n" + "="*80)
    print("COMPREHENSIVE CROSS-REFERENCE REPORT")
    print("="*80)
    
    # Convert amounts
    df_copy = df.copy()
    df_copy['Amount'] = df_copy['AmountDC'].str.replace('.', '').str.replace(',', '.').astype(float)
    
    # Get property-level summary from transactions
    prop_trans = df_copy.groupby(['CostCenterCodeDescriptionCode']).agg({
        'Amount': 'sum',
        'AccountCodeNameDescription': lambda x: list(x.unique())[:5]  # Top relaties
    }).reset_index()
    prop_trans.columns = ['object_id', 'total_trans_amount', 'relaties']
    
    # Merge with database
    merged = huizen.merge(prop_trans, on='object_id', how='left')
    
    # Properties with borg in DB but no transactions
    missing_trans = merged[(merged['borg'] > 0) & (merged['total_trans_amount'].isna())]
    
    # Properties with transactions but no borg in DB
    missing_borg = merged[(merged['borg'].isna() | (merged['borg'] == 0)) & 
                          (merged['total_trans_amount'] > 0)]
    
    print(f"\n📊 SUMMARY:")
    print(f"   Properties in database: {len(huizen)}")
    print(f"   Properties with borg set: {(huizen['borg'] > 0).sum()}")
    print(f"   Properties in transactions: {len(prop_trans)}")
    print(f"   Properties with borg but no transactions: {len(missing_trans)}")
    
    if len(missing_trans) > 0:
        print(f"\n⚠️  PROPERTIES WITH BORG BUT NO MATCHING TRANSACTIONS (first 10):")
        for idx, row in missing_trans.head(10).iterrows():
            print(f"   {row['object_id']}: {row['adres']}, {row['plaats']} - Borg: €{row['borg']:,.2f}")
    
    return merged

def export_results(df, huizen, relaties):
    """Export analysis results to CSV"""
    output_dir = BASE_DIR / "Shared/Output"
    output_dir.mkdir(exist_ok=True)
    
    # Convert amounts
    df_copy = df.copy()
    df_copy['Amount'] = df_copy['AmountDC'].str.replace('.', '').str.replace(',', '.').astype(float)
    
    # Full transaction export with object_id normalized
    trans_file = output_dir / "all_transactions_analyzed.csv"
    df_copy['object_id_normalized'] = df_copy['CostCenterCodeDescriptionCode'].str.zfill(4)
    df_copy.to_csv(trans_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ Exported all transactions to: {trans_file}")
    
    # Property-relatie mapping
    prop_relatie = df_copy.groupby(['CostCenterCodeDescriptionCode', 'CostCenterCodeDescriptionDescription', 
                                     'AccountCodeNameCode', 'AccountCodeNameDescription']).agg({
        'Amount': ['sum', 'count'],
        'EntryDate': ['min', 'max']
    }).reset_index()
    prop_relatie.columns = ['_'.join(col).strip('_') for col in prop_relatie.columns]
    
    mapping_file = output_dir / "property_relatie_mapping.csv"
    prop_relatie.to_csv(mapping_file, index=False, encoding='utf-8-sig')
    print(f"✅ Exported property-relatie mapping to: {mapping_file}")

def main():
    print("🔍 BORG RECONCILIATION ANALYSIS - COMPREHENSIVE AUDIT")
    print("="*80)
    
    # Load all data
    transactions = load_transactions()
    huizen, relaties, contracts = load_database_info()
    
    # Run all analyses
    gl_summary = analyze_gl_accounts(transactions)
    borg_trans = identify_borg_transactions(transactions)
    cost_center_summary = analyze_by_cost_center(transactions)
    relatie_summary = analyze_by_relatie(transactions)
    
    # Try amount matching
    borg_matches = find_borg_by_amount(transactions, huizen)
    
    # Cross-reference
    merged = generate_comprehensive_report(transactions, huizen, relaties, contracts)
    
    # Export
    export_results(transactions, huizen, relaties)
    
    print("\n" + "="*80)
    print("✨ ANALYSIS COMPLETE!")
    print("="*80)

if __name__ == "__main__":
    main()
