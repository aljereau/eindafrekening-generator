# RyanRent Eindafrekening Generator - Project Status

**Last Updated**: 2025-11-20  
**Phase**: Bar Visualization Refinement  
**Status**: Active Development - Bar Design Finalized

---

## Executive Summary

The RyanRent Eindafrekening Generator is a Python-based tool that generates visual, single-page PDF settlement reports for vacation rental properties. The system reads Excel input data and produces professional PDF invoices with visual bar charts showing deposit, utilities (GWE), and cleaning budget usage.

### Current Focus
We're refining the **bar visualization system** to create an intuitive, single-bar overlay design that clearly shows budget usage and returns.

---

## Recent Completion: Bar Design Overhaul

### What Was Just Fixed (2025-11-20)

**Problem**: The bar visualization showed two separate "pills" side-by-side (yellow used portion + green return portion), which looked disconnected and confusing.

**Solution**: Implemented a **single continuous bar with overlay design**:
- **Layer 1**: Full-width green bar (#81C784) representing the total pot/budget
- **Layer 2**: Yellow overlay (#FFE082) showing the used portion
- **Result**: Green naturally shows through unused area, creating unified visual

### Visual Design

**Underuse Scenario (e.g., €250 used of €500)**:
```
[═══════ YELLOW (€250) ═══════][═══════ GREEN (€250 return) ═══════]
                              ↑ single continuous bar
```

**Perfect Fit**:
```
[════════════════════ YELLOW (€500) ════════════════════]
```

**Overflow**:
```
[════════════════ YELLOW (€500) ════════════════][RED (+€75)]
                                                 ↑ extends beyond
```

### Technical Implementation

**File Modified**: `svg_bars.py` → `generate_bar_svg()`

**Key Changes**:
1. Green bar as base layer (full pot width)
2. Yellow overlays on top (proportional to usage)
3. Red extension for overflow scenarios (50px fixed)
4. Labels positioned intelligently based on segment width

---

## Project Architecture

### Core Components

```
├── Excel Input Layer
│   ├── input_template.xlsx          # 4-sheet template with named ranges
│   └── build_excel_template.py      # Generates template with formulas
│
├── Data Processing Layer
│   ├── excel_reader.py              # Reads Excel using named ranges
│   ├── entities.py                  # Data models (Client, Period, etc.)
│   └── calculator.py                # Business logic & calculations
│
├── Visualization Layer
│   ├── svg_bars.py                  # SVG bar chart generation ⭐ JUST UPDATED
│   ├── viewmodels.py                # Transforms data for templates
│   └── text_mapping.json            # Dutch text dictionary
│
├── Output Layer
│   ├── template_onepager.html       # One-page summary
│   ├── template_detail.html         # Detailed breakdown
│   ├── template_renderer.py         # Jinja2 rendering
│   └── pdf_generator.py             # HTML → PDF (WeasyPrint)
│
└── Main Script
    └── generate.py                  # Orchestrates entire flow
```

---

## Data Flow

```
Excel Input (input_template.xlsx)
    ↓
excel_reader.py reads named ranges
    ↓
entities.py structures data
    ↓
calculator.py performs calculations
    ↓
viewmodels.py generates SVG bars + view models
    ↓
template_renderer.py renders HTML
    ↓
pdf_generator.py creates PDF (or saves HTML)
    ↓
Output: eindafrekening_[date]_onepager.html/pdf
```

---

## Key Features Implemented

### ✅ Completed Features

1. **Excel Input System**
   - 4-sheet template (Algemeen, GWE_Detail, Schoonmaak, Schade)
   - Named ranges for robust data extraction
   - Data validation (dropdowns, number formats)
   - Excel formulas with Python validation layer

2. **Bar Visualization** ⭐ JUST COMPLETED
   - Single continuous bar design
   - Green base layer (pot/budget)
   - Yellow overlay (usage)
   - Red overflow extension
   - Smart label positioning

3. **Schoonmaak Package System**
   - Dropdown: "Basis Schoonmaak" (5 hours, €250) or "Intensief Schoonmaak" (7 hours, €350)
   - Auto-calculated voorschot based on selection
   - Extra hours calculated automatically

4. **GWE (Utilities) Tracking**
   - Power (kWh) and Gas (m³) meter readings
   - Cost calculation based on consumption
   - Reporting period separate from stay period

5. **Multi-Template Output**
   - One-pager: Simplified overview
   - Detail: Comprehensive breakdown
   - HTML-first with PDF fallback

6. **Text Externalization**
   - All Dutch copy in `text_mapping.json`
   - Easy updates without touching code

7. **Guide Row Filtering**
   - Excel template includes instructional rows
   - Python automatically filters them out

---

## Current File Status

### Recently Modified (2025-11-20)
- ✅ `svg_bars.py` - Bar overlay design implemented
- ✅ `viewmodels.py` - Generates bar SVGs with new function
- ✅ `template_onepager.html` - Updated header dates, compact spacing

### Active Files
- `generate.py` - Main orchestration script
- `excel_reader.py` - Reads Excel template
- `calculator.py` - Business logic
- `template_onepager.html` - Primary output template
- `template_detail.html` - Detailed view template

### Archive
- `Archive/` - Contains old documentation and test files
- Variations B, C, D templates (experimental designs)

---

## Excel Template Structure

### Sheet 1: Algemeen (General)
**Named Ranges**:
- Client info: `Naam`, `Email`, `Telefoon`
- Object: `Object_adres`
- Period: `Checkin_datum`, `Checkout_datum`, `Aantal_dagen`
- Deposits: `Borg_voorschot`, `Borg_gebruikt`, `Borg_terug`, `Restschade`
- GWE: `GWE_voorschot`, `GWE_meer_minder`
- Cleaning: `Schoonmaak_pakket`, `Voorschot_schoonmaak`, `Inbegrepen_uren`, `Extra_schoonmaak_bedrag`
- Settlement: `Totaal_eindafrekening`

### Sheet 2: GWE_Detail
**Named Ranges**:
- Readings: `Power_start`, `Power_eind`, `KWh_verbruik`, `Gas_start`, `Gas_eind`, `Gas_verbruik`
- Table: `GWE_Detail_Table` (dynamic costs breakdown)

### Sheet 3: Schoonmaak
**Named Ranges**:
- `Extra_uren`, `Totaal_uren`

### Sheet 4: Schade
**Named Ranges**:
- `Schade_Table` (damage items with costs)

---

## Bar Visualization Details

### Current Design (Implemented)

**Function**: `generate_bar_svg()` in `svg_bars.py`

**Layers**:
1. **Green base** (#81C784) - Full pot width, always visible
2. **Yellow overlay** (#FFE082) - Usage portion overlays on green
3. **Red extension** (#EF9A9A, striped) - Overflow beyond pot (50px fixed)

**Smart Features**:
- Minimum width enforcement (5px) for visibility
- Label positioning based on segment size (>40px for inline)
- Dashed red boundary marker at pot edge (overflow scenarios)
- Pattern fills for visual distinction

**Parameters**:
- `voorschot`: Pot/budget amount
- `gebruikt_or_totaal`: Amount used
- `is_overfilled`: Boolean for overflow state
- `label_gebruikt`: Label for used portion
- `label_extra_or_terug`: Label for return/overflow
- `pot_width`: Fixed width (typically 380px or 280px)
- `height`: Bar height (typically 30px)

---

## Known Issues & TODOs

### Minor Issues
1. ⚠️ WeasyPrint not installed - PDF generation falls back to HTML
2. ⚠️ Warning about `Schoonmaak_pakket` named range (can be ignored if Excel is v2)
3. ⚠️ Excel formula validation warnings (Python recalculates correctly)

### Pending Old TODOs (Low Priority)
These are leftover from earlier iterations and may not be relevant:
- Guide row filtering (✅ already completed)
- Schoonmaak pakket dropdown (✅ already completed)
- Text mapping updates (✅ already completed)

---

## Testing

### Current Test Data
The system uses `input_template.xlsx` with minimal/zero data:
- Client: Empty
- Period: 2025-11-20 → 2025-11-20 (0 days)
- All amounts: €0

### To Test With Real Data
1. Open `input_template.xlsx`
2. Fill in:
   - Client info (Sheet: Algemeen)
   - Dates (Sheet: Algemeen)
   - Deposit amounts (Sheet: Algemeen)
   - GWE readings & costs (Sheet: GWE_Detail)
   - Cleaning package selection (Sheet: Algemeen)
   - Any damage items (Sheet: Schade)
3. Run: `python3 generate.py`
4. Output: `output/eindafrekening_[dates]_onepager.html`

### Test Scenarios to Verify
- ✅ Underuse (50% used) - Green return portion visible
- ✅ Perfect fit (100% used) - No green visible
- ✅ Small overflow (10% over) - Small red extension
- ✅ Large overflow (50% over) - Larger red extension
- ⏳ Zero usage - All green bar
- ⏳ Tiny usage (<5%) - Minimum visibility enforcement

---

## Color Palette

| Element | Color | Hex | Usage |
|---------|-------|-----|-------|
| **Base bar** | Green | `#81C784` | Pot/return amount |
| **Usage** | Yellow | `#FFE082` | Amount used |
| **Overflow** | Red | `#EF9A9A` | Over budget |
| **Border** | Gray | `#E0E0E0` | Bar outline |
| **Boundary** | Dark Red | `#D32F2F` | Pot limit marker |
| **Text** | Dark | `#2C3E50` | Primary labels |
| **Overflow Text** | Red | `#C62828` | Overflow labels |

---

## Commands

### Generate Report
```bash
python3 generate.py
```

### Build Excel Template
```bash
python3 build_excel_template.py
```

### Test Bar Variations (Experimental)
```bash
python3 test_bar_variations.py
```
*(Note: This was for comparing design variations and is no longer actively used)*

---

## Next Steps / Roadmap

### Immediate Next (If Needed)
1. **Test with real data** - Verify bars work with actual client scenarios
2. **Install WeasyPrint** - Enable PDF generation (currently HTML-only)
3. **Refinements**:
   - Adjust bar widths if needed (currently 380px for VERBLIJF, 280px for START)
   - Tweak label thresholds (currently >40px for inline labels)
   - Fine-tune colors if needed

### Future Enhancements (Nice to Have)
1. **Print Optimization**
   - Ensure one-pager fits on single A4 page
   - Adjust spacing/sizing for print media

2. **Data Validation**
   - Add more robust Excel formula checking
   - Warn if calculations seem incorrect

3. **Template Improvements**
   - Add more visual icons
   - Improve footer design
   - Add QR code for payment?

4. **Localization**
   - Currently Dutch-only
   - Could add English/other languages via text_mapping.json

---

## Important Context for Claude

### User Preferences (Established)
1. **Single continuous bar** - Not two pills side-by-side ✅
2. **Green shows through unused** - Natural visual for "money back" ✅
3. **Overflow extends beyond** - Clear visual of exceeding budget ✅
4. **Clean, minimal design** - Modern, flat, not cluttered ✅
5. **Positive framing** - Focus on returns, not penalties ✅

### Technical Decisions Made
1. **HTML-first approach** - PDF as optional step
2. **SVG for bars** - Pixel-perfect, scalable, consistent
3. **Named ranges in Excel** - Robust data extraction
4. **Python as authority** - Excel formulas validated by Python
5. **Jinja2 templates** - Flexible, maintainable HTML generation

### Files to Focus On
- `svg_bars.py` - Bar generation logic ⭐
- `viewmodels.py` - Data transformation for templates
- `template_onepager.html` - Main output template
- `generate.py` - Orchestration

### Files to Avoid Editing (Unless Necessary)
- `entities.py` - Stable data models
- `excel_reader.py` - Working well
- `calculator.py` - Business logic is correct
- Archived files - Historical reference only

---

## Key Learnings / Design Evolution

### Iteration 1: Flexbox Bars
❌ **Problem**: Inconsistent sizing, alignment issues, broke with extreme values

### Iteration 2: Separate Pill Design
❌ **Problem**: Two pills looked disconnected, unclear relationship

### Iteration 3: Fixed-Width Bars + Overflow Zone (Variations B, C)
⚠️ **Problem**: Still felt like separate elements, grid became complex

### Iteration 4: Overlay Design (Current) ✅
✅ **Solution**: Single bar, green base, yellow overlay, natural visual flow

---

## Dependencies

```
Python 3.13
├── openpyxl       # Excel reading/writing
├── Jinja2         # Template rendering
└── WeasyPrint     # HTML → PDF (optional, not installed)
```

---

## Output Files

### Generated Each Run
- `output/eindafrekening_[dates]_onepager.html` - One-page summary
- `output/eindafrekening_[dates]_detail.html` - Detailed breakdown
- *(PDF versions if WeasyPrint installed)*

### Logs
- Console output shows:
  - Excel data read summary
  - Calculation warnings
  - Output file paths
  - Generation status

---

## Questions for Next Session

If continuing this project, consider:

1. **Are the bar widths optimal?**
   - Currently: START = 280px, VERBLIJF = 380px
   - Should they be equal? Different?

2. **Is the overflow extension size right?**
   - Currently: 50px fixed
   - Should it scale with overflow amount?

3. **Label positioning working well?**
   - Currently: Inline if segment >40px
   - Need floating labels for tiny segments?

4. **Colors satisfactory?**
   - Green: #81C784
   - Yellow: #FFE082
   - Red: #EF9A9A

5. **Ready to test with real client data?**
   - Need example scenarios to validate design

---

## Success Criteria

### Phase 1: Core Functionality ✅
- [x] Read Excel data
- [x] Calculate settlements
- [x] Generate HTML output
- [x] Visual bar charts

### Phase 2: Polish & Refinement ⏳ IN PROGRESS
- [x] Single continuous bar design
- [x] Smart label positioning
- [ ] Test with real data
- [ ] PDF generation working
- [ ] One-page print optimization

### Phase 3: Production Ready 📋 TODO
- [ ] Error handling robust
- [ ] User documentation complete
- [ ] Excel template user-friendly
- [ ] Output professional quality
- [ ] Performance acceptable (<5s generation)

---

## Contact & Handoff Notes

**For Claude (or future developer)**:

This project is in **active refinement** of the bar visualization system. The core functionality works, but we're perfecting the visual design for clarity and user experience.

**Start here**:
1. Read this file (PROJECT_STATUS.md)
2. Review `svg_bars.py` - Bar generation logic
3. Open `output/eindafrekening_[latest]_onepager.html` - See current output
4. Check `template_onepager.html` - Main template structure

**Key files** to understand the codebase:
- `CLAUDE.md` - High-level project overview
- `PROJECT.md` - Original design specification
- `README.md` - Installation & usage

**If user wants changes**:
- Bar design → Modify `svg_bars.py`
- Layout changes → Modify `template_onepager.html`
- Calculations → Modify `calculator.py`
- Data extraction → Modify `excel_reader.py`

**Current state**: Bar overlay design just implemented. System is stable and functional. Ready for real-world testing.

---

*End of Status Document*

