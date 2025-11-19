# RyanRent Eindafrekening Generator

## Project Overzicht

**Doel:** Een geautomatiseerde one-page visuele eindafrekening generator voor vakantiehuur verblijven.

**Probleem:** Klanten ontvangen nu 150-250 pagina PDF rapporten met foto's plus facturen, wat zorgt voor verwarring, discussies en een gevoel van oneerlijke behandeling. Ze begrijpen niet wat ze betalen of hoe bedragen tot stand zijn gekomen.

**Oplossing:** Een visueel dashboard-stijl one-pager die het verhaal vertelt: "Wat je betaalde → Wat er gebeurde → Wat je moet betalen/terugkrijgt" met intuïtieve bar visualisaties.

---

## Kern Concept

### De Verhaal Flow

**LINKS → MIDDEN → RECHTS = VOOR → TIJDENS → NA**

Elke categorie (Borg, GWE, Schoonmaak) vertelt een drie-stappen visueel verhaal:

1. **LINKS (START):** "Dit is wat je vooraf betaalde" - Volle groene bar = voorschot baseline
2. **MIDDEN (VERBLIJF):** "Dit is wat er gebeurde tijdens je verblijf" - Bar splitst of breidt uit om gebruik te tonen
3. **RECHTS (RESULTAAT):** "Dit is het netto effect" - Simpel +/- bedrag in groen (retour) of rood (betalen)

### Visuele Logica

**Scenario A: Klant krijgt geld terug (bijv. Borg)**
- Gele bar (gebruikt deel) + Groene bar (retour deel)
- Totale lengte = zelfde als de start bar
- Het groene deel = "dit krijg je terug"

**Scenario B: Klant moet bijbetalen (bijv. GWE, Schoonmaak)**
- Gele bar (volledig voorschot gebruikt) + Roze/Rode dashed bar (meerverbruik)
- De roze bar **breidt uit voorbij** de baseline
- Visueel toont "je ging over je budget"

### Waarom Dit Werkt

- **Visueel eerlijk:** Je ziet meteen of iets "binnen" of "buiten" het voorschot valt
- **Intuïtief:** Korter = terug, langer = betalen
- **Geen verrassingen:** Het verhaal is links → midden → rechts
- **Dashboard-achtig:** Net als je energierekening, niet zoals een factuur

---

## Sectie Structuur

### **SECTIE 1: START VERBLIJF (Links Boven)**
**"Wat je aan het begin hebt betaald"**

Drie groene bars verticaal gestapeld:
- **BORG:** €800
- **GWE:** €350  
- **CLEANING:** €250

Elk met korte beschrijving:
- "Borg Vooraf betaald en gereserveerd voor u"
- "Voorschot GWE"
- "Basis Schoonmaak pakket"

**Doel:** De baseline/referentie tonen - dit zijn de startbedragen waarmee we gaan vergelijken.

---

### **SECTIE 2: VERBLIJF (Rechts Boven)**
**"Wat er gebeurde tijdens je verblijf P1-P12"**

Drie horizontale bar visualisaties met resultaat rechts:

#### **BORG (underfilled - geld terug)**
```
[████████ 600 Eu.][██ 200 Eu.] ┊ +200 Eu.
   (geel)          (groen)      ┊ (groen)
```
- Gele bar = gebruikt (€600)
- Groene bar = terug (€200)
- Samen = lengte van start bar
- Rechts van dotted line: **+200 Eu.** in groen

#### **GWE (overfilled - bijbetalen)**
```
[████████████ 350 Eu.][░░ 100 Eu.] ┊ -100 Eu.
      (geel)           (roze dashed)┊ (rood)
```
- Gele bar = voorschot (€350) tot aan dotted line
- Roze dashed bar = extra (€100) **gaat door de dotted line**
- Rechts van dotted line: **-100 Eu.** in rood

#### **CLEANING (overfilled - bijbetalen)**
```
[████████ 250 Eu.][░░░ 150 Eu.] ┊ -150 Eu.
    (geel)         (roze dashed) ┊ (rood)
```
- Gele bar = basis pakket (€250) 
- Roze dashed bar = extra uren (€150) **gaat door de dotted line**
- Rechts van dotted line: **-150 Eu.** in rood

**Verticale Dotted Line:**
- Markeert "Extra Verbruik" zone
- Alles links = binnen budget
- Alles rechts (door de lijn) = over budget

**Netto Berekening (onderaan sectie 2):**
```
-50 Eu.
Netto Eind Afrek.
```
Berekening: +200 (borg) -100 (GWE) -150 (cleaning) = -50 totaal

---

### **SECTIE 3: UITLEG VAN WAARDES (Onder)**
**"Hier is WAAROM die bedragen zo zijn"**

Gedetailleerde breakdown van elke categorie:

#### **BORG - Uitgebreid**
```
[████████ 600 Eu.][██ 200 Eu.]
   (geel)          (groen)

Schades XXX --------- 30 Eu
Schades XXX --------- 30 Eu  
Schades XXX --------- 30 Eu
Schades XXX --------- 30 Eu
Schades XXX --------- 30 Eu
Schades XXX --------- 30 Eu
Schades XXX --------- 30 Eu
Schades XXX --------- 30 Eu
──────────────────────────
Totaal: 600 Eu. gebruikt
200 Eu. minder verbruikt dan voorschot
```

#### **GWE - Uitgebreid**
```
[████████████ 350 Eu.][░░ 100 Eu.]
      (geel)           (roze dashed)

Gas Verbruik P1-P12 -------- 275 Eu
Water Verbruik P1-P12 ------ 75 Eu
Electra Verbruik ----------- 100 Eu (10000 kWh)
──────────────────────────────────
Totaal verbruik: 450 Eu.
Voorschot: 350 Eu.
Extra: 100 Eu.
```

#### **CLEANING - Uitgebreid**
```
[████████ 250 Eu.][░░░ 150 Eu.]
    (geel)         (roze dashed)

Basis schoonmaak pakket: 250 Eu. (included)
Extra uren nodig: 150 Eu.
Reden: Grondige reiniging nodig na verblijf
──────────────────────────────────
Totaal: 400 Eu.
Voorschot: 250 Eu.
Extra: 150 Eu.
```

---

## Kleurensysteem

