#!/usr/bin/env python3
"""
Round all monetary values in the database to 0 decimal places (integers).
Excludes: meter readings, percentages, hours, oppervlakte, and similar non-monetary REAL columns.
"""
import sqlite3

db_path = "database/ryanrent_mock.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Define tables and their monetary columns (excluding meters, percentages, hours, oppervlakte)
tables_columns = {
    "boekingen": [
        "totale_huur_factuur", "betaalde_borg", "voorschot_gwe", "voorschot_schoonmaak"
    ],
    "borg_transacties": [
        "bedrag"
    ],
    "checkouts": [
        "schade_geschat", "schoonmaak_kosten"
    ],
    "contract_regels": [
        "prijs_pp_pw", "totaal_maand_bedrag"
    ],
    "damages": [
        "estimated_cost"
        # btw_percentage excluded (percentage, not monetary)
    ],
    "debiteuren_standen": [
        "oorspronkelijk_bedrag", "openstaand_bedrag"
    ],
    "eindafrekeningen": [
        "borg_terug", "gwe_totaal_incl", "totaal_eindafrekening",
        "schoonmaak_kosten", "schade_totaal_kosten", "extra_voorschot_bedrag",
        "voorschot_gwe_incl"
        # meter values and hours/uurtarief excluded
    ],
    "huizen": [
        "voorschot_gwe", "internet", "meubilering", "tuinonderhoud",
        "aanschaf_inventaris", "kosten_gem_heffingen_standaard",
        "kosten_operationeel_standaard", "borg", "stoffering",
        "eindschoonmaak", "vve_kosten"
        # oppervlakte excluded (m2, not monetary)
    ],
    "huizen_archief": [
        "voorschot_gwe", "internet", "meubilering", "tuinonderhoud",
        "aanschaf_inventaris", "kosten_gem_heffingen_standaard",
        "kosten_operationeel_standaard", "borg", "stoffering",
        "eindschoonmaak"
        # oppervlakte excluded (m2, not monetary)
    ],
    "inhuur_contracten": [
        "kale_huur", "servicekosten", "voorschot_gwe", "afval_kosten",
        "totale_huur", "borg", "inhuur_prijs_excl_btw",
        "inhuur_prijs_incl_btw", "kale_inhuurprijs"
    ],
    "klant_parameters": [
        "prijs_pp_pw_override"
    ],
    "meter_readings": [
        # All excluded - meter values and tariffs need precision
    ],
    "parameters": [
        "prijs_pp_pw"
    ],
    "relaties": [
        # min_marge_pct, max_marge_pct excluded (percentages)
    ],
    "team_beschikbaarheid": [
        # Hours excluded
    ],
    "teams": [
        # Hours excluded
    ],
    "verhuur_contracten": [
        "kale_huur", "servicekosten", "borg", "voorschot_gwe",
        "kosten_internet_standaard", "kosten_inventaris_standaard",
        "kosten_afval_standaard", "kosten_onderhoud_standaard",
        "kosten_aanschaf_standaard", "kosten_gem_heffingen_standaard",
        "kosten_operationeel_standaard", "minimum_verhuur_prijs",
        "verhuur_incl_btw", "verhuur_excl_btw", "overige_kosten",
        "afval_kosten", "marge"
        # target_margin, actual_margin excluded (percentages)
    ],
    "woning_acties": [
        # Hours excluded
    ]
}

print("🔄 Rounding all monetary values to 2 decimals...\n")

total_updated = 0
for table, columns in tables_columns.items():
    if not columns:
        continue
    print(f"📋 Table: {table}")
    for col in columns:
        try:
            sql = f"UPDATE {table} SET {col} = ROUND({col}, 2) WHERE {col} IS NOT NULL"
            cursor.execute(sql)
            rows_affected = cursor.rowcount
            total_updated += rows_affected
            print(f"   ✓ {col}: {rows_affected} rows updated")
        except sqlite3.OperationalError as e:
            print(f"   ⚠️ {col}: Skipped ({e})")
    print()

conn.commit()
conn.close()

print(f"✅ Done! {total_updated} total values have been rounded to 2 decimals.")
