# Excel-Database Integration - Quick Guide

## Overview
The `input_template.xlsx` now has a dropdown menu to select properties from the database, eliminating manual typing and reducing errors.

## How It Works

### 1. Update Excel with Latest Properties
Whenever properties are added/changed in the database, run:
```bash
python3 Eindafrekening/scripts/update_excel_template.py
```

This script:
- Reads all active properties from `ryanrent_core.db`
- Updates the hidden "PropertyList" sheet in Excel
- Adds a dropdown to cell B10 (Adres Object)

### 2. Use the Template
1. Open `Eindafrekening/input_template.xlsx`
2. Go to cell B10 (Adres Object)
3. Click the dropdown arrow
4. Select a property from the list (381 properties available)
5. Fill in other fields (dates, amounts, etc.)
6. Generate report as usual

### 3. Optional: Auto-Fill City/Postcode
To make City and Postcode auto-fill when you select a property, add these formulas:

**City (B13):**
```
=IF(B10="","",VLOOKUP(B10,PropertyList!$B$2:$E$999,2,FALSE))
```

**Postcode (B12):**
```
=IF(B10="","",VLOOKUP(B10,PropertyList!$B$2:$E$999,3,FALSE))
```

## Workflow Example

```
1. New house added in Huizeninventaris app
   ↓
2. Run: python3 Eindafrekening/scripts/update_excel_template.py
   ↓
3. Open input_template.xlsx
   ↓
4. Select property from dropdown (new house now appears!)
   ↓
5. Fill in dates, amounts
   ↓
6. Generate eindafrekening
```

## Benefits
- ✅ No manual typing of addresses
- ✅ Reduced errors
- ✅ Always uses current database data
- ✅ Familiar Excel interface
- ✅ Works with OneDrive (shared access)

## Files
- **Script**: `Eindafrekening/scripts/update_excel_template.py`
- **Template**: `Eindafrekening/input_template.xlsx`
- **Database**: `Shared/database/ryanrent_core.db`
