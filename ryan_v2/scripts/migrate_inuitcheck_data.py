#!/usr/bin/env python3
"""
RYAN V2: In-Uit-Check Data Migration Script
============================================

Purpose: Migrate check-in/check-out data from Excel to SQLite database
Author: RyanRent Development Team
Date: 2025-12-22

Input: Shared/Sources/ryanrent_uitcheck_database_v4.xlsx
Output: Data inserted into ryanrent_mock.db (woning_cycli + woning_acties tables)

Usage:
    python scripts/migrate_inuitcheck_data.py
"""

import sqlite3
import pandas as pd
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ============================================================================
# Configuration
# ============================================================================

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
EXCEL_PATH = BASE_DIR / "Shared" / "Sources" / "ryanrent_uitcheck_database_v4.xlsx"
DB_PATH = BASE_DIR / "database" / "ryanrent_mock.db"

# Validation constants
VALID_STATUS = [
    'NIET_GESTART', 'VOORINSPECTIE_GEPLAND', 'VOORINSPECTIE_UITGEVOERD',
    'UITCHECK_GEPLAND', 'UITCHECK_UITGEVOERD', 'SCHOONMAAK_NODIG',
    'KLAAR_VOOR_INCHECK', 'INCHECK_GEPLAND', 'INCHECK_UITGEVOERD',
    'TERUG_NAAR_EIGENAAR', 'AFGEROND'
]

VALID_ACTIE_TYPE = [
    'VOORINSPECTIE', 'UITCHECK', 'SCHOONMAAK', 'INCHECK',
    'OVERDRACHT_EIGENAAR', 'REPARATIE'
]

VALID_KLANT_TYPE = ['TRADIRO', 'EXTERN', 'EIGENAAR']
VALID_BESTEMMING = ['OPNIEUW_VERHUREN', 'TERUG_NAAR_EIGENAAR']
VALID_JA_NEE = ['JA', 'NEE', 'ONBEKEND']
VALID_SLEUTEL_METHODE = ['PERSOONLIJK', 'IN_WONING_ACHTERGELATEN', 'ANDERS']

# ============================================================================
# Helper Functions
# ============================================================================

def generate_uuid() -> str:
    """Generate a UUID string for database primary keys."""
    return str(uuid.uuid4())


def validate_date(date_str: Optional[str]) -> bool:
    """Validate ISO date format: YYYY-MM-DD"""
    if pd.isna(date_str) or date_str is None:
        return True  # NULL is valid

    try:
        datetime.strptime(str(date_str).strip()[:10], '%Y-%m-%d')
        return True
    except:
        return False


def validate_datetime(datetime_str: Optional[str]) -> bool:
    """Validate ISO datetime format: YYYY-MM-DD HH:MM:SS"""
    if pd.isna(datetime_str) or datetime_str is None:
        return True  # NULL is valid

    try:
        datetime.strptime(str(datetime_str).strip(), '%Y-%m-%d %H:%M:%S')
        return True
    except:
        return False


def validate_hours(hours: Optional[float]) -> bool:
    """Validate hours field (must be >= 0 if not NULL)"""
    if pd.isna(hours) or hours is None:
        return True  # NULL is valid

    try:
        return float(hours) >= 0
    except:
        return False


