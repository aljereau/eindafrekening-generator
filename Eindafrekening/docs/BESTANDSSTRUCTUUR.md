# 📂 RyanRent Eindafrekening Generator - Bestandsstructuur

**Versie:** 2.0 (Production Clean)
**Laatst bijgewerkt:** November 2024

---

## 🎯 Voor Eindgebruikers

Deze bestanden zijn **alles wat je nodig hebt** om eindafrekeningen te genereren:

### ✅ Essentiële Bestanden

```
Eindafrekening Generator/
│
├── 📄 input_template.xlsx              # Excel invoer template (VUL DIT IN!)
│
├── 🚀 Genereer_Eindafrekening.command  # Mac launcher (DUBBELKLIK)
├── 🚀 Genereer_Eindafrekening.bat      # Windows launcher (DUBBELKLIK)
│
├── 📘 SNELSTART_GIDS.md                # Stap-voor-stap gebruikershandleiding
├── 📘 GEBRUIKERSHANDLEIDING.md         # Uitgebreide handleiding
├── 📘 README.md                        # Project overzicht
│
├── 📦 output/                          # Gegenereerde eindafrekeningen
│   ├── onepager HTML & PDF
│   └── detail HTML & PDF
│
├── 🎨 assets/                          # Logo bestanden
│   └── ryanrent_co.jpg
│
└── 🔧 venv/                            # Python virtual environment (NIET VERWIJDEREN)
```

### ⚙️ Core Systeem Bestanden (Niet Aanraken)

```
├── 🐍 generate.py                      # Hoofdscript
├── 🐍 calculator.py                    # Bedrijfslogica berekeningen
├── 🐍 entities.py                      # Data modellen
├── 🐍 excel_reader.py                  # Excel inlezer
├── 🐍 viewmodels.py                    # View transformatie
├── 🐍 svg_bars.py                      # Bar chart generator
├── 🐍 template_renderer.py             # HTML rendering
├── 🐍 pdf_generator.py                 # PDF conversie
│
├── 🌐 template_onepager.html           # OnePager template
├── 🌐 template_detail.html             # Detail template
│
└── 📋 requirements.txt                 # Python dependencies
```

---

## 🗄️ Archive Folder

Ontwikkelingsbestanden en test scripts (alleen voor developers):

```
Archive/
├── dev-utilities/                      # Build & utility scripts
│   ├── build_excel_template.py         # Excel template generator
│   └── update_template_builder.py      # Template updater
│
├── test-scripts/                       # Test & debug scripts
│   ├── create_test_full_overuse.py     # Test data generator
│   └── debug_data.py                   # Debug utility
│
├── documentation/                      # Technical documentation
├── samples/                            # Example outputs
├── testing/                            # Test files
└── [old templates & test outputs]      # Historical files
```

---

## ⚡ Snelle Referentie

### Wat moet ik gebruiken?
- **`input_template.xlsx`** → Vul dit in met klantgegevens
- **`Genereer_Eindafrekening.command`** (Mac) → Dubbelklik om te genereren
- **`Genereer_Eindafrekening.bat`** (Windows) → Dubbelklik om te genereren
- **`SNELSTART_GIDS.md`** → Lees dit voor instructies

### Wat mag ik NIET aanraken?
- ❌ `venv/` folder → Virtual environment (systeem afhankelijk)
- ❌ Alle `.py` bestanden → Core systeem code
- ❌ Template HTML bestanden → Gegenereerde output hangt hiervan af
- ❌ `Archive/` folder → Alleen voor developers

### Waar komen mijn eindafrekeningen?
- ✅ `output/` folder → Alle gegenereerde HTML en PDF bestanden

---

## 🧹 Schoonmaak Status

**Gearchiveerd:**
- ✓ Test scripts → `Archive/test-scripts/`
- ✓ Utility scripts → `Archive/dev-utilities/`
- ✓ Oude templates → `Archive/old-templates/`
- ✓ Test outputs → `Archive/test-outputs/`
- ✓ Sample data → `Archive/samples/`

**Root folder bevat nu ALLEEN:**
- ✓ Productie-klare code
- ✓ Gebruikersdocumentatie
- ✓ Launcher scripts
- ✓ Excel template

---

## 📊 Bestandstelling

| Type | Aantal | Locatie |
|------|--------|---------|
| Python modules | 8 | Root |
| HTML templates | 2 | Root |
| Launcher scripts | 2 | Root |
| Documentatie | 3 | Root |
| Excel template | 1 | Root |
| Gearchiveerde files | ~50+ | Archive/ |

**Totaal root bestanden:** ~20 (schoon en overzichtelijk!)

---

## 🔍 Troubleshooting

### "Ik zie teveel bestanden!"
→ Je kijkt waarschijnlijk in de `Archive/` folder. Blijf in de root folder.

### "Waar is [oud bestand]?"
→ Check `Archive/` folder. Alle oude/test bestanden zijn daar naartoe verplaatst.

### "Mag ik Archive/ verwijderen?"
→ Ja, als je zeker weet dat je geen oude test data of build scripts nodig hebt. Maar het is veiliger om te bewaren.

---

**Status:** ✅ Production Clean
**Onderhouden door:** Aljereau Marten