### **Primaire Kleuren (uit design system)**
```css
--color-primary: #E85D45        /* Coral - voor accenten, CTA's */
--color-secondary: #2C2C2C      /* Dark - voor text, logo */
--color-text-primary: #1A1A1A   
--color-text-secondary: #6B6B6B 
--color-text-tertiary: #A0A0A0  
--color-background: #F8F8F8     
--color-surface: #FFFFFF        
--color-border: #E8E8E8         
```

### **Semantische Kleuren (voor bars)**
```css
--color-prepaid: #90EE90        /* Licht groen - voorschot/gereserveerd */
--color-used: #FFE082           /* Licht geel - gebruikt/verbruikt */
--color-return: #81C784         /* Groen - retour bedrag */
--color-extra: #FFCDD2          /* Licht roze/rood - meerkosten */
--color-success: #4CAF50        /* Groen text - positief bedrag */
--color-error: #E85D45          /* Rood text - negatief bedrag */
```

### **Kleur Betekenis**
- **Groen:** Gereserveerd geld, voorschot, positief resultaat, geld terug
- **Geel:** Gebruikt/verbruikt deel, neutraal
- **Roze/Rood (dashed):** Extra kosten, overschrijding, meerverbruik
- **Groene text:** Positieve bedragen (+200 Eu.)
- **Rode text:** Negatieve bedragen (-100 Eu.)

---

## Design System Specificaties

### **Typography**
```css
--font-family-base: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
--font-size-xs: 0.75rem;      /* 12px */
--font-size-sm: 0.875rem;     /* 14px */
--font-size-base: 1rem;       /* 16px */
--font-size-lg: 1.125rem;     /* 18px */
--font-size-xl: 1.5rem;       /* 24px */
--font-size-2xl: 2rem;        /* 32px */
--font-size-3xl: 2.5rem;      /* 40px */
```

### **Spacing**
```css
--spacing-xs: 0.25rem;   /* 4px */
--spacing-sm: 0.5rem;    /* 8px */
--spacing-md: 1rem;      /* 16px */
--spacing-lg: 1.5rem;    /* 24px */
--spacing-xl: 2rem;      /* 32px */
--spacing-2xl: 3rem;     /* 48px */
```

### **Border Radius**
```css
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 16px;
--radius-xl: 20px;
--radius-full: 9999px;
```

### **Shadows**
```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
--shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);
--shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.08);
```

---

## Bar Specificaties

