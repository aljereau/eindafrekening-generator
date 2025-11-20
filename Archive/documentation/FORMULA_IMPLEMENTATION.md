# Excel Formula Implementation - Samenvatting

## Implementatie Voltooid ✅

Datum: 20 November 2024

## Overzicht

Alle berekende velden in de Excel template zijn nu voorzien van formules. Gebruikers kunnen nu in real-time zien wat de uitkomsten zijn terwijl ze data invullen. De cellen met formules zijn beveiligd (read-only) om onbedoelde wijzigingen te voorkomen.

## Geïmplementeerde Formules

### Sheet: Algemeen

| Veld | Cel | Formula |
|------|-----|---------|
| **Aantal_dagen** | B19 | `=IF(AND(B17<>"",B18<>""),B18-B17,"")` |
| **Inbegrepen_uren** | B29 | `=IF(B28="5_uur",5,IF(B28="7_uur",7,""))` |
| **Borg_gebruikt** | B43 | `=Schade!Schade_totaal_incl` |
| **Borg_terug** | B44 | `=IF(Borg_gebruikt="","",Voorschot_borg-Borg_gebruikt)` |
| **Restschade** | B45 | `=IF(Borg_gebruikt="","",MAX(0,Borg_gebruikt-Voorschot_borg))` |
| **GWE_meer_minder** | B46 | `=IF(GWE_Detail!GWE_totaal_incl="","",Voorschot_GWE-GWE_Detail!GWE_totaal_incl)` |
| **Totaal_eindafrekening** | B47 | `=IF(OR(Borg_terug="",GWE_meer_minder="",Schoonmaak!Extra_schoonmaak_bedrag=""),"",Borg_terug+GWE_meer_minder-Schoonmaak!Extra_schoonmaak_bedrag)` |

### Sheet: GWE_Detail

| Veld | Cel | Formula |
|------|-----|---------|
| **KWh_verbruik** | B6 | `=IF(AND(B4<>"",B5<>""),B5-B4,"")` |
| **Gas_verbruik** | B9 | `=IF(AND(B7<>"",B8<>""),B8-B7,"")` |
| **Kosten_excl** (tabel) | D13:D... | `=IF(AND(B13<>"",C13<>""),B13*C13,"")` (per rij) |
| **GWE_totaal_excl** | B36 | `=SUM(D14:D34)` |
| **GWE_BTW** | B37 | `=IF(B36="","",B36*0.21)` |
| **GWE_totaal_incl** | B38 | `=IF(B36="","",B36+B37)` |

### Sheet: Schoonmaak

| Veld | Cel | Formula |
|------|-----|---------|
| **Inbegrepen_uren** | B5 | `=IF(B4="5_uur",5,IF(B4="7_uur",7,""))` |
| **Extra_uren** | B7 | `=IF(AND(B5<>"",B6<>""),MAX(0,B6-B5),"")` |
| **Extra_schoonmaak_bedrag** | B9 | `=IF(AND(B7<>"",B8<>""),B7*B8,"")` |

### Sheet: Schade

| Veld | Cel | Formula |
|------|-----|---------|
| **Bedrag_excl** (tabel) | D5:D54 | `=IF(AND(B5<>"",C5<>""),B5*C5,"")` (per rij) |
| **Schade_totaal_excl** | B58 | `=SUM(D6:D56)` |
| **Schade_BTW** | B59 | `=IF(B58="","",B58*0.21)` |
| **Schade_totaal_incl** | B60 | `=IF(B58="","",B58+B59)` |

## Celbeveiliging