def print_header(text: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_subheader(text: str):
    """Print formatted subsection header."""
    print(f"\n--- {text} ---")


# ============================================================================
# Validation Functions
# ============================================================================

def validate_cycli_row(row: pd.Series, idx: int, existing_huis_ids: set) -> Tuple[bool, Optional[str]]:
    """
    Validate a single cycle row from Excel.

    Returns: (is_valid, error_message)
    """
    # Check huis_id exists in database
    huis_id = row.get('huis_id')
    if pd.isna(huis_id) or not huis_id:
        return False, f"Row {idx}: Missing huis_id"

    if str(huis_id).strip() not in existing_huis_ids:
        return False, f"Row {idx}: huis_id '{huis_id}' not found in huizen table"

    # Check klant_type (use default if missing)
    klant_type = row.get('klant_type')
    if pd.isna(klant_type):
        klant_type = 'EXTERN'  # Default to EXTERN if not specified
    elif klant_type not in VALID_KLANT_TYPE:
        return False, f"Row {idx}: Invalid klant_type '{klant_type}'"

    # Check bestemming (use default if missing)
    bestemming = row.get('bestemming')
    if pd.isna(bestemming):
        bestemming = 'OPNIEUW_VERHUREN'  # Default to re-renting if not specified
    elif bestemming not in VALID_BESTEMMING:
        return False, f"Row {idx}: Invalid bestemming '{bestemming}'"

    if pd.isna(row.get('status')) or row.get('status') not in VALID_STATUS:
        return False, f"Row {idx}: Invalid status '{row.get('status')}'"

    # Check dates
    if not validate_date(row.get('einddatum_huurder')):
        return False, f"Row {idx}: Invalid einddatum_huurder format"

    if not validate_date(row.get('startdatum_nieuwe_huurder')):
        return False, f"Row {idx}: Invalid startdatum_nieuwe_huurder format"

    # Check is_actief
    is_actief = row.get('is_actief')
    if pd.isna(is_actief):
        return False, f"Row {idx}: Missing is_actief"

    # Convert JA/NEE to 1/0
    if isinstance(is_actief, str):
        if is_actief.upper() not in ['JA', 'NEE', '1', '0']:
            return False, f"Row {idx}: Invalid is_actief '{is_actief}'"

    return True, None


def validate_acties_row(row: pd.Series, idx: int) -> Tuple[bool, Optional[str]]:
    """
    Validate a single action row from Excel.

    Returns: (is_valid, error_message)
    """
    # Check required fields
    if pd.isna(row.get('object_id')) or not row.get('object_id'):
        return False, f"Row {idx}: Missing object_id (needed for cyclus lookup)"

    if pd.isna(row.get('actie_type')) or row.get('actie_type') not in VALID_ACTIE_TYPE:
        return False, f"Row {idx}: Invalid actie_type '{row.get('actie_type')}'"

    # Check dates
    if not validate_datetime(row.get('gepland_op')):
        return False, f"Row {idx}: Invalid gepland_op format"

    if not validate_datetime(row.get('uitgevoerd_op')):
        return False, f"Row {idx}: Invalid uitgevoerd_op format"

    # Check hours
    if not validate_hours(row.get('verwachte_schoonmaak_uren')):
        return False, f"Row {idx}: Invalid verwachte_schoonmaak_uren (must be >= 0)"

    if not validate_hours(row.get('werkelijke_schoonmaak_uren')):
        return False, f"Row {idx}: Invalid werkelijke_schoonmaak_uren (must be >= 0)"

    # Check enum fields (if provided)
    fotos = row.get('fotos_gemaakt')
    if not pd.isna(fotos) and fotos not in VALID_JA_NEE:
        return False, f"Row {idx}: Invalid fotos_gemaakt '{fotos}'"

    issues = row.get('issues_gevonden')
    if not pd.isna(issues) and issues not in VALID_JA_NEE:
        return False, f"Row {idx}: Invalid issues_gevonden '{issues}'"

    sleutels = row.get('sleutels_bevestigd')
    if not pd.isna(sleutels) and sleutels not in VALID_JA_NEE:
        return False, f"Row {idx}: Invalid sleutels_bevestigd '{sleutels}'"

    methode = row.get('sleuteloverdracht_methode')
    if not pd.isna(methode) and methode not in VALID_SLEUTEL_METHODE:
        return False, f"Row {idx}: Invalid sleuteloverdracht_methode '{methode}'"

    return True, None


# ============================================================================
# Database Functions
# ============================================================================

def get_existing_huis_ids(conn: sqlite3.Connection) -> set:
    """Get all existing object_ids from huizen table."""
    cursor = conn.cursor()
    cursor.execute("SELECT object_id FROM huizen")
    return {str(row[0]) for row in cursor.fetchall()}


def insert_cycli(conn: sqlite3.Connection, df_cycli: pd.DataFrame, existing_huis_ids: set) -> Dict[str, str]:
    """
    Insert validated cycles into database and return mapping.

    Returns: Dict[huis_id → cyclus_id]
    """
    cursor = conn.cursor()
    mapping = {}
    inserted_count = 0
    error_count = 0

    print_subheader("Inserting Cycli")

    for idx, row in df_cycli.iterrows():
        # Validate
        is_valid, error_msg = validate_cycli_row(row, idx, existing_huis_ids)
        if not is_valid:
            print(f"  ❌ SKIP: {error_msg}")
            error_count += 1
            continue

        # Generate new UUID
        cyclus_id = generate_uuid()
        huis_id = str(row['huis_id']).strip()

        # Convert is_actief to integer
        is_actief_raw = row.get('is_actief')
        if isinstance(is_actief_raw, str):
            is_actief = 1 if is_actief_raw.upper() in ['JA', '1'] else 0
        else:
            is_actief = int(is_actief_raw)

        # Apply defaults for missing values
        klant_type = row.get('klant_type') if not pd.isna(row.get('klant_type')) else 'EXTERN'
        bestemming = row.get('bestemming') if not pd.isna(row.get('bestemming')) else 'OPNIEUW_VERHUREN'

        # Convert dates to strings (pandas returns Timestamp objects)
        einddatum = row.get('einddatum_huurder')
        if not pd.isna(einddatum):
            einddatum = pd.to_datetime(einddatum).strftime('%Y-%m-%d') if hasattr(einddatum, 'strftime') else str(einddatum)[:10]
        else:
            einddatum = None

        startdatum = row.get('startdatum_nieuwe_huurder')
        if not pd.isna(startdatum):
            startdatum = pd.to_datetime(startdatum).strftime('%Y-%m-%d') if hasattr(startdatum, 'strftime') else str(startdatum)[:10]
        else:
            startdatum = None

        # Prepare data (convert NaN to None)
        data = {
            'cyclus_id': cyclus_id,
            'huis_id': huis_id,
            'is_actief': is_actief,
            'klant_type': klant_type,
            'bestemming': bestemming,
            'status': row['status'],
            'einddatum_huurder': einddatum,
            'startdatum_nieuwe_huurder': startdatum,
            'interne_opmerking': row.get('interne_opmerking') if not pd.isna(row.get('interne_opmerking')) else None,
        }

        # Insert
        try:
            cursor.execute("""
                INSERT INTO woning_cycli (
                    cyclus_id, huis_id, is_actief, klant_type, bestemming, status,
                    einddatum_huurder, startdatum_nieuwe_huurder, interne_opmerking
                ) VALUES (
                    :cyclus_id, :huis_id, :is_actief, :klant_type, :bestemming, :status,
                    :einddatum_huurder, :startdatum_nieuwe_huurder, :interne_opmerking
                )
            """, data)

            # Store mapping
            mapping[huis_id] = cyclus_id
            inserted_count += 1

            print(f"  ✅ Inserted: huis_id={huis_id[:8]}... → cyclus_id={cyclus_id[:8]}...")

        except Exception as e:
            print(f"  ❌ ERROR inserting row {idx}: {e}")
            error_count += 1

    conn.commit()

    print(f"\n  📊 Summary: {inserted_count} inserted, {error_count} errors")
    return mapping


def insert_acties(conn: sqlite3.Connection, df_acties: pd.DataFrame, huis_to_cyclus: Dict[str, str]):
    """Insert validated actions into database."""
    cursor = conn.cursor()
    inserted_count = 0
    error_count = 0

    print_subheader("Inserting Acties")

    for idx, row in df_acties.iterrows():
        # Validate
        is_valid, error_msg = validate_acties_row(row, idx)
        if not is_valid:
            print(f"  ❌ SKIP: {error_msg}")
            error_count += 1
            continue

        # Lookup cyclus_id via huis_id (object_id)
        huis_id = str(row['object_id']).strip()
        cyclus_id = huis_to_cyclus.get(huis_id)

        if not cyclus_id:
            print(f"  ❌ SKIP Row {idx}: No cyclus found for huis_id '{huis_id}'")
            error_count += 1
            continue

        # Use existing actie_id or generate new
        actie_id = row.get('actie_id')
        if pd.isna(actie_id) or not actie_id:
            actie_id = generate_uuid()
        else:
            actie_id = str(actie_id).strip()

        # Convert datetimes to strings (pandas returns Timestamp objects)
        gepland_op = row.get('gepland_op')
        if not pd.isna(gepland_op):
            gepland_op = pd.to_datetime(gepland_op).strftime('%Y-%m-%d %H:%M:%S') if hasattr(gepland_op, 'strftime') else str(gepland_op)[:19]
        else:
            gepland_op = None

        uitgevoerd_op = row.get('uitgevoerd_op')
        if not pd.isna(uitgevoerd_op):
            uitgevoerd_op = pd.to_datetime(uitgevoerd_op).strftime('%Y-%m-%d %H:%M:%S') if hasattr(uitgevoerd_op, 'strftime') else str(uitgevoerd_op)[:19]
        else:
            uitgevoerd_op = None

        # Prepare data (convert NaN to None)
        data = {
            'actie_id': actie_id,
            'cyclus_id': cyclus_id,
            'actie_type': row['actie_type'],
            'gepland_op': gepland_op,
            'uitgevoerd_op': uitgevoerd_op,
            'uitgevoerd_door': row.get('uitgevoerd_door') if not pd.isna(row.get('uitgevoerd_door')) else None,
            'fotos_gemaakt': row.get('fotos_gemaakt') if not pd.isna(row.get('fotos_gemaakt')) else None,
            'issues_gevonden': row.get('issues_gevonden') if not pd.isna(row.get('issues_gevonden')) else None,
            'verwachte_schoonmaak_uren': row.get('verwachte_schoonmaak_uren') if not pd.isna(row.get('verwachte_schoonmaak_uren')) else None,
            'werkelijke_schoonmaak_uren': row.get('werkelijke_schoonmaak_uren') if not pd.isna(row.get('werkelijke_schoonmaak_uren')) else None,
            'sleutels_bevestigd': row.get('sleutels_bevestigd') if not pd.isna(row.get('sleutels_bevestigd')) else None,
            'sleuteloverdracht_methode': row.get('sleuteloverdracht_methode') if not pd.isna(row.get('sleuteloverdracht_methode')) else None,
            'opmerking': row.get('opmerking') if not pd.isna(row.get('opmerking')) else None,
        }

        # Insert
        try:
            cursor.execute("""
                INSERT INTO woning_acties (
                    actie_id, cyclus_id, actie_type,
                    gepland_op, uitgevoerd_op, uitgevoerd_door,
                    fotos_gemaakt, issues_gevonden,
                    verwachte_schoonmaak_uren, werkelijke_schoonmaak_uren,
                    sleutels_bevestigd, sleuteloverdracht_methode,
                    opmerking
                ) VALUES (
                    :actie_id, :cyclus_id, :actie_type,
                    :gepland_op, :uitgevoerd_op, :uitgevoerd_door,
                    :fotos_gemaakt, :issues_gevonden,
                    :verwachte_schoonmaak_uren, :werkelijke_schoonmaak_uren,
                    :sleutels_bevestigd, :sleuteloverdracht_methode,
                    :opmerking
                )
            """, data)

            inserted_count += 1
            print(f"  ✅ Inserted: actie_id={actie_id[:8]}..., type={data['actie_type']}")

        except Exception as e:
            print(f"  ❌ ERROR inserting row {idx}: {e}")
            error_count += 1

    conn.commit()

    print(f"\n  📊 Summary: {inserted_count} inserted, {error_count} errors")


def run_post_migration_validation(conn: sqlite3.Connection):
    """Run validation queries after migration."""
    cursor = conn.cursor()

    print_subheader("Post-Migration Validation")

    # Check 1: Duplicate active cycles
    cursor.execute("""
        SELECT huis_id, COUNT(*) as count
        FROM woning_cycli
        WHERE is_actief = 1
        GROUP BY huis_id
        HAVING COUNT(*) > 1
    """)
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"  ⚠️  WARNING: {len(duplicates)} houses have multiple active cycles!")
        for huis_id, count in duplicates:
            print(f"      - huis_id={huis_id}: {count} active cycles")
    else:
        print("  ✅ No duplicate active cycles")

    # Check 2: Orphaned actions
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM woning_acties a
        LEFT JOIN woning_cycli c ON a.cyclus_id = c.cyclus_id
        WHERE c.cyclus_id IS NULL
    """)
    orphaned = cursor.fetchone()[0]
    if orphaned > 0:
        print(f"  ❌ ERROR: {orphaned} orphaned actions (no matching cyclus)")
    else:
        print("  ✅ No orphaned actions")

    # Check 3: Total counts
    cursor.execute("SELECT COUNT(*) FROM woning_cycli")
    total_cycli = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM woning_cycli WHERE is_actief = 1")
    active_cycli = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM woning_acties")
    total_acties = cursor.fetchone()[0]

    print(f"\n  📊 Database Summary:")
    print(f"      - Total cycli: {total_cycli} ({active_cycli} active)")
    print(f"      - Total acties: {total_acties}")

    # Check 4: Status-check (if view exists)
    try:
        cursor.execute("""
            SELECT status_severity, COUNT(*) as count
            FROM v_status_check
            GROUP BY status_severity
        """)
        status_results = cursor.fetchall()
        if status_results:
            print(f"\n  📋 Status Check Results:")
            for severity, count in status_results:
                icon = "❌" if severity == "BLOCKER" else "⚠️" if severity == "WARNING" else "✅"
                print(f"      {icon} {severity}: {count} cycles")
    except:
        print("\n  ℹ️  Status-check view not available (run views_inuitcheck.sql first)")


# ============================================================================
# Main Migration Flow
# ============================================================================

def main():
    """Main migration workflow."""

    print_header("RYAN V2: In-Uit-Check Data Migration")
    print(f"\n  Excel: {EXCEL_PATH.name}")
    print(f"  Database: {DB_PATH.name}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # -------------------------------------------------------------------------
    # Step 1: Load Excel
    # -------------------------------------------------------------------------
    print_header("Step 1: Load Excel Data")

    if not EXCEL_PATH.exists():
        print(f"\n  ❌ ERROR: Excel file not found at: {EXCEL_PATH}")
        return

    try:
        print(f"\n  📂 Reading: {EXCEL_PATH.name}...")
        df_cycli = pd.read_excel(EXCEL_PATH, sheet_name='WONING_CYCLI')
        df_acties = pd.read_excel(EXCEL_PATH, sheet_name='ACTIES')

        print(f"  ✅ Loaded:")
        print(f"      - WONING_CYCLI: {len(df_cycli)} rows")
        print(f"      - ACTIES: {len(df_acties)} rows")

    except Exception as e:
        print(f"\n  ❌ ERROR loading Excel: {e}")
        return

    # -------------------------------------------------------------------------
    # Step 2: Connect to Database
    # -------------------------------------------------------------------------
    print_header("Step 2: Connect to Database")

    if not DB_PATH.exists():
        print(f"\n  ❌ ERROR: Database not found at: {DB_PATH}")
        print("     Run schema_inuitcheck.sql first!")
        return

    try:
        conn = sqlite3.connect(str(DB_PATH))
        print(f"  ✅ Connected to: {DB_PATH.name}")

        # Check if tables exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='woning_cycli'")
        if not cursor.fetchone():
            print("\n  ❌ ERROR: Table 'woning_cycli' not found!")
            print("     Run schema_inuitcheck.sql first!")
            conn.close()
            return

        print("  ✅ Tables exist: woning_cycli, woning_acties")

    except Exception as e:
        print(f"\n  ❌ ERROR connecting to database: {e}")
        return

    # -------------------------------------------------------------------------
    # Step 3: Get Existing House IDs
    # -------------------------------------------------------------------------
    print_header("Step 3: Validate Foreign Keys")

    existing_huis_ids = get_existing_huis_ids(conn)
    print(f"\n  ✅ Found {len(existing_huis_ids)} existing houses in huizen table")

    # -------------------------------------------------------------------------
    # Step 4: Insert Cycli
    # -------------------------------------------------------------------------
    print_header("Step 4: Migrate Cycli")

    huis_to_cyclus = insert_cycli(conn, df_cycli, existing_huis_ids)

    if not huis_to_cyclus:
        print("\n  ⚠️  No cycles inserted, skipping actions migration")
        conn.close()
        return

    # -------------------------------------------------------------------------
    # Step 5: Insert Acties
    # -------------------------------------------------------------------------
    print_header("Step 5: Migrate Acties")

    insert_acties(conn, df_acties, huis_to_cyclus)

    # -------------------------------------------------------------------------
    # Step 6: Post-Migration Validation
    # -------------------------------------------------------------------------
    print_header("Step 6: Post-Migration Validation")

    run_post_migration_validation(conn)

    # -------------------------------------------------------------------------
    # Completion
    # -------------------------------------------------------------------------
    print_header("Migration Complete")
    print(f"\n  ✅ Migration finished successfully!")
    print(f"  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n  Next steps:")
    print("    1. Review validation results above")
    print("    2. Test queries with RYAN agent")
    print("    3. Check v_status_check view for blockers")
    print("\n")

    conn.close()


if __name__ == "__main__":
    main()
