# RyanRent - Multi-App Suite

A monorepo containing multiple applications for managing RyanRent's rental properties, all sharing a central database.

## Repository Structure

```
RyanRent/
├── Eindafrekening/          # Settlement Report Generator (✅ Complete)
├── Manager/                 # Database Management Tool (✅ MVP)
├── Huizeninventaris/        # Property Inventory (🚧 Planned)
├── Contracten/              # Contract Management (🚧 Planned)
├── Incheck/                 # Check-in/Check-out (🚧 Planned)
├── Shared/                  # Core Database & Entities
│   ├── database.py          # Database management
│   ├── entities.py          # Data models
│   ├── migrations/          # Schema migrations
│   └── scripts/             # Utility scripts
└── Archive/                 # Old/deprecated files
```

## Quick Start

### Run the Settlement Generator
```bash
python3 Eindafrekening/src/generate.py --no-pause --auto-open
```

### View the Database
```bash
python3 Manager/manage.py
```

### Import Legacy Data
```bash
python3 Shared/scripts/import_legacy_data.py
```

## Database

All apps share a single SQLite database: `Shared/database/ryanrent_core.db`

**Tables:**
- `properties` - Rental properties (381 imported)
- `clients` - Customers (81 imported)
- `contracts` - Rental agreements
- `bookings` - Individual stays
- `eindafrekeningen` - Settlement reports

## Development

**Requirements:**
```bash
pip install -r requirements.txt
```

**Build Standalone App:**
```bash
cd Eindafrekening
python3 scripts/build_app.py
```

## Files

- `requirements.txt` - Python dependencies
- `Ryanrent Sales...xlsm` - Legacy Excel data source
- `.gitignore` - Git ignore rules

## Notes

- Each app folder is self-contained with its own `src/`, `templates/`, `assets/`
- The `Shared/` folder contains code used by multiple apps
- Old files have been moved to `Archive/`