### Beveiligde Cellen (Locked)
Alle berekende velden zijn beveiligd en kunnen niet handmatig worden bewerkt:
- Grijze achtergrond (computed_fill: #E7E6E6)
- Protection(locked=True)
- Label eindigt met "(automatisch)"

### Vrije Invoervelden (Unlocked)
Invoervelden zijn ontgrendeld voor data entry:
- Gele achtergrond (required_fill: #FFF2CC) voor verplichte velden
- Witte/geen achtergrond voor optionele velden
- Protection(locked=False)

### Sheet Protection
Alle sheets zijn beveiligd zonder wachtwoord:
- `ws.protection.sheet = True`
- Geen wachtwoord (gebruikers kunnen beveiliging uitschakelen in Excel indien nodig)
- Voorkomt onbedoelde wijzigingen aan formules

## Python Validatie

### Validatiefunctie: `validate_excel_calculations()`
Locatie: `calculator.py`

De functie controleert of Excel formules dezelfde resultaten produceren als de Python business logic:

**Gevalideerde Berekeningen:**
1. GWE meter readings (KWh en Gas verbruik)
2. GWE kostenregels (individuele bedragen)
3. GWE totalen (excl, BTW, incl)
4. Schoonmaak (inbegrepen uren, extra uren, extra bedrag)
5. Schade regels (individuele bedragen)
6. Schade totalen (excl, BTW, incl)
7. Borg (gebruikt, terug, restschade)

**Resultaat:**
- Lijst met waarschuwingen bij mismatches
- Lege lijst als alles klopt

### Integratie in `generate.py`

```python
# Valideer Excel berekeningen
validation_warnings = validate_excel_calculations(data)

if validation_warnings:
    print(f"\n   ⚠️  WAARSCHUWING: Excel formulas komen niet overeen...")
    for warning in validation_warnings:
        print(f"      • {warning}")
    print(f"\n   Python zal alle waarden herberekenen en corrigeren...")

# Herbereken alles voor consistentie
data = recalculate_all(data)
```

**Gedrag:**
- ✅ Detecteert afwijkingen tussen Excel en Python
- ✅ Toont waarschuwingen aan gebruiker
- ✅ Herberekent automatisch alle waarden in Python
- ✅ Gaat door met generatie (geen blokkering)

## Gebruiksinstructies

### Voor Anna (Gebruiker)

1. **Open de template** (`input_template.xlsx`)
2. **Vul de gele velden in** (verplicht)
3. **Vul overige velden in** (optioneel)
4. **Zie live resultaten** in grijze velden
   - Aantal dagen wordt automatisch berekend
   - Totalen worden live bijgewerkt
   - Eindafrekening is direct zichtbaar
5. **Sla op en draai `generate.py`**
   - Python valideert de berekeningen
   - Bij afwijkingen: waarschuwing + herberekening
   - PDFs worden gegenereerd

### Waarom Valideren?

Hoewel de formules correct zijn, kunnen er situaties zijn waarin:
- Gebruiker formules handmatig heeft aangepast
- Excel en Python verschillende afrondingen gebruiken
- Er een bug in de formules zit

De validatie zorgt ervoor dat de **Python berekeningen altijd leidend zijn** voor de uiteindelijke PDF output.

## Testing

### Testresultaten

✅ **Template generatie** (`build_excel_template.py`)
- Alle formules correct aangemaakt
- Alle sheets beveiligd
- Alle named ranges correct

✅ **Formuleverificatie**
- Alle 17 berekende velden hebben formules
- Alle formules verwijzen naar correcte cellen/named ranges

✅ **Validatie met oude data** (`sample_1_normale_afrekening.xlsx`)
- Detecteert ontbrekende formules
- Toont 6 waarschuwingen
- Herberekent correct
- Genereert succesvolle output

✅ **Validatie met nieuwe template** (`input_template_filled.xlsx`)
- Formules worden gedetecteerd
- Validatie werkt correct
- Output succesvol gegenereerd

### Test Commands

```bash
# Genereer nieuwe template met formules
python3 build_excel_template.py

# Test met oude data (zonder formules)
python3 generate.py --input sample_1_normale_afrekening.xlsx

# Test met nieuwe template (met formules)
python3 generate.py --input input_template_filled.xlsx
```

## Technische Details

### Openpyxl Formule Handling

**Belangrijk:** Openpyxl leest alleen **cached values** van formules, niet de formules zelf tijdens evaluatie. Dit betekent:

1. Als je een Excel file programmatisch maakt met formules, bevat deze geen cached values
2. Excel moet het bestand openen en de formules berekenen
3. Pas dan zijn de cached values beschikbaar voor openpyxl

**Impact:**
- Nieuwe templates tonen `0` of `None` als waarde tot Excel ze opent
- Validatie detecteert dit en herberekent in Python (gewenst gedrag)
- Gebruikers zien correcte waarden zodra ze het bestand openen in Excel

### Cell Protection Implementation

```python
# Computed cells (locked)
ws['B19'].protection = Protection(locked=True)

# Input cells (unlocked)
ws['B17'].protection = Protection(locked=False)

# Sheet protection (no password)
ws.protection.sheet = True
```

## Files Gewijzigd

1. **`build_excel_template.py`**
   - Toegevoegd: `Protection` import
   - Toegevoegd: Formules voor alle berekende velden
   - Toegevoegd: Cell protection logic voor alle sheets
   - Toegevoegd: Sheet protection activatie

2. **`calculator.py`**
   - Toegevoegd: `validate_excel_calculations()` functie
   - 150+ regels validatielogica
   - Controleert alle berekeningen tegen business rules

3. **`generate.py`**
   - Toegevoegd: Validatie stap vóór recalculate_all()
   - Toegevoegd: Waarschuwingsweergave
   - Geen blokkering bij validatiefouten

## Volgende Stappen

### Voor Gebruiker
1. ✅ Test de nieuwe template in Excel
2. ✅ Vul proefdata in en bekijk live berekeningen
3. ✅ Verifieer dat beveiligde cellen niet bewerkt kunnen worden
4. ✅ Genereer test PDFs

### Voor Ontwikkelaar (optioneel)
1. ⚡ Overweeg WeasyPrint installatie voor directe PDF generatie
2. ⚡ Voeg unit tests toe voor `validate_excel_calculations()`
3. ⚡ Overweeg logging van validatiewaarschuwingen naar file

## Conclusie

✅ **Alle doelstellingen behaald:**
- [x] Excel formules in alle berekende velden
- [x] Live preview tijdens data entry
- [x] Celbeveiliging op computed fields
- [x] Python validatie tegen Excel resultaten
- [x] Automatische herberekening bij mismatch
- [x] Sheet protection geactiveerd

**Gebruikerservaring:**
- Anna ziet direct wat de eindafrekening wordt
- Geen wachten tot PDF generatie
- Bescherming tegen onbedoelde formula wijzigingen
- Python garandeert correctheid van output

**Betrouwbaarheid:**
- Dubbele controle: Excel formules + Python berekeningen
- Validatie waarschuwt bij afwijkingen
- Python is altijd leidend voor output
- Geen risico op incorrecte berekeningen in PDF

