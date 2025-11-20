# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**RyanRent Eindafrekening Generator** - A Python-based tool that generates visual, single-page PDF settlement reports for vacation rental properties. The tool reads Excel input data and produces professional PDF invoices with visual bar charts showing deposit usage, utility consumption, and cleaning costs.

## Core Development Commands

### Running the Generator
```bash
# Basic usage with default input.xlsx
python3 generate.py

# Specify custom input file
python3 generate.py --input "path/to/custom.xlsx"

# Non-interactive mode (for scripts)
python3 generate.py --no-pause
```

### Environment Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Testing and Debugging
```bash
# Inspect Excel file structure
python3 debug_excel.py

# Create sample Excel file for testing
python3 create_sample_excel.py
```

## Architecture and Data Flow

### Processing Pipeline
```
Excel Input (input.xlsx)
    ↓
read_excel_data() → Extracts from "Hoofdgegevens" and "Schades Detail" sheets
    ↓
calculate_values() → Computes percentages, net amounts, bar proportions
    ↓
Jinja2 Template (template.html) → Renders HTML with embedded CSS
    ↓
WeasyPrint → Converts HTML to PDF
    ↓
Output: output/{filename}.pdf + output/{filename}.html (fallback)
```

### Key Data Transformations

**Bar Visualization Logic:**
- **Underfilled scenario** (deposit return): Used portion + Return portion = 100% of baseline
- **Overfilled scenario** (additional charges): Used portion = 100% + Extra portion extends beyond baseline
- Bar widths are calculated as percentages relative to the prepaid amount (`voorschot`)

**Net Settlement Calculation:**
```python
netto = borg_terug + (gwe_terug OR -gwe_extra) + (clean_terug OR -clean_extra_calc)
```

### Excel Input Structure

**Sheet 1: "Hoofdgegevens"** (Main data)
- Column A: Labels
- Column B: Values
- Required fields: Guest name, property info, period, amounts for deposit, utilities, cleaning

**Sheet 2: "Schades Detail"** (Optional damage breakdown)
- Column A: Damage descriptions
- Column B: Amounts
- Sum must match "Borg Gebruikt" from Sheet 1

## Critical Implementation Details

### WeasyPrint PDF Generation
The script gracefully handles WeasyPrint failures (common on macOS due to missing system libraries):
- Primary: PDF generation via WeasyPrint
- Fallback: HTML output saved to `output/` directory
- Import WeasyPrint inside functions (not at module level) to prevent import errors from blocking script execution

### Base64 Logo Encoding
The logo at `assets/ryanrent_co.jpg` is encoded as base64 and embedded directly in the HTML to avoid path issues in PDF generation. If logo is missing, script continues with fallback "RR" text logo.

### Visual Design Constraints
- Fixed bar width: 220px represents 100% budget baseline
- Overfilled bars extend beyond this baseline using calculated extra percentages
- Color system:
  - Green (`#A5D6A7`): Prepaid amounts and returns
  - Yellow/Orange (`#FFCC80`): Used portions
  - Red/Pink (`#EF9A9A` with stripes): Extra charges beyond budget

### Error Handling Strategy
The script includes defensive programming for common Excel data issues:
- Non-numeric values in number fields → defaults to 0.0 with warning
- Missing values → defaults to empty string or 0.0
- Division by zero → prevented with `if voorschot > 0` checks
- Missing sheets → graceful degradation (e.g., no damage detail)

## File Organization

```
.
├── generate.py              # Main generator script
├── debug_excel.py           # Excel inspection utility
├── create_sample_excel.py   # Sample data generator
├── template.html            # Jinja2 template with embedded CSS
├── requirements.txt         # Python dependencies
├── PROJECT.md              # Comprehensive project documentation
├── input.xlsx              # User-provided input data
├── output/                 # Generated PDFs and HTML files
├── assets/                 # Logo and static resources
│   └── ryanrent_co.jpg
└── Building folder/        # Client-specific working files
```

## Development Workflow

### When Modifying the Template
1. The `template.html` file contains both HTML structure and all CSS inline
2. Visual design follows a three-column layout: Start (25%) | Stay (55%) | Result (20%)
3. Test changes with `python3 generate.py` using sample data
4. Check both PDF output and HTML fallback

### When Modifying Calculations
1. Update logic in `calculate_values()` function in `generate.py`
2. Key calculations involve percentage conversions for bar proportions
3. Test edge cases: zero values, exact matches, extreme overages
4. Verify net settlement formula includes all components correctly

### When Extending Excel Input
1. Update cell references in `read_excel_data()` function
2. Add corresponding calculations in `calculate_values()`
3. Update Jinja2 template to display new data
4. Update Excel template structure documentation

## Known Limitations and Workarounds

**macOS WeasyPrint Issues:**
WeasyPrint requires system libraries (cairo, pango) that may not be installed. The script handles this by catching `OSError` and `ImportError`, falling back to HTML-only output. Users can open the HTML file and print to PDF manually if needed.

**Long File Paths:**
The project is located in a OneDrive shared library with a very long path. Use relative paths when possible and be mindful of path length limits on Windows systems.

**Excel Sheet Names:**
Sheet names are hardcoded as "Hoofdgegevens" and "Schades Detail" (Dutch). Any changes to these names require updates in the code.

## Context for Future Development

This is a **Phase 1** implementation focused on manual Excel input and local PDF generation. The `PROJECT.md` file outlines future enhancements including:
- Phase 2: Email parsing and OCR for automatic data extraction
- Phase 3: Web portal with client access
- Phase 4: Microsoft Power Automate integration

When implementing future phases, maintain backward compatibility with the current Excel input format.
