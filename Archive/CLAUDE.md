# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RyanRent is a monorepo containing multiple Python applications for managing rental properties, settlement reports, and contracts. All apps share a centralized SQLite database.

## Repository Architecture

### Core Applications

**Eindafrekening/** - Settlement Report Generator (Production-ready)
- Generates visual PDF settlement reports from Excel templates
- Modular architecture with separate concerns for reading, calculating, rendering, and generating
- Outputs: OnePager summary + detailed breakdown PDFs

**Shared/** - Core Database & Business Logic
- `database.py`: SQLite operations, schema migrations, versioning
- `entities.py`: Domain models (Client, RentalProperty, Period, Deposit, GWE, Cleaning, Damage, Settlement)
- `migrations/`: SQL schema evolution (001-004 applied)

**database/** - SQLite Database Storage
- `ryanrent_core.db`: Active shared database (used by all applications)
- `*.backup`: Database backups for rollback

**Incheck/** - Check-in Management (Planned, not implemented)

**Removed Applications** (cleanup completed 2025-11-26):
- `Contracten/`: Flask-based contract management (incomplete)
- `Dashboard/`: Tkinter GUI launcher (needs rebuild)
- `Launcher/`: VBA-based Excel launcher (superseded)
- `Huizen/`: Property management scripts (removed)

### Key Design Patterns

1. **Shared Database Layer**: All apps reference `database/ryanrent_core.db`
2. **Migration-Based Schema**: Sequential numbered SQL files in `Shared/migrations/`
3. **Dataclass Domain Models**: All entities defined in `Shared/entities.py` using Python dataclasses
4. **Modular Pipeline**: Settlement generation follows Read → Calculate → Transform → Render → Generate flow
5. **Dutch Business Domain**: Entity models and Excel templates use Dutch naming to match business terminology

## Development Commands

### Settlement Generator

```bash
# Generate settlement report (interactive)
python3 Eindafrekening/src/generate.py

# Non-interactive with auto-open
python3 Eindafrekening/src/generate.py --no-pause --auto-open

# Custom input file
python3 Eindafrekening/src/generate.py --input path/to/file.xlsx

# Save intermediate JSON viewmodels for debugging
python3 Eindafrekening/src/generate.py --save-json

# HTML-only output (skip PDF generation)
python3 Eindafrekening/src/generate.py --html-only
```

### Build Standalone Application

```bash
cd Eindafrekening
python3 scripts/build_app.py
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `openpyxl==3.1.2` - Excel reading
- `jinja2==3.1.2` - HTML templating
- `weasyprint==60.1` - PDF generation

## Eindafrekening Architecture

### Module Responsibilities

**excel_reader.py**
- Uses `openpyxl` to read Excel files via named ranges
- Extracts client, object, period, GWE, cleaning, and damage data
- Returns structured data dictionary

**calculator.py**
- Business logic calculations (VAT, totals, deposit refunds)
- Validates Excel formulas against Python logic
- Recalculates all values to ensure consistency
- `Calculator` class with methods for each calculation domain

**viewmodels.py**
- Transforms raw data into presentation models
- Builds `OnePagerViewModel` (summary) and `DetailViewModel` (breakdown)
- Handles data serialization for templates

**template_renderer.py**
- Uses Jinja2 to render HTML templates
- Injects SVG visualizations for utility usage
- Two templates: `template_onepager.html` and `template_detail.html`

**svg_bars.py**
- Generates SVG bar charts for utility consumption visualization
- Creates visual representations of electricity and gas usage

**pdf_generator.py**
- Uses WeasyPrint to convert HTML to PDF
- Falls back to HTML output if PDF generation fails
- Handles base64-encoded logo embedding

**generate.py**
- Main orchestrator script
- Coordinates the complete pipeline
- Saves results to database with versioning
- Supports both frozen executable and source modes

### Data Flow

```
Excel Input
  ↓ excel_reader.py
Raw Data Dictionary
  ↓ calculator.py
Validated & Recalculated Data
  ↓ viewmodels.py
OnePagerViewModel + DetailViewModel
  ↓ template_renderer.py
OnePager HTML + Detail HTML
  ↓ pdf_generator.py
OnePager PDF + Detail PDF
  ↓ database.py
Saved to Database (versioned)
```

## Database Schema

### Core Tables

**properties** - Rental properties (381+ imported)
- `address`, `city`, `postal_code`, `property_type`
- `bedrooms`, `max_occupancy`, `sqm`
- Pricing fields: `default_rent_excl`, `cleaning_*`, `deposit_*`

**clients** - Customers (81+ imported)
- `name`, `email`, `phone`, `type` (business/individual)

**contracts** - Rental agreements
- Links `property_id` and `client_id`
- `start_date`, `end_date`, `rent_price_excl`

**bookings** - Individual stays
- `contract_id`, `checkin_date`, `checkout_date`

**eindafrekeningen** - Settlement reports (versioned)
- `client_name`, `checkin_date`, `checkout_date`, `version`
- Financial summary fields: `borg_terug`, `gwe_totaal_incl`, `totaal_eindafrekening`
- `data_json`: Complete settlement data as JSON
- `file_path`: Path to generated PDF

### Naming Conventions

**Database Schema**: English naming for SQL interoperability
- Table names: Lowercase English or Dutch domain terms (`properties`, `clients`, `eindafrekeningen`)
- Column names: English snake_case (`client_name`, `checkin_date`, `base_rent_price`)
- Note: Some tables mix conventions (e.g., `eindafrekeningen` has both English and Dutch columns)

**Python Domain Models**: Dutch naming matching business terminology
- Dataclass fields use Dutch terms (`voorschot`, `terug`, `omschrijving`)
- Defined in `Shared/entities.py`
- Reflects actual business language used by RyanRent

**Excel Templates**: Dutch naming for user interface
- Named ranges use Dutch (`Klantnaam`, `Incheck_datum`, `Object_adres`)
- Column headers in Dutch matching business terminology
- Translation happens at the application layer

**Future Standardization**: Consider full Dutch schema for consistency with business domain and Excel workflows

### Versioning System

Settlement reports support versioning:
- First generation: Version 1 (no reason required)
- Revisions: Version 2+ (reason required)
- View `latest_eindafrekeningen` shows most recent version per client/period

## Important Conventions

### Path Handling

Applications must work in both modes:
- **Source mode**: Running from `Eindafrekening/src/generate.py`
- **Frozen mode**: Running as compiled executable

Path resolution pattern:
```python
if getattr(sys, 'frozen', False):
    project_root = os.path.dirname(sys.executable)
    bundle_dir = sys._MEIPASS  # Bundled assets
else:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bundle_dir = project_root
```

### Shared Module Import

All apps must add Shared directory to Python path:
```python
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
shared_dir = os.path.join(root_dir, 'Shared')
sys.path.append(shared_dir)
```

### Database Migrations

When modifying schema:
1. Create new numbered SQL file in `Shared/migrations/` (e.g., `005_description.sql`)
2. Migrations run automatically on Database initialization
3. Applied migrations tracked in `schema_migrations` table
4. Current applied migrations: 001-004

**Migration History**:
- `001_initial_schema.sql`: Eindafrekeningen table and versioning
- `002_core_schema.sql`: Properties, clients, contracts, bookings tables
- `003_property_details.sql`: Extended property fields (object_id, bedrooms, etc.)
- `004_pricing_columns.sql`: Property pricing fields (base_rent_price, gwe_advance, etc.)
- Migrations 005-009 removed during 2025-11-26 cleanup

### Entity Models

When adding new domain models:
1. Define dataclass in `Shared/entities.py`
2. Follow existing naming conventions (Dutch business terms)
3. Use `Optional[type]` for nullable fields
4. Document field meanings with comments

## Testing Approach

### Manual Testing

Settlement generator includes validation:
- Compares Excel formulas vs. Python calculations
- Warns on discrepancies
- Recalculates all values for consistency

### Data Verification

```bash
# Verify database directly with sqlite3
sqlite3 database/ryanrent_core.db "SELECT COUNT(*) FROM properties;"
sqlite3 database/ryanrent_core.db "SELECT COUNT(*) FROM clients;"
sqlite3 database/ryanrent_core.db "SELECT COUNT(*) FROM eindafrekeningen;"

# View all tables
sqlite3 database/ryanrent_core.db ".tables"

# View applied migrations
sqlite3 database/ryanrent_core.db "SELECT * FROM schema_migrations;"
```

## File Organization

```
.
├── Eindafrekening/          # Settlement generator (production-ready)
│   ├── src/                 # Python modules
│   ├── templates/           # Jinja2 HTML templates
│   ├── assets/              # Logo, styles
│   ├── scripts/             # Build and analysis tools
│   └── input_template.xlsx  # User fills this
├── Shared/                  # Core Python layer
│   ├── database.py          # Database operations
│   ├── entities.py          # Domain models
│   └── migrations/          # Schema evolution (001-004)
├── database/                # Database storage (SQLite files)
│   ├── ryanrent_core.db     # Active database
│   └── *.backup             # Database backups
├── Incheck/                 # Check-in management (planned, empty)
├── Archive/                 # Deprecated files and old Excel data
└── requirements.txt         # Python dependencies
```

## Known Limitations

- WeasyPrint PDF generation may fail on some systems (falls back to HTML)
- Excel input template must use exact named ranges as defined in `excel_reader.py`
- Database versioning requires manual reason entry for revisions
- Legacy Excel file (`Ryanrent Sales...xlsm`) contains master data but format is fragile

## Future Applications

Planned apps should follow established patterns:
1. Create app folder with descriptive name (e.g., `Contracten/`, `Incheck/`)
2. Import `Shared/database.py` and `Shared/entities.py`
3. Add database tables via new migration file starting at `005_description.sql`
4. Use shared database: `database/ryanrent_core.db` (resolved by Database class)
5. Consider Excel-based workflows for MVP (like Huizen/ and Eindafrekening/)
6. Use Dutch naming in Python entities and Excel templates to match business terminology
7. Document any new naming conventions in this file

**Naming Convention Guidelines**:
- **Prefer Dutch** for new tables/columns to align with business domain
- **Excel templates** must use Dutch named ranges matching business terminology
- **Python entities** should use Dutch field names matching Excel and business language
- **Translation layer** only needed if mixing with existing English schema
