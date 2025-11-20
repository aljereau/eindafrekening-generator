# 📋 INPUT TEMPLATE USER GUIDE

## ✅ Template Status: READY FOR USE

The `input_template.xlsx` file is now properly configured with:
- ✓ All sheets unlocked and editable
- ✓ All necessary formulas in place
- ✓ Proper default values
- ✓ Validation ready for user input

---

## 📊 SHEETS OVERVIEW

### 1. **Algemeen** (General Information)
Main sheet containing all client, property, and financial data.

### 2. **GWE_Detail** (Utility Details)
Gas, water, electricity meter readings and cost breakdowns.

### 3. **Schoonmaak** (Cleaning)
Cleaning package details and extra hours.

### 4. **Schade** (Damage)
Damage items and costs (optional - only if damage occurred).

---

## 📝 WHAT TO FILL IN

### REQUIRED FIELDS (Must Fill):

#### Client Information
- **Klantnaam**: Customer name (e.g., "Familie Jansen")
- **Email**: Customer email address
- **Telefoonnummer**: Customer phone number
- **Object_adres**: Property full address
- **Incheck_datum**: Check-in date
- **Uitcheck_datum**: Check-out date
- **Aantal_dagen**: Number of days

#### Financial Data
- **Borg_gebruikt**: Amount of deposit used (€0 if no damage)
- **KWh_begin**: Electricity meter start reading
- **KWh_eind**: Electricity meter end reading
- **Gas_begin**: Gas meter start reading
- **Gas_eind**: Gas meter end reading
- **GWE_totaal_excl**: Total utility cost excluding VAT (from supplier invoice)
- **Totaal_uren_gew**: Total cleaning hours worked

### OPTIONAL FIELDS:

- **Object_ID**, **Unit_nr**, **Plaats**, **Postcode**: Property details
- **Energie_leverancier**: Energy supplier name (e.g., "Vattenfall")
- **Meterbeheerder**: Meter manager (e.g., "Enexis")
- **RR_Factuurnummer**: Invoice number
- **RR_Klantnummer**: Customer number

### PRE-FILLED DEFAULTS (Can Modify):

- **Voorschot_borg**: Deposit prepaid (default: €500)
- **Voorschot_GWE**: Utility prepaid (default: €300)
- **Voorschot_schoonmaak**: Cleaning prepaid (default: €250)
- **Schoonmaak_pakket_type**: Package type (default: "5_uur")
- **Inbegrepen_uren**: Included hours (default: 5)
- **Uurtarief_schoonmaak**: Hourly rate (default: €50)
- **Contactpersoon**: RyanRent contact (default: "Anna van RyanRent")
- **RR_Inspecteur**: Inspector name (default: "Anna")

---

## ⚙️ AUTO-CALCULATED FIELDS (Do NOT Edit)

These fields have formulas and will calculate automatically:

### Meter Readings
- **KWh_verbruik**: = KWh_eind - KWh_begin
- **Gas_verbruik**: = Gas_eind - Gas_begin

### Deposit Calculations
- **Borg_terug**: = Voorschot_borg - Borg_gebruikt (if positive)
- **Restschade**: = Borg_gebruikt - Voorschot_borg (if negative)

### GWE (Utilities) Calculations
- **GWE_BTW**: = GWE_totaal_excl × 21%
- **GWE_totaal_incl**: = GWE_totaal_excl + GWE_BTW
- **GWE_meer_minder**: = Voorschot_GWE - GWE_totaal_incl

### Cleaning Calculations
- **Extra_uren**: = Totaal_uren_gew - Inbegrepen_uren (if > 0)
- **Extra_schoonmaak_bedrag**: = Extra_uren × Uurtarief_schoonmaak

### Net Settlement
- **Totaal_eindafrekening**: = Borg_terug - Restschade + GWE_meer_minder - Extra_schoonmaak_bedrag

---

## 🎯 TYPICAL USER WORKFLOW

### Step 1: Client & Property Info
1. Open `input_template.xlsx`
2. Go to **Algemeen** sheet
3. Fill in client name, email, phone
4. Fill in property address
5. Fill in check-in and check-out dates

### Step 2: Deposit (Borg)
1. Enter amount of deposit used in `Borg_gebruikt`
   - €0 if no damage
   - €X if damage occurred
2. Formula will auto-calculate `Borg_terug` and `Restschade`

### Step 3: Utilities (GWE)
1. Go to **GWE_Detail** sheet
2. Enter meter readings:
   - `KWh_begin` and `KWh_eind`
   - `Gas_begin` and `Gas_eind`
3. Formulas will auto-calculate verbruik (consumption)
4. Enter `GWE_totaal_excl` (from supplier invoice)
5. Formulas will auto-calculate BTW and totals

### Step 4: Cleaning (Schoonmaak)
1. Go to **Schoonmaak** sheet
2. Enter `Totaal_uren_gew` (total hours worked)
3. Formula will auto-calculate extra hours and cost

### Step 5: Damage (Optional)
1. Go to **Schade** sheet
2. If damage occurred, fill in damage items and costs
3. Formulas will auto-calculate totals

### Step 6: Generate Report
1. Save the Excel file
2. Run: `python3 generate.py`
3. View output HTML in `output/` folder

---

## ⚠️ IMPORTANT NOTES

### Formulas Need Excel
- Formulas will calculate when you open and save in Excel
- If using programmatically, Python will recalculate during generation
- Always verify totals make sense before generating

### GWE Manual Entry
- You can enter `GWE_totaal_excl` directly (from supplier invoice)
- OR fill in detail lines in GWE_Detail sheet rows 12-30
- Python will use whichever method has data

### Cleaning Package Logic
- Package is ALWAYS fully used (never refunded)
- Only extra hours beyond package are charged additionally
- Bar will always show yellow (100% used)
- Result is either €0 or negative (if extra hours)

### Deposit Logic
- Can be used for damage, cleaning overages, or other costs
- Excel `Borg_gebruikt` is source of truth
- If used > prepaid, customer owes the difference (Restschade)

---

## 🧪 TEST SCENARIOS AVAILABLE

Use these pre-filled test files to verify the system:

1. **test_scenario_1_underuse.xlsx** - Customer gets money back
2. **test_scenario_2_perfect.xlsx** - Neutral (€0)
3. **test_scenario_3_overflow.xlsx** - Customer owes money
4. **test_complete_overflow.xlsx** - Full overflow with all fields

To test:
```bash
cp test_complete_overflow.xlsx input_template.xlsx
python3 generate.py
```

---

## ❓ TROUBLESHOOTING

### "Named range not found" warnings
- These are harmless if it's for optional fields
- Common: `Schoonmaak_pakket` (legacy field, can be ignored)

### Calculations show €0
- Make sure you saved the file in Excel first (to calculate formulas)
- OR Python will recalculate during generation

### Generated report shows wrong values
- Check that all required fields are filled
- Verify meter readings are correct (end > begin)
- Check formulas calculated (save in Excel first)

---

## 📞 SUPPORT

For issues with the template:
1. Check this guide first
2. Verify all required fields are filled
3. Test with one of the provided test scenarios
4. Contact RyanRent technical team

---

**Last Updated**: November 20, 2025
**Template Version**: 2.0
**Status**: ✅ Production Ready
