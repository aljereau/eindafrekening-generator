# RyanRent Eindafrekening Generator

Professionele eindafrekeningstool voor vakantieverhuur met visuele pot-gebaseerde overzichten.

## 🚀 Snel Starten

### 1. Installatie

```bash
# Activeer virtual environment
source venv/bin/activate  # macOS/Linux
# of
venv\Scripts\activate  # Windows

# Installeer dependencies (indien nodig)
pip install -r requirements.txt
```

### 2. Excel Template Genereren

```bash
python3 build_excel_template.py
```

Dit creëert `input_template.xlsx` met:
- Vooringevulde formules
- Data validatie
- Beschermde cellen
- 4 sheets: Algemeen, GWE_Detail, Schoonmaak, Schade

### 3. Eindafrekening Genereren

```bash
python3 generate.py
```

Dit genereert twee HTML bestanden in `output/`:
- **OnePager**: Visueel overzicht met pot-gebaseerde bars
- **Detail**: Volledige specificatie met alle regels

## 📊 Wat Krijg Je?

### Pot-Gebaseerde Visualisatie
- **Voorschot = Vaste 400px pot** (altijd zelfde breedte)
- **Underuse**: Proportionele weergave + groen gestreept retour
- **Overflow**: Volle pot + vaste 100px rode indicator (25%)

### Duidelijke Captions
- Underuse: `Voorschot: €350 · Verbruik: €180 · Terug: €170`
- Perfect: `Uw voorschot dekte uw volledige verbruik.`
- Overflow: `Voorschot: €250 · Verbruik: €450 · Extra te betalen: €200`

### Drie Categorieën
1. **BORG** - Borgstelling en schade
2. **GWE** - Gas/Water/Elektra verbruik
3. **SCHOONMAAK** - Schoonmaakkosten en extra uren

## 📁 Bestandsstructuur

```
Eindafrekening Generator/
├── generate.py              # Hoofdscript
├── input_template.xlsx      # Excel invoer template
├── output/                  # Gegenereerde eindafrekeningen
├── assets/                  # Logo bestanden
├── venv/                    # Virtual environment
└── Archive/                 # Ontwikkelingsbestanden
    ├── documentation/       # Technische documentatie
    ├── testing/            # Test scripts
    ├── samples/            # Voorbeeld bestanden
    └── test-outputs/       # Test outputs
```

## 🔧 Core Modules

- `excel_reader.py` - Leest Excel met named ranges
- `calculator.py` - Berekent borg, GWE, schoonmaak, schade
- `viewmodels.py` - Transformeert data naar templates
- `svg_bars.py` - Genereert pot-gebaseerde bar visualisaties
- `template_renderer.py` - Rendert Jinja2 templates
- `pdf_generator.py` - Converteert HTML naar PDF (optioneel)

## 📖 Documentatie

Zie `GEBRUIKERSHANDLEIDING.md` voor volledige handleiding.

Technische documentatie in `Archive/documentation/`:
- PROJECT.md - Volledig project overzicht
- Bar Design.md - UX/design principes
- FORMULA_IMPLEMENTATION.md - Excel formule implementatie

## ✅ Productie-Ready

Alle essentiële bestanden aanwezig:
- ✓ 9 Core Python scripts
- ✓ 2 HTML templates
- ✓ Excel template met formules
- ✓ Dependencies geïnstalleerd
- ✓ Handleiding voor gebruikers

## 🎨 Design Principes

- **Pot-metaphor**: Voorschot = vaste baseline
- **Consistent sizing**: Alle bars 400px breed (pot)
- **Smart overflow**: Vaste 25% indicator (niet proportioneel)
- **Positive framing**: Groen voor retour, neutraal voor bijbetaling
- **Concise captions**: Bullet-style met middot (·) separator

---

**Versie**: 2.0  
**Status**: Production Ready  
**Laatste update**: November 2025
