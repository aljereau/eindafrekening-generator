#!/usr/bin/env python3
"""
Create a complete test scenario with GWE overflow and extra cleaning hours
All fields are filled, calculations are done by Python
"""

import openpyxl
from datetime import date, timedelta
from pathlib import Path

def set_named_value(wb, name: str, value):
    """Set value to a named range in the workbook"""
    try:
        if name not in wb.defined_names:
            print(f"   ⚠️  Warning: Named range '{name}' not found")
            return False

        defn = wb.defined_names[name]
        destinations = list(defn.destinations)
        if not destinations:
            return False

        sheet_name, cell_ref = destinations[0]
        ws = wb[sheet_name]
        cell_ref = cell_ref.replace('$', '')
        ws[cell_ref] = value
        return True
    except Exception as e:
        print(f"   ⚠️  Error setting '{name}': {e}")
        return False


def create_complete_overflow_scenario():
    """
    Complete overflow scenario with all fields filled:
    - Borg: €500 prepaid, €500 used (damage) → €0 return
    - GWE: €300 prepaid, €485 actual → Customer owes €185
    - Schoonmaak: €250 prepaid (5 hours), 7.5 hours used → Customer owes €125 for extra 2.5 hours
    Total: Customer owes €310
    """
    print("\n📝 Creating Complete Overflow Test Scenario")
    print("=" * 70)

    src = Path("input_template.xlsx")
    dst = Path("test_complete_overflow.xlsx")

    wb = openpyxl.load_workbook(src)

    # === CLIENT INFO ===
    print("\n1️⃣  Client Information")
    set_named_value(wb, 'Klantnaam', "Familie Janssen")
    set_named_value(wb, 'Email', "m.janssen@email.nl")
    set_named_value(wb, 'Telefoonnummer', "06-11223344")
    set_named_value(wb, 'Contactpersoon', "Anna van RyanRent")
    print("   ✓ Client info set")

    # === OBJECT INFO ===
    print("\n2️⃣  Property Information")
    set_named_value(wb, 'Object_adres', "Kustlaan 88B, 4321AB Zandvoort")
    set_named_value(wb, 'Object_ID', "RR-2024-088")
    set_named_value(wb, 'Unit_nr', "88B")
    set_named_value(wb, 'Plaats', "Zandvoort")
    set_named_value(wb, 'Postcode', "4321AB")
    print("   ✓ Property info set")

    # === PERIOD ===
    print("\n3️⃣  Stay Period")
    checkin = date(2025, 7, 15)
    checkout = checkin + timedelta(days=14)  # 14 days
    set_named_value(wb, 'Incheck_datum', checkin)
    set_named_value(wb, 'Uitcheck_datum', checkout)
    set_named_value(wb, 'Aantal_dagen', 14)
    print(f"   ✓ Period: {checkin} → {checkout} (14 days)")

    # === DEPOSITS ===
    print("\n4️⃣  Prepaid Amounts (Voorschotten)")
    set_named_value(wb, 'Voorschot_borg', 500)
    set_named_value(wb, 'Voorschot_GWE', 300)
    set_named_value(wb, 'Voorschot_schoonmaak', 250)
    print("   ✓ Borg: €500")
    print("   ✓ GWE: €300")
    print("   ✓ Schoonmaak: €250")

    # === BORG (DEPOSIT) - Fully used for damage ===
    print("\n5️⃣  Borg Usage (Damage)")
    set_named_value(wb, 'Borg_gebruikt', 500)  # Full deposit used
    set_named_value(wb, 'Borg_terug', 0)  # No return
    set_named_value(wb, 'Restschade', 0)  # No excess damage
    print("   ✓ Deposit used: €500 (full)")
    print("   ✓ Return: €0")

    # === GWE (UTILITIES) - Heavy usage, overflow ===
    print("\n6️⃣  GWE Usage (Utilities)")

    # Meter readings
    set_named_value(wb, 'KWh_begin', 10000)
    set_named_value(wb, 'KWh_eind', 10850)  # 850 kWh usage
    set_named_value(wb, 'KWh_verbruik', 850)

    set_named_value(wb, 'Gas_begin', 5000)
    set_named_value(wb, 'Gas_eind', 5120)  # 120 m³ usage
    set_named_value(wb, 'Gas_verbruik', 120)

    # GWE calculations (realistic Dutch utility rates for 2025)
    # Electricity: 850 kWh × €0.40 = €340
    # Gas: 120 m³ × €1.20 = €144
    # Total excl: €484
    # BTW (21%): €101.64
    # Total incl: €585.64
    # Overflow: €585.64 - €300 = €285.64

    gwe_totaal_excl = 484.00
    gwe_btw = 101.64
    gwe_totaal_incl = 585.64
    gwe_meer_minder = 300 - gwe_totaal_incl  # Negative = customer owes

    set_named_value(wb, 'GWE_totaal_excl', gwe_totaal_excl)
    set_named_value(wb, 'GWE_BTW', gwe_btw)
    set_named_value(wb, 'GWE_totaal_incl', gwe_totaal_incl)
    set_named_value(wb, 'GWE_meer_minder', gwe_meer_minder)

    set_named_value(wb, 'Energie_leverancier', "Vattenfall")
    set_named_value(wb, 'Meterbeheerder', "Enexis")

    print("   ✓ Electricity: 850 kWh (10000 → 10850)")
    print("   ✓ Gas: 120 m³ (5000 → 5120)")
    print(f"   ✓ Total: €{gwe_totaal_incl:.2f}")
    print(f"   ✓ Overflow: €{abs(gwe_meer_minder):.2f}")

    # === SCHOONMAAK (CLEANING) - Extra hours ===
    print("\n7️⃣  Schoonmaak (Cleaning)")

    # 5-hour package, but 7.5 hours used
    set_named_value(wb, 'Schoonmaak_pakket_type', "5_uur")
    set_named_value(wb, 'Inbegrepen_uren', 5.0)
    set_named_value(wb, 'Extra_uren', 2.5)  # 2.5 extra hours
    set_named_value(wb, 'Totaal_uren_gew', 7.5)  # Total hours worked
    set_named_value(wb, 'Uurtarief_schoonmaak', 50.0)  # €50 per hour
    set_named_value(wb, 'Extra_schoonmaak_bedrag', 125.0)  # 2.5 × €50

    print("   ✓ Package: 5 uur (€250)")
    print("   ✓ Total hours: 7.5")
    print("   ✓ Extra hours: 2.5 × €50 = €125")

    # === NET SETTLEMENT ===
    print("\n8️⃣  Net Settlement")
    # Borg: €0 (neutral)
    # GWE: -€285.64 (customer owes)
    # Schoonmaak: -€125 (customer owes)
    # Total: -€410.64
    totaal_eindafrekening = 0 + gwe_meer_minder - 125.0
    set_named_value(wb, 'Totaal_eindafrekening', totaal_eindafrekening)
    print(f"   ✓ Customer owes: €{abs(totaal_eindafrekening):.2f}")

    # === METADATA ===
    print("\n9️⃣  Metadata")
    set_named_value(wb, 'RR_Factuurnummer', "RR-2025-0042")
    set_named_value(wb, 'RR_Klantnummer', "KL-2025-088")
    set_named_value(wb, 'RR_Inspecteur', "Anna")
    set_named_value(wb, 'RR_Projectleider', "Mark")
    print("   ✓ Metadata set")

    # Save
    wb.save(dst)
    wb.close()

    print("\n" + "=" * 70)
    print(f"✅ Complete test scenario saved: {dst}")
    print("=" * 70)
    print("\n📊 Summary:")
    print("   • Borg: €500 → €500 used → €0 return")
    print("   • GWE: €300 → €585.64 used → Customer owes €285.64")
    print("   • Schoonmaak: €250 → 7.5 hours → Customer owes €125")
    print(f"   • TOTAL: Customer owes €{abs(totaal_eindafrekening):.2f}")
    print("\n💡 To test:")
    print(f"   1. cp {dst} input_template.xlsx")
    print("   2. python3 generate.py")
    print("   3. View output HTML")


if __name__ == "__main__":
    create_complete_overflow_scenario()