### **Start Bars (Sectie 1 - Links)**
- **Hoogte:** 56px
- **Breedte:** 100% van kolom
- **Achtergrond:** Licht groen (#90EE90)
- **Border:** 2px solid groen (#4CAF50)
- **Border radius:** 12px
- **Text:** Bedrag gecentreerd, bold

### **Verblijf Bars (Sectie 2 - Midden)**

#### **Used Portion (geel)**
- **Achtergrond:** Licht geel (#FFE082)
- **Border:** 2px solid oranje (#FFA726)
- **Text:** Bedrag in euros

#### **Return Portion (groen)**
- **Achtergrond:** Licht groen (#81C784)
- **Border:** 2px solid groen (#4CAF50)
- **Text:** Bedrag in euros

#### **Extra Portion (roze/rood)**
- **Achtergrond:** Licht roze/rood (#FFCDD2)
- **Border:** 2px **dashed** rood (#E85D45)
- **Text:** Bedrag in euros

### **Bar Height**
Alle bars in sectie 2: **56px hoog**

### **Proportionele Breedte Berekeningen**

```javascript
// Voor underfilled (zoals Borg)
const usedPercentage = (gebruikt / voorschot) * 100;
const returnPercentage = 100 - usedPercentage;

// Voorbeeld Borg:
// gebruikt = 600, voorschot = 800
// usedPercentage = 75%
// returnPercentage = 25%
// Bar: 75% geel + 25% groen

// Voor overfilled (zoals GWE)
const baseWidth = 100; // voorschot neemt 100% van baseline
const extraPercentage = ((verbruik - voorschot) / voorschot) * 100;

// Voorbeeld GWE:
// voorschot = 350, verbruik = 450
// extra = 100
// extraPercentage = 28.6%
// Bar: 100% geel + 28.6% roze (extends beyond)
```

---

## Page Layout Specificaties

### **Pagina Formaat**
- **Print size:** A4 (210mm × 297mm)
- **Margins:** 20mm all around
- **Orientation:** Portrait

### **Grid Structuur Sectie 1 & 2**

```
┌────────────────────────────────────────────────────────┐
│                       HEADER                           │
│  Logo + Title         |    Guest Info + Period Badge   │
└────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────┐
│                    INTRO TEXT                          │
└────────────────────────────────────────────────────────┘
┌─────────────┬──┬──────────────────────┬──┬────────────┐
│  SECTIE 1   ││  │    SECTIE 2         ││  │  RESULT   │
│  (Start)    ││█│    (Verblijf)       ││┊│            │
│             ││█│                     ││┊│            │
│   ~25%      ││ │       ~55%          ││ │    ~20%    │
└─────────────┴──┴──────────────────────┴──┴────────────┘
       ↓
═══════════════════════════════════════════════════════════
       ↓
┌────────────────────────────────────────────────────────┐
│                    SECTIE 3                            │
│              (Uitleg van waardes)                      │
│                                                        │
│  Volledige breedte, verticaal gestapeld              │
└────────────────────────────────────────────────────────┘
```

### **Column Verhoudingen (Sectie 1 & 2)**
```css
grid-template-columns: 25% 2px 55% 2px 20%;
```

- Kolom 1 (Start): 25%
- Kolom 2 (Divider): 2px solid lijn
- Kolom 3 (Verblijf): 55%
- Kolom 4 (Divider): 2px dotted lijn
- Kolom 5 (Result): 20%

---

## Componenten Breakdown

### **1. Header**
```
┌──────────────────────────────────────────────┐
│ [Logo RR]  RyanRent               Fam. Jansen│
│            Eindoverzicht Verblijf  Zeezicht  │
│                                    P1-P12    │
└──────────────────────────────────────────────┘
```

**Elementen:**
- Logo (56×56px, dark background)
- Brand naam (2rem, bold)
- Subtitle (1rem, secondary color)
- Guest naam (1.125rem, bold, right-aligned)
- Property naam (0.875rem, secondary, right-aligned)
- Period badge (coral background, white text, pill-shaped)

### **2. Intro**
```
┌────────────────────────────────────────────────┐
│  Uw persoonlijke overzicht in één oogopslag.  │
│  Hieronder ziet u wat u vooraf betaalde en    │
│  hoe dit tijdens het verblijf is gebruikt.    │
└────────────────────────────────────────────────┘
```

**Styling:**
- Background: gradient (light coral)
- Padding: 1.5rem
- Border radius: 16px
- Text: centered, 0.875rem, secondary color

### **3. Sectie Headers**
```
┌──────────────┐  ┌────────────────┐  ┌─────────────┐
│START VERBLIJF│  │    VERBLIJF    │  │    Extra    │
│     P1       │  │   P1 - P12     │  │  Verbruik   │
└──────────────┘  └────────────────┘  └─────────────┘
```

**Styling:**
- Title: 2rem, bold
- Subtitle: 0.875rem, tertiary color
- Text: centered

### **4. Category Row (in Sectie 1)**
```
┌───────────────────────┐
│ BORG                  │
│ €800                  │
│ [████████████████]    │
│ Borg Vooraf betaald...│
└───────────────────────┘
```

**Elementen:**
- Label: 1rem, bold (BORG, GWE, CLEANING)
- Amount: 2.5rem, extra bold (€800)
- Bar: 56px height, full width, green
- Description: 0.875rem, secondary color

### **5. Category Row (in Sectie 2)**
```
┌──────────────────────────────┬────────────┐
│ [██████][██]                 │  +200 Eu.  │
│  600 Eu. 200 Eu.             │  (groen)   │
│                              │            │
│ Gebruikt: €600               │            │
│ Terug: €200                  │            │
└──────────────────────────────┴────────────┘
```

**Elementen:**
- Horizontal bars met proportionele width
- Detail labels onder bars (0.875rem)
- Result amount rechts (1.5rem, bold, colored)

### **6. Uitleg Card (Sectie 3)**
```
┌─────────────────────────────────────────────┐
│▌ BORG                                       │
│▌                                            │
│▌ [bar visualization]                        │
│▌                                            │
│▌ Schades XXX --------- 30 Eu               │
│▌ Schades XXX --------- 30 Eu               │
│▌ ...                                        │
│▌                                            │
│▌ Totaal: 600 Eu. gebruikt                  │
│▌ 200 Eu. minder verbruikt dan voorschot    │
└─────────────────────────────────────────────┘
```

**Styling:**
- Background: light gray (#F8F8F8)
- Left border: 4px solid coral
- Padding: 1.5rem
- Border radius: 16px
- Margin bottom: 1rem

### **7. Settlement Table**
```
┌────────────────────────────────────────────────────┐
│  EINDAFREKENING                                    │
│                                                    │
│  ┌─────────┬──────────┬──────────┬──────────────┐ │
│  │Onderdeel│Voorschot │Gebruikt  │Resultaat     │ │
│  ├─────────┼──────────┼──────────┼──────────────┤ │
│  │🔒 Borg  │€800      │€600      │€200 terug    │ │
│  │⚡ G/W/E │€350      │€450      │€200 bijbetalen│ │
│  │🧹 Clean │€250      │€400      │€150 bijbetalen│ │
│  ├─────────┴──────────┴──────────┼──────────────┤ │
│  │          TOTAAL NETTO         │-€50          │ │
│  └───────────────────────────────┴──────────────┘ │
└────────────────────────────────────────────────────┘
```

**Styling:**
- Background: gradient (light coral)
- Padding: 2rem
- Border radius: 16px
- Table: white background, borders
- Footer row: bold, larger font, thick top border

### **8. Footer**
```
┌────────────────────────────────────────────────┐
│         RyanRent | Contact Info               │
│         Voor vragen: info@ryanrent.nl         │
│         Gedetailleerd rapport beschikbaar     │
└────────────────────────────────────────────────┘
```

**Styling:**
- Border top: 1px solid border color
- Padding top: 2rem
- Text: centered, 0.75rem, tertiary color

---

## Technical Architecture

### **Stack Keuze: Python + Excel**

**Waarom:**
- Anna heeft Microsoft 365
- Excel is bekend
- Python is simpel te installeren
- Geen hosting/cloud nodig
- Makkelijk te onderhouden

### **Project Structuur**
```
ryanrent-eindafrekening/
├── input.xlsx                 # Anna vult dit in
├── template.html              # HTML template met placeholders
├── generate.py                # Main generator script
├── generate.bat              # Windows launcher (dubbelklik)
├── requirements.txt          # Python dependencies
├── README.md                 # Instructies voor Anna
├── output/                   # Gegenereerde PDFs komen hier
│   └── .gitkeep
└── assets/                   # Optional: logo, fonts
    └── logo.png
```

### **Data Flow**
```
Excel Input
    ↓
Python Script (generate.py)
    ↓
Lees Excel data (openpyxl)
    ↓
Bereken automatisch:
    - Percentages voor bars
    - Totalen
    - Netto bedrag
    ↓
Vul HTML template (Jinja2)
    ↓
Genereer PDF (pdfkit/weasyprint)
    ↓
Output PDF in /output folder
```

---

## Excel Input Template Specificatie

### **Sheet 1: Hoofdgegevens**

**Structuur (twee kolommen):**
```
A                    | B
─────────────────────┼──────────────
Gast Naam            | Fam. Jansen
Property Naam        | Vakantiewoning Zeezicht
Property Adres       | Strandweg 42, Zandvoort
Periode Start        | P1
Periode Eind         | P12
Aantal Dagen         | 12
                     |
BORG                 |
Borg Voorschot       | 800
Borg Gebruikt        | 600
                     |
GWE                  |
GWE Voorschot        | 350
GWE Verbruik Totaal  | 450
Gas Euro             | 275
Water Euro           | 75
Electra Euro         | 100
Electra kWh          | 10000
                     |
SCHOONMAAK           |
Schoonmaak Voorschot | 250
Schoonmaak Gebruikt  | 400
Schoonmaak Extra     | 150
```

### **Sheet 2: Schades Detail (Optioneel)**

```
A                        | B
─────────────────────────┼────────
Schade Omschrijving      | Bedrag
─────────────────────────┼────────
Reparatie deur keuken    | 30
Schoonmaak extra keuken  | 30
Vervangen lamp           | 25
Reparatie tegelwerk      | 30
Schoonmaak vloerbedekking| 30
Reparatie wasmachine     | 30
Vervangen gordijn        | 30
Schilderwerk schade      | 30
```

**Notes:**
- Als Sheet 2 aanwezig is, gebruik deze voor gedetailleerde breakdown
- Als niet aanwezig, toon alleen totaal
- Som van Sheet 2 moet matchen met "Borg Gebruikt" uit Sheet 1

---

## Python Script Specificatie

### **Dependencies (requirements.txt)**
```
openpyxl==3.1.2        # Excel reading
jinja2==3.1.2          # Template engine
weasyprint==60.1       # HTML to PDF (recommended)
# OR
pdfkit==1.0.0          # Alternative: HTML to PDF
wkhtmltopdf            # Required for pdfkit
```

### **Main Script Flow (generate.py)**

```python
#!/usr/bin/env python3
"""
RyanRent Eindafrekening Generator
Genereert visuele eindafrekening PDF vanuit Excel input
"""

import openpyxl
from jinja2 import Template
from weasyprint import HTML
from datetime import datetime
import os

def read_excel_data(filepath='input.xlsx'):
    """
    Lees data uit Excel
    Returns: dict met alle benodigde data
    """
    wb = openpyxl.load_workbook(filepath)
    sheet = wb['Hoofdgegevens']
    
    data = {
        # Basis info
        'gast_naam': sheet['B1'].value,
        'property_naam': sheet['B2'].value,
        'property_adres': sheet['B3'].value,
        'periode_start': sheet['B4'].value,
        'periode_eind': sheet['B5'].value,
        'aantal_dagen': sheet['B6'].value,
        
        # Borg
        'borg_voorschot': float(sheet['B8'].value),
        'borg_gebruikt': float(sheet['B9'].value),
        
        # GWE
        'gwe_voorschot': float(sheet['B11'].value),
        'gwe_verbruik': float(sheet['B12'].value),
        'gwe_gas': float(sheet['B13'].value),
        'gwe_water': float(sheet['B14'].value),
        'gwe_electra_euro': float(sheet['B15'].value),
        'gwe_electra_kwh': float(sheet['B16'].value),
        
        # Schoonmaak
        'clean_voorschot': float(sheet['B18'].value),
        'clean_gebruikt': float(sheet['B19'].value),
        'clean_extra': float(sheet['B20'].value),
    }
    
    # Probeer schades sheet te lezen
    try:
        schades_sheet = wb['Schades Detail']
        data['schades'] = []
        for row in schades_sheet.iter_rows(min_row=2, values_only=True):
            if row[0] and row[1]:
                data['schades'].append({
                    'omschrijving': row[0],
                    'bedrag': float(row[1])
                })
    except:
        data['schades'] = None
    
    wb.close()
    return data

def calculate_values(data):
    """
    Bereken afgeleide waardes
    """
    # Borg berekeningen
    data['borg_terug'] = data['borg_voorschot'] - data['borg_gebruikt']
    data['borg_gebruikt_pct'] = (data['borg_gebruikt'] / data['borg_voorschot']) * 100
    data['borg_terug_pct'] = 100 - data['borg_gebruikt_pct']
    
    # GWE berekeningen
    data['gwe_extra'] = data['gwe_verbruik'] - data['gwe_voorschot']
    if data['gwe_extra'] > 0:
        data['gwe_is_overfilled'] = True
        data['gwe_extra_pct'] = (data['gwe_extra'] / data['gwe_voorschot']) * 100
    else:
        data['gwe_is_overfilled'] = False
        data['gwe_gebruikt_pct'] = (data['gwe_verbruik'] / data['gwe_voorschot']) * 100
        data['gwe_terug_pct'] = 100 - data['gwe_gebruikt_pct']
        data['gwe_terug'] = data['gwe_voorschot'] - data['gwe_verbruik']
    
    # Schoonmaak berekeningen
    data['clean_extra_calc'] = data['clean_gebruikt'] - data['clean_voorschot']
    if data['clean_extra_calc'] > 0:
        data['clean_is_overfilled'] = True
        data['clean_extra_pct'] = (data['clean_extra_calc'] / data['clean_voorschot']) * 100
    else:
        data['clean_is_overfilled'] = False
        data['clean_gebruikt_pct'] = (data['clean_gebruikt'] / data['clean_voorschot']) * 100
        if data['clean_gebruikt_pct'] < 100:
            data['clean_terug_pct'] = 100 - data['clean_gebruikt_pct']
            data['clean_terug'] = data['clean_voorschot'] - data['clean_gebruikt']
    
    # Netto berekening
    netto = 0
    if data['borg_terug'] > 0:
        netto += data['borg_terug']
    if data.get('gwe_extra', 0) > 0:
        netto -= data['gwe_extra']
    elif data.get('gwe_terug', 0) > 0:
        netto += data['gwe_terug']
    if data.get('clean_extra_calc', 0) > 0:
        netto -= data['clean_extra_calc']
    elif data.get('clean_terug', 0) > 0:
        netto += data['clean_terug']
    
    data['netto'] = netto
    data['netto_is_positive'] = netto > 0
    
    # Datum gegenereerd
    data['generated_date'] = datetime.now().strftime('%d-%m-%Y %H:%M')
    
    return data

def generate_pdf(data, output_filename=None):
    """
    Genereer PDF vanuit template
    """
    # Lees HTML template
    with open('template.html', 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Vul template met Jinja2
    template = Template(template_content)
    html_filled = template.render(**data)
    
    # Genereer output filename als niet gegeven
    if not output_filename:
        safe_name = data['gast_naam'].replace(' ', '_').replace('.', '')
        output_filename = f"eindafrekening_{safe_name}_{data['periode_start']}-{data['periode_eind']}.pdf"
    
    output_path = os.path.join('output', output_filename)
    
    # Genereer PDF met WeasyPrint
    HTML(string=html_filled).write_pdf(output_path)
    
    return output_path

def main():
    """
    Main functie - run complete flow
    """
    print("🏠 RyanRent Eindafrekening Generator")
    print("=" * 50)
    
    try:
        # Stap 1: Lees Excel
        print("\n📊 Excel data inlezen...")
        data = read_excel_data()
        print(f"   ✓ Gast: {data['gast_naam']}")
        print(f"   ✓ Property: {data['property_naam']}")
        print(f"   ✓ Periode: {data['periode_start']} - {data['periode_eind']}")
        
        # Stap 2: Bereken waardes
        print("\n🔢 Waardes berekenen...")
        data = calculate_values(data)
        print(f"   ✓ Borg: €{data['borg_terug']:.0f} terug")
        print(f"   ✓ GWE: {'€' + str(abs(data.get('gwe_extra', 0))) + ' extra' if data.get('gwe_is_overfilled') else '€' + str(data.get('gwe_terug', 0)) + ' terug'}")
        print(f"   ✓ Schoonmaak: {'€' + str(abs(data.get('clean_extra_calc', 0))) + ' extra' if data.get('clean_is_overfilled') else '€' + str(data.get('clean_terug', 0)) + ' terug'}")
        print(f"   ✓ Netto: {'€' + str(abs(data['netto'])):.0f} {'terug' if data['netto_is_positive'] else 'bijbetalen'}")
        
        # Stap 3: Genereer PDF
        print("\n📄 PDF genereren...")
        output_path = generate_pdf(data)
        print(f"   ✓ PDF opgeslagen: {output_path}")
        
        print("\n✅ Klaar! PDF is gegenereerd.")
        print(f"\n📂 Locatie: {os.path.abspath(output_path)}")
        
    except FileNotFoundError as e:
        print(f"\n❌ Fout: Bestand niet gevonden - {e}")
        print("   Zorg dat 'input.xlsx' en 'template.html' aanwezig zijn.")
    except Exception as e:
        print(f"\n❌ Fout: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nDruk op Enter om af te sluiten...")

if __name__ == "__main__":
    main()
```

### **Windows Launcher (generate.bat)**
```batch
@echo off
echo ========================================
echo  RyanRent Eindafrekening Generator
echo ========================================
echo.
python generate.py
pause
```

---

## HTML Template Specificatie

### **Template Structuur**

Het HTML template gebruikt Jinja2 syntax voor placeholders:

```html
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <title>RyanRent - Eindafrekening {{ gast_naam }}</title>
    <style>
        /* Alle CSS from design system inline */
    </style>
</head>
<body>
    <div class="page">
        <!-- HEADER -->
        <header class="header">
            <div class="logo-section">
                <div class="logo">RR</div>
                <div class="brand-info">
                    <h1>RyanRent</h1>
                    <p>Eindoverzicht Verblijf</p>
                </div>
            </div>
            <div class="header-meta">
                <div class="guest-name">{{ gast_naam }}</div>
                <div class="property-name">{{ property_naam }}</div>
                <div class="property-name">{{ property_adres }}</div>
                <span class="period">{{ periode_start }}-{{ periode_eind }} ({{ aantal_dagen }} dagen)</span>
            </div>
        </header>

        <!-- INTRO -->
        <div class="intro">
            <p>Uw persoonlijke overzicht in één oogopslag. Hieronder ziet u wat u vooraf betaalde en hoe dit tijdens het verblijf is gebruikt.</p>
        </div>

        <!-- VISUAL GRID -->
        <div class="visual-grid">
            <!-- SECTIE 1: START -->
            <div class="sectie-1">
                <div class="column-header">
                    <h2>START VERBLIJF</h2>
                    <p>{{ periode_start }}</p>
                </div>
                
                <!-- BORG -->
                <div class="start-card">
                    <div class="category-label">BORG</div>
                    <div class="amount">€{{ borg_voorschot|int }}</div>
                    <div class="bar-prepaid"></div>
                    <div class="description">Borg Vooraf betaald en gereserveerd voor u.</div>
                </div>

                <!-- GWE -->
                <div class="start-card">
                    <div class="category-label">GWE</div>
                    <div class="amount">€{{ gwe_voorschot|int }}</div>
                    <div class="bar-prepaid"></div>
                    <div class="description">Voorschot GWE</div>
                </div>

                <!-- CLEANING -->
                <div class="start-card">
                    <div class="category-label">CLEANING</div>
                    <div class="amount">€{{ clean_voorschot|int }}</div>
                    <div class="bar-prepaid"></div>
                    <div class="description">Basis Schoonmaak pakket</div>
                </div>
            </div>

            <!-- VERTICAL DIVIDER -->
            <div class="divider-solid"></div>

            <!-- SECTIE 2: VERBLIJF -->
            <div class="sectie-2">
                <div class="column-header">
                    <h2>VERBLIJF</h2>
                    <p>{{ periode_start }} - {{ periode_eind }}</p>
                </div>

                <!-- BORG -->
                <div class="verblijf-row">
                    <div class="bars-container">
                        <div class="bar-used" style="width: {{ borg_gebruikt_pct }}%;">
                            {{ borg_gebruikt|int }} Eu.
                        </div>
                        <div class="bar-return" style="width: {{ borg_terug_pct }}%;">
                            {{ borg_terug|int }} Eu.
                        </div>
                    </div>
                    <div class="details">
                        <div>Gebruikt: €{{ borg_gebruikt|int }}</div>
                        <div>Terug: €{{ borg_terug|int }}</div>
                    </div>
                </div>

                <!-- GWE -->
                <div class="verblijf-row">
                    {% if gwe_is_overfilled %}
                    <div class="bars-container-overfilled">
                        <div class="bar-used-full">{{ gwe_voorschot|int }} Eu.</div>
                        <div class="bar-extra" style="width: {{ gwe_extra_pct }}%;">
                            {{ gwe_extra|int }} Eu.
                        </div>
                    </div>
                    {% else %}
                    <div class="bars-container">
                        <div class="bar-used" style="width: {{ gwe_gebruikt_pct }}%;">
                            {{ gwe_verbruik|int }} Eu.
                        </div>
                        {% if gwe_terug > 0 %}
                        <div class="bar-return" style="width: {{ gwe_terug_pct }}%;">
                            {{ gwe_terug|int }} Eu.
                        </div>
                        {% endif %}
                    </div>
                    {% endif %}
                    <div class="details">
                        <div>Voorschot: €{{ gwe_voorschot|int }}</div>
                        <div>Verbruik: €{{ gwe_verbruik|int }}</div>
                        {% if gwe_is_overfilled %}
                        <div>Extra: €{{ gwe_extra|int }}</div>
                        {% endif %}
                    </div>
                </div>

                <!-- CLEANING -->
                <div class="verblijf-row">
                    {% if clean_is_overfilled %}
                    <div class="bars-container-overfilled">
                        <div class="bar-used-full">{{ clean_voorschot|int }} Eu.</div>
                        <div class="bar-extra" style="width: {{ clean_extra_pct }}%;">
                            {{ clean_extra_calc|int }} Eu.
                        </div>
                    </div>
                    {% else %}
                    <div class="bars-container">
                        <div class="bar-used" style="width: {{ clean_gebruikt_pct }}%;">
                            {{ clean_gebruikt|int }} Eu.
                        </div>
                    </div>
                    {% endif %}
                    <div class="details">
                        <div>Gebruikt: €{{ clean_gebruikt|int }}</div>
                        {% if clean_is_overfilled %}
                        <div>Extra uren: €{{ clean_extra_calc|int }}</div>
                        {% endif %}
                    </div>
                </div>
            </div>

            <!-- VERTICAL DIVIDER DOTTED -->
            <div class="divider-dotted"></div>

            <!-- SECTIE 2.5: RESULTS -->
            <div class="sectie-results">
                <div class="column-header">
                    <h2>Extra<br>Verbruik</h2>
                </div>

                <div class="result-amount positive">
                    +{{ borg_terug|int }} Eu.
                </div>

                <div class="result-amount {% if gwe_is_overfilled %}negative{% else %}positive{% endif %}">
                    {% if gwe_is_overfilled %}-{{ gwe_extra|int }}{% else %}+{{ gwe_terug|int }}{% endif %} Eu.
                </div>

                <div class="result-amount {% if clean_is_overfilled %}negative{% else %}neutral{% endif %}">
                    {% if clean_is_overfilled %}-{{ clean_extra_calc|int }}{% else %}€0{% endif %} Eu.
                </div>

                <div class="netto-amount {% if netto_is_positive %}positive{% else %}negative{% endif %}">
                    {{ netto|int }} Eu.<br>
                    <span class="netto-label">Netto Eind Afrek.</span>
                </div>
            </div>
        </div>

        <!-- HORIZONTAL SEPARATOR -->
        <div class="horizontal-separator"></div>

        <!-- SECTIE 3: UITLEG -->
        <section class="uitleg-section">
            <h3 class="section-title">Uitleg van waardes</h3>

            <!-- BORG UITLEG -->
            <div class="uitleg-card">
                <h4>BORG</h4>
                <div class="uitleg-bar-container">
                    <div class="bar-used" style="width: {{ borg_gebruikt_pct }}%;">
                        {{ borg_gebruikt|int }} Eu.
                    </div>
                    <div class="bar-return" style="width: {{ borg_terug_pct }}%;">
                        {{ borg_terug|int }} Eu.
                    </div>
                </div>
                
                {% if schades %}
                <div class="detail-list">
                    {% for schade in schades %}
                    <div class="detail-row">
                        <span>{{ schade.omschrijving }}</span>
                        <span>{{ schade.bedrag|int }} Eu</span>
                    </div>
                    {% endfor %}
                    <div class="detail-total">
                        <span>Totaal gebruikt:</span>
                        <span>{{ borg_gebruikt|int }} Eu.</span>
                    </div>
                </div>
                {% endif %}
                
                <div class="conclusion">
                    {{ borg_terug|int }} Eu. minder verbruikt dan voorschot
                </div>
            </div>

            <!-- GWE UITLEG -->
            <div class="uitleg-card">
                <h4>GWE</h4>
                <div class="uitleg-bar-container">
                    <div class="bar-used-full">{{ gwe_voorschot|int }} Eu.</div>
                    {% if gwe_is_overfilled %}
                    <div class="bar-extra" style="width: {{ gwe_extra_pct }}%;">
                        {{ gwe_extra|int }} Eu.
                    </div>
                    {% endif %}
                </div>
                
                <div class="detail-list">
                    <div class="detail-row">
                        <span>Gas Verbruik {{ periode_start }}-{{ periode_eind }}</span>
                        <span>{{ gwe_gas|int }} Eu</span>
                    </div>
                    <div class="detail-row">
                        <span>Water Verbruik {{ periode_start }}-{{ periode_eind }}</span>
                        <span>{{ gwe_water|int }} Eu</span>
                    </div>
                    <div class="detail-row">
                        <span>Electra Verbruik ({{ gwe_electra_kwh|int }} kWh)</span>
                        <span>{{ gwe_electra_euro|int }} Eu</span>
                    </div>
                    <div class="detail-total">
                        <span>Totaal verbruik:</span>
                        <span>{{ gwe_verbruik|int }} Eu.</span>
                    </div>
                    <div class="detail-row">
                        <span>Voorschot:</span>
                        <span>{{ gwe_voorschot|int }} Eu.</span>
                    </div>
                    {% if gwe_is_overfilled %}
                    <div class="detail-row extra">
                        <span>Extra:</span>
                        <span>{{ gwe_extra|int }} Eu.</span>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- CLEANING UITLEG -->
            <div class="uitleg-card">
                <h4>CLEANING</h4>
                <div class="uitleg-bar-container">
                    <div class="bar-used-full">{{ clean_voorschot|int }} Eu.</div>
                    {% if clean_is_overfilled %}
                    <div class="bar-extra" style="width: {{ clean_extra_pct }}%;">
                        {{ clean_extra_calc|int }} Eu.
                    </div>
                    {% endif %}
                </div>
                
                <div class="detail-list">
                    <div class="detail-row">
                        <span>Basis schoonmaak pakket</span>
                        <span>{{ clean_voorschot|int }} Eu (included)</span>
                    </div>
                    {% if clean_is_overfilled %}
                    <div class="detail-row extra">
                        <span>Extra uren nodig</span>
                        <span>{{ clean_extra_calc|int }} Eu</span>
                    </div>
                    <div class="detail-note">
                        Reden: Grondige extra reiniging nodig na verblijf
                    </div>
                    {% else %}
                    <div class="detail-note success">
                        Het schoonmaakpakket was voldoende voor uw verblijf.
                    </div>
                    {% endif %}
                </div>
            </div>
        </section>

        <!-- SETTLEMENT TABLE -->
        <section class="settlement-section">
            <h3 class="section-title">💰 Eindafrekening</h3>
            
            <table class="settlement-table">
                <thead>
                    <tr>
                        <th>Onderdeel</th>
                        <th>Voorschot</th>
                        <th>Gebruikt/Verbruik</th>
                        <th>Resultaat</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>🔒 Borg</strong></td>
                        <td>€{{ borg_voorschot|int }}</td>
                        <td>€{{ borg_gebruikt|int }}</td>
                        <td class="positive">€{{ borg_terug|int }} terug</td>
                    </tr>
                    <tr>
                        <td><strong>⚡ G/W/E</strong></td>
                        <td>€{{ gwe_voorschot|int }}</td>
                        <td>€{{ gwe_verbruik|int }}</td>
                        <td class="{% if gwe_is_overfilled %}negative{% else %}positive{% endif %}">
                            {% if gwe_is_overfilled %}
                            €{{ gwe_extra|int }} bijbetalen
                            {% else %}
                            €{{ gwe_terug|int }} terug
                            {% endif %}
                        </td>
                    </tr>
                    <tr>
                        <td><strong>🧹 Schoonmaak</strong></td>
                        <td>€{{ clean_voorschot|int }}</td>
                        <td>€{{ clean_gebruikt|int }}</td>
                        <td class="{% if clean_is_overfilled %}negative{% else %}neutral{% endif %}">
                            {% if clean_is_overfilled %}
                            €{{ clean_extra_calc|int }} bijbetalen
                            {% else %}
                            €0
                            {% endif %}
                        </td>
                    </tr>
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="3"><strong>TOTAAL NETTO</strong></td>
                        <td class="{% if netto_is_positive %}positive{% else %}negative{% endif %}">
                            <strong>{% if not netto_is_positive %}-{% endif %}€{{ netto|abs|int }}</strong>
                        </td>
                    </tr>
                </tfoot>
            </table>

            <div class="payment-info">
                {% if netto_is_positive %}
                <p><strong>Terugbetaling:</strong> Het bedrag van €{{ netto|int }} wordt binnen 7 werkdagen overgemaakt op uw rekening.</p>
                {% else %}
                <p><strong>Bijbetaling:</strong> Gelieve €{{ netto|abs|int }} over te maken binnen 14 dagen naar NL00 BANK 0123 4567 89 o.v.v. {{ gast_naam }} - {{ periode_start }}/{{ periode_eind }}</p>
                {% endif %}
            </div>
        </section>

        <!-- FOOTER -->
        <footer class="footer">
            <p><strong>RyanRent</strong> | Strandweg 100, 2042 AA Zandvoort</p>
            <p>Tel: +31 (0)23 123 4567 | Email: info@ryanrent.nl | www.ryanrent.nl</p>
            <p style="margin-top: 1rem;">Voor vragen over deze afrekening kunt u contact opnemen met onze administratie.</p>
            <p>Een gedetailleerd incheck- en eindcheck rapport met foto's is separaat beschikbaar op aanvraag.</p>
            <p style="margin-top: 1rem; font-size: 0.7rem; color: #A0A0A0;">
                Gegenereerd op: {{ generated_date }}
            </p>
        </footer>
    </div>
</body>
</html>
```

---

## Installation & Setup Instructies

### **Voor de Developer (jij)**

1. **Project setup:**
```bash
mkdir ryanrent-eindafrekening
cd ryanrent-eindafrekening

# Create folders
mkdir output assets

# Create files
touch generate.py
touch generate.bat
touch template.html
touch requirements.txt
touch README.md

# Create Excel template (in Excel)
# Sheet 1: "Hoofdgegevens"
# Sheet 2: "Schades Detail"
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Test run:**
```bash
python generate.py
```

---

### **Voor Anna (eindgebruiker)**

**Eenmalige Setup (30 minuten):**

1. **Installeer Python:**
   - Download van python.org
   - Tijdens installatie: vink "Add Python to PATH" aan
   - Installeer

2. **Setup project folder:**
   - Unzip `ryanrent-eindafrekening.zip`
   - Open command prompt in die folder
   - Run: `pip install -r requirements.txt`

3. **Test:**
   - Dubbelklik `generate.bat`
   - Als het werkt zie je een PDF in `/output`

**Dagelijks Gebruik (5 minuten):**

1. Open `input.xlsx`
2. Vul klantgegevens in (Sheet 1)
3. Vul schades in indien nodig (Sheet 2)
4. Save Excel
5. Dubbelklik `generate.bat`
6. PDF staat in `/output` folder
7. Attach aan email en verstuur

---

## Error Handling & Edge Cases

### **Error Cases die Script moet handlen:**

1. **Excel not found:**
   - Error: "input.xlsx niet gevonden"
   - Solution: Zorg dat Excel in dezelfde folder staat

2. **Missing template:**
   - Error: "template.html niet gevonden"
   - Solution: Check of template aanwezig is

3. **Invalid data (letters instead of numbers):**
   - Error: "Kan bedrag niet converteren naar nummer"
   - Solution: Check of alle bedragen getallen zijn

4. **Division by zero (voorschot = 0):**
   - Vermijd door check: `if voorschot > 0`

5. **Negative voorschot:**
   - Validatie: voorschot moet >= 0

6. **Output folder doesn't exist:**
   - Script maakt folder aan indien niet aanwezig

### **Edge Case Scenarios:**

**Scenario 1: Alles exact 0**
- Borg: 0 gebruikt van 800 → +800 terug
- GWE: 0 verbruik van 350 → +350 terug
- Clean: 0 extra van 250 → €0
- Netto: +1150

**Scenario 2: Alles exact gelijk**
- Borg: 800 gebruikt van 800 → €0
- GWE: 350 verbruik van 350 → €0
- Clean: 250 gebruikt van 250 → €0
- Netto: €0
- Bars: alle 100% geel, geen groen/roze

**Scenario 3: Extreme overage**
- GWE: 1500 verbruik van 350 → -1150
- Bar: normale geel + zeer lange roze bar
- Percentage berekening: (1150/350)*100 = 328%

**Scenario 4: Geen schades lijst**
- Sheet 2 niet aanwezig of leeg
- Toon alleen totaal in sectie 3
- Geen detail lijst

**Scenario 5: Zeer lange gast naam**
- Truncate in UI indien > 30 characters
- Filename: max 50 chars, rest vervangen door ...

---

## Testing Checklist

### **Functionele Tests:**

- [ ] Excel met normale data → PDF correct
- [ ] Excel met edge case (alles 0) → PDF correct
- [ ] Excel zonder Sheet 2 → PDF zonder schades lijst
- [ ] Bars tonen correcte proporties
- [ ] Kleuren correct (groen = terug, rood = betalen)
- [ ] Netto berekening klopt
- [ ] Percentages kloppen (optellen tot 100% of meer)
- [ ] Overfilled bars gaan over dotted line
- [ ] Underfilled bars blijven binnen bounds
- [ ] PDF print goed op A4
- [ ] Alle fonts/styling zichtbaar in PDF

### **Edge Case Tests:**

- [ ] Voorschot = 0 → geen error
- [ ] Verbruik = 0 → bar is 0%, geen crash
- [ ] Extreme bedragen (€10,000+) → fit nog steeds
- [ ] Speciale characters in naam → geen crash
- [ ] Zeer lange periode naam → fits
- [ ] Geen schades → sectie 3 toont alleen totaal

### **UX Tests:**

- [ ] Anna kan Excel invullen zonder hulp
- [ ] generate.bat werkt met dubbelklik
- [ ] Error messages zijn duidelijk
- [ ] PDF opent automatisch na generatie (optioneel)
- [ ] Output filename is herkenbaar

---

## Future Enhancements

### **Phase 2: Automation**

1. **Email Parsing:**
   - Read facturen van Gmail
   - OCR met Google Vision API of Claude
   - Auto-fill Excel

2. **Meterstanden OCR:**
   - Upload foto's van meters
   - Extract getallen
   - Bereken verbruik automatisch

3. **Database Storage:**
   - Sla historical data op
   - Trends analysis
   - Klant historie

### **Phase 3: Web Portal**

1. **Upload Interface:**
   - Drag & drop facturen
   - Auto-generate
   - Download PDF

2. **Client Portal:**
   - Klant kan inloggen
   - Zie afrekening online
   - Approve/Bezwaar button
   - History van verblijven

3. **Response Mechanism:**
   - Email met "Akkoord" button
   - Track responses
   - Auto-reminder na X dagen

### **Phase 4: Power Automate Integration**

1. **Migrate naar Microsoft Flow:**
   - Excel Online als input
   - Auto-email naar klanten
   - Response tracking
   - Integration met administratie systeem

---

## Success Criteria

### **Dit project is succesvol als:**

1. **Anna kan het gebruiken zonder hulp** na 5 minuten uitleg
2. **PDF is visueel duidelijk** - klanten snappen het meteen
3. **Geen extra werk** - Anna doet nu al deze stappen, alleen mooier gepresenteerd
4. **Minder discussies** - klanten accepteren afrekening zonder vragen
5. **Professioneler** - RyanRent ziet er beter uit dan concurrentie
6. **Schaalbaar** - kan later geautomatiseerd worden

### **KPI's:**

- Aantal "Waarom betaal ik dit?" emails: **-80%**
- Tijd van Anna per afrekening: **-50%** (van 20min naar 10min)
- Klant tevredenheid score: **+30%**
- Aantal correcties/disputes: **-70%**

---

## Support & Maintenance

### **Als er iets mis gaat:**

1. **Python errors:**
   - Check of alle packages geïnstalleerd zijn
   - Run: `pip install -r requirements.txt --upgrade`

2. **PDF generatie faalt:**
   - WeasyPrint heeft soms issues met fonts
   - Alternative: switch naar pdfkit
   - Check if wkhtmltopdf installed

3. **Excel niet ingelezen:**
   - Check sheet names (moet exact "Hoofdgegevens" zijn)
   - Check column B voor data
   - Check of geen lege cellen tussen data

4. **Bars zien er raar uit:**
   - Check percentage berekeningen
   - Check of voorschot > 0
   - Check CSS in template

### **Contact voor support:**

- Developer: [jouw naam]
- Email: [jouw email]
- Project repo: [github link]

---

## Appendix

### **A. Design System Reference**

Zie `/assets/financial-dashboard-style-guide.html` voor volledige design system documentatie.

### **B. Excel Template Example**

Zie `/examples/input-example.xlsx` voor voorbeeld input data.

### **C. Sample Output**

Zie `/examples/output-sample.pdf` voor voorbeeld gegenereerde PDF.

### **D. Troubleshooting Guide**

Zie `/docs/TROUBLESHOOTING.md` voor veelvoorkomende problemen en oplossingen.

---

## Version History

- **v1.0** - Initial release met Excel + Python generator
- **v1.1** - (toekomst) Email parsing toevoegen
- **v2.0** - (toekomst) Web portal implementatie

---

**Project Eigenaar:** [Jouw Naam]  
**Klant:** RyanRent  
**Datum:** November 2025  
**Status:** In Development  

---

# 🎯 BUILD INSTRUCTIONS FOR CURSOR

Om dit project te bouwen in Cursor:

1. **Start met de basis structuur:**
   ```
   Maak folders: output/, assets/
   Maak files: generate.py, template.html, requirements.txt, generate.bat
   ```

2. **Bouw generate.py:**
   - Implementeer read_excel_data()
   - Implementeer calculate_values()
   - Implementeer generate_pdf()
   - Test met dummy data

3. **Bouw template.html:**
   - Start met design system CSS (van financial dashboard)
   - Implementeer page layout (header, sections, footer)
   - Implementeer bar visualizations met correct proportions
   - Test met static data eerst

4. **Bouw Excel template:**
   - Sheet 1: Hoofdgegevens met alle fields
   - Sheet 2: Schades Detail optioneel
   - Formatteer netjes

5. **Test end-to-end:**
   - Excel invullen
   - Run generate.py
   - Check PDF output
   - Fix bugs

6. **Polish:**
   - Error handling toevoegen
   - generate.bat maken voor easy launching
   - README.md schrijven
   - Package voor Anna

**LET OP:**
- Gebruik design system colors/styling
- Test met edge cases
- Maak code maintainable voor toekomstige updates
- Documenteer goed voor Anna

---

*Einde PROJECT.md*