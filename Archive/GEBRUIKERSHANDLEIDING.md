# 📘 RyanRent Eindafrekening Generator - Gebruikershandleiding

**Voor:** Anna en het RyanRent team
**Versie:** 2.0 (Complete rebuild)
**Laatst bijgewerkt:** November 2024

---

## 📋 Inhoudsopgave

1. [Snelstart Gids](#snelstart-gids)
2. [Excel Template Invullen](#excel-template-invullen)
3. [PDF's Genereren](#pdfs-genereren)
4. [Veld Uitleg Per Tabblad](#veld-uitleg-per-tabblad)
5. [Veelgestelde Vragen](#veelgestelde-vragen)
6. [Probleemoplossing](#probleemoplossing)

---

## 🚀 Snelstart Gids

### Stap 1: Open de Template
1. Open `input_template.xlsx` in Excel
2. Je ziet 4 tabbladen (tabs onderaan):
   - 🔵 **Algemeen** - Basisgegevens
   - 🟢 **GWE_Detail** - Gas/Water/Elektra
   - 🟠 **Schoonmaak** - Schoonmaakuren
   - 🔴 **Schade** - Schadeposten

### Stap 2: Vul de Gegevens In
1. **Start bij Algemeen** - vul alle gele velden (verplicht) in
2. **Ga naar GWE_Detail** - vul meterstanden in
3. **Ga naar Schoonmaak** - vul werkelijke uren in
4. **Ga naar Schade** - vul eventuele schadeposten in

### Stap 3: Controleer de Berekeningen
- Grijze velden worden **automatisch berekend**
- Controleer of de bedragen kloppen
- Let op: BTW wordt automatisch berekend door Python (nog niet in Excel)

### Stap 4: Genereer PDF's
```bash
python3 generate.py
```

Je krijgt **2 PDF bestanden**:
- `{gast}_onepager_{periode}.pdf` - Simpel overzicht voor klant
- `{gast}_detail_{periode}.pdf` - Uitgebreid met alle details

---

## 📝 Excel Template Invullen

### 🔵 Tabblad 1: Algemeen

#### **Klantgegevens** (verplicht met *)

| Veld | Uitleg | Voorbeeld |
|------|--------|-----------|
| Naam Klant * | Volledige naam zoals op contract | Familie Janssen |
| Contactpersoon | Primair aanspreekpunt | Dhr. P. Janssen |
| Email * | Voor verzenden eindafrekening | p.janssen@email.nl |
| Telefoonnummer | Voor eventuele vragen | +31 6 12345678 |

#### **Objectgegevens** (adres verplicht)

| Veld | Uitleg | Voorbeeld |
|------|--------|-----------|
| Adres Object * | Volledige adres vakantiewoning | Strandweg 42 |
| Unit Nummer | Appartement/unit nummer indien van toepassing | A3 |
| Postcode | Voor administratie | 1234 AB |
| Plaats | Voor administratie | Zandvoort |
| Object ID | Intern RyanRent nummer | OBJ-2024-042 |

#### **Verblijfsperiode** (beide data verplicht)

| Veld | Uitleg | Voorbeeld |
|------|--------|-----------|
| Incheck Datum * | Aankomstdatum gast | 01-07-2024 |
| Uitcheck Datum * | Vertrekdatum gast | 15-07-2024 |
| Aantal Dagen | **Automatisch berekend** | 14 |

💡 **Tip:** Excel berekent automatisch aantal dagen wanneer je beide data invult!

#### **Voorschotten** (alle verplicht)

| Veld | Uitleg | Voorbeeld |
|------|--------|-----------|
| Voorschot Borg * | Bedrag dat gast vooraf betaalde als borg | €800.00 |
| Voorschot GWE * | Bedrag voor gas/water/elektra vooraf betaald | €350.00 |
| Voorschot Schoonmaak * | Bedrag voor schoonmaak vooraf betaald | €250.00 |
| Overige Voorschotten | Extra kosten (bijv. toeristenbelasting) | €0.00 |

#### **Contractgegevens**

| Veld | Uitleg | Opties |
|------|--------|--------|
| Schoonmaak Pakket * | Welk pakket is afgesproken | **Dropdown:** 5_uur of 7_uur |
| Inbegrepen Uren | **Automatisch** (5 of 7 afhankelijk van pakket) | - |
| Uurtarief Schoonmaak * | Prijs per uur extra schoonmaak | €50.00 (standaard) |
| Meterbeheerder | Wie beheert de meters | Stedin |
| Energie Leverancier | Bij wie zit het contract | Vattenfall |
| Contractnummer | Contractnummer energieleverancier | 1234567890 |

#### **Interne RyanRent Gegevens** (optioneel)

Deze velden zijn voor **jullie interne administratie**:
- RR Klantnummer
- RR Folder Link (OneDrive link naar klantmap)
- RR Projectleider (wie beheert dit object)
- RR Inspecteur (wie deed de inspectie)
- RR Factuurnummer

#### **Berekende Velden** (⚠️ NIET INVULLEN)

Deze velden worden door **Python automatisch berekend**:
- Borg Gebruikt
- Borg Terug
- Restschade
- GWE Meer/Minder
- Totaal Eindafrekening

---

### 🟢 Tabblad 2: GWE_Detail

#### **Meterstanden**

| Veld | Uitleg | Voorbeeld |
|------|--------|-----------|
| Elektra (kWh) Begin * | Meterstand bij incheck | 10000 |
| Elektra (kWh) Eind * | Meterstand bij uitcheck | 11250 |
| Elektra (kWh) Verbruik | **Automatisch:** Eind - Begin | 1250 |
| Gas (m³) Begin * | Meterstand bij incheck | 5000.00 |
| Gas (m³) Eind * | Meterstand bij uitcheck | 5150.50 |
| Gas (m³) Verbruik | **Automatisch:** Eind - Begin | 150.50 |

💡 **Tip:** Maak foto's van de meters bij in- en uitcheck!

#### **Kostenregels - Verbruik omzetten naar Euro's**

Dit is waar je het **verbruik omzet in kosten** op basis van de tarieven van de energieleverancier.

**Voorbeeldregels** (grijs) zijn al ingevuld en linken automatisch naar:
- Meterstanden (KWh_verbruik, Gas_verbruik)
- Aantal dagen verblijf

**Hoe gebruik je de voorbeeldregels:**

1. **Pas de tarieven aan** naar de echte tarieven van de energieleverancier
2. **Voeg extra regels toe** als nodig (bijvoorbeeld servicekosten, waterverbruik)
3. **Verwijder grijze voorbeeldregels** als je klaar bent

**Voorbeeld invulling:**

| Omschrijving | Verbruik/Dagen | Tarief excl. BTW | Kosten excl. BTW |
|--------------|----------------|------------------|------------------|
| Elektra verbruik (zie meterstand) | 1250 | €0.30 | €375.00 |
| Gas verbruik (zie meterstand) | 150.50 | €1.20 | €180.60 |
| Vaste levering elektra per dag | 14 | €0.50 | €7.00 |
| Vaste levering gas per dag | 14 | €0.45 | €6.30 |
| Waterverbruik (geschat per dag) | 14 | €3.50 | €49.00 |
| **TOTAAL** | | | **€617.90** |

💡 **Tips:**
- De kolom "Kosten excl. BTW" berekent automatisch: Verbruik × Tarief
- Je kunt zelf regels toevoegen of verwijderen
- BTW (21%) wordt door Python berekend

#### **Totalen** (⚠️ Berekend door Python)

- Totaal excl. BTW
- BTW (21%)
- Totaal incl. BTW

---

### 🟠 Tabblad 3: Schoonmaak

| Veld | Uitleg | Voorbeeld |
|------|--------|-----------|
| Schoonmaak Pakket | **Komt van Algemeen tab** | 5_uur |
| Inbegrepen Uren | **Automatisch** (5 of 7) | 5 |
| Totaal Uren Gewerkt * | Hoeveel uren is er daadwerkelijk gewerkt? | 7.5 |
| Extra Uren | **Automatisch:** max(0, Gewerkt - Inbegrepen) | 2.5 |
| Uurtarief | **Komt van Algemeen tab** | €50.00 |
| Extra Schoonmaak Bedrag | **Automatisch:** Extra uren × Uurtarief | €125.00 |

💡 **Voorbeeld scenario:**
- Pakket: 5_uur (5 uur inbegrepen)
- Gewerkt: 7.5 uur
- Extra: 2.5 uur × €50 = €125 extra kosten

---

### 🔴 Tabblad 4: Schade

**Instructie:** Vul hier alle schadeposten in. Bedrag wordt automatisch berekend.

| Beschrijving | Aantal | Tarief excl. BTW | Bedrag excl. BTW |
|--------------|--------|------------------|------------------|
| Gebroken raam keuken | 1 | €150.00 | **€150.00** |
| Beschadigde vloerbedekking woonkamer | 3 | €45.00 | **€135.00** |
| Vervangen handdoeken (set) | 2 | €25.00 | **€50.00** |
| Schoonmaak verwijderen vlekken | 1 | €75.00 | **€75.00** |
| | | **TOTAAL** | **€410.00** |

**Kolom uitleg:**
- **Beschrijving:** Wat is er kapot/beschadigd?
- **Aantal:** Hoeveel stuks/eenheden?
- **Tarief excl. BTW:** Prijs per stuk (zonder BTW)
- **Bedrag excl. BTW:** **Automatisch berekend** (Aantal × Tarief)

💡 **Tips:**
- Wees specifiek in beschrijving (helpt bij eventuele discussies)
- Maak foto's van de schade
- Bedragen altijd **exclusief BTW** invullen (Python berekent 21% BTW)

#### **Totalen** (⚠️ Berekend door Python)

- Totaal Schade excl. BTW
- BTW (21%)
- Totaal Schade incl. BTW

---

## 🖨️ PDF's Genereren

### Stap 1: Sla Excel Op
- **Belangrijk:** Sla `input_template.xlsx` op met de ingevulde gegevens
- Of sla op als `eindafrekening_[gastnaam]_[datum].xlsx` om origineel te bewaren

### Stap 2: Open Terminal/Command Prompt
- **Mac:** Open Terminal
- **Windows:** Open Command Prompt

### Stap 3: Navigeer naar de Map
```bash
cd "/Users/.../Eindafrekening Generator"
```

### Stap 4: Run het Script
```bash
python3 generate.py
```

Of met eigen bestandsnaam:
```bash
python3 generate.py --input "eindafrekening_janssen_juli2024.xlsx"
```

### Stap 5: Check de Output
In de map `output/` vind je:
- `janssen_onepager_01-07-15-07.pdf` - Voor de klant
- `janssen_detail_01-07-15-07.pdf` - Voor jullie administratie
- `janssen_onepager_01-07-15-07.html` - Backup (als PDF faalt)
- `janssen_detail_01-07-15-07.html` - Backup (als PDF faalt)

---

## ❓ Veelgestelde Vragen

### **Q: Moet ik alle velden invullen?**
**A:** Alleen velden met een `*` zijn verplicht. Andere velden kun je leeg laten.

### **Q: Wat als ik geen schade heb?**
**A:** Laat het Schade tabblad gewoon leeg. Python zal automatisch €0 gebruiken.

### **Q: Waarom zie ik geen BTW in Excel?**
**A:** BTW wordt door Python berekend (21% standaard tarief). Je ziet het wel in de PDF.

### **Q: Kan ik eigen regels toevoegen bij GWE Kostenregels?**
**A:** Ja! Voeg gewoon nieuwe regels toe onder de voorbeelden. De kolom "Kosten" berekent automatisch.

### **Q: Wat als de meterstanden niet kloppen?**
**A:** Controleer of je Begin < Eind hebt ingevuld. Excel berekent automatisch het verschil.

### **Q: Kan ik de uurtarieven aanpassen?**
**A:** Ja, pas het veld "Uurtarief Schoonmaak" aan in het Algemeen tabblad.

### **Q: Hoe voeg ik extra voorschotten toe?**
**A:** Gebruik het veld "Overige Voorschotten" in het Algemeen tabblad.

### **Q: Waar vind ik de gegenereerde PDF's?**
**A:** In de map `output/` in dezelfde map als het Excel bestand.

---

## 🔧 Probleemoplossing

### ❌ **"File not found: input_template.xlsx"**
**Oplossing:**
- Zorg dat je in de juiste map zit
- Of geef het volledige pad op: `--input "/pad/naar/bestand.xlsx"`

### ❌ **"WeasyPrint failed, HTML fallback created"**
**Oplossing:**
- Dit is normaal op Mac
- Open de `.html` bestanden in de `output/` map
- Print deze naar PDF via browser (Cmd+P → Save as PDF)

### ❌ **"Invalid value in cell X"**
**Oplossing:**
- Controleer of numerieke velden echt getallen bevatten (geen tekst)
- Controleer of datumvelden echte data zijn (DD-MM-YYYY)

### ❌ **Bedragen kloppen niet**
**Oplossing:**
- Controleer of alle voorschotten correct zijn ingevuld
- Controleer of GWE kostenregels correct zijn
- Let op: BTW wordt door Python toegevoegd (niet in Excel zichtbaar)

### ❌ **Excel formules geven #REF! error**
**Oplossing:**
- Gebruik de originele `input_template.xlsx`
- Kopieer nooit/plak cellen zonder formules
- Als het blijft gebeuren, gebruik `build_excel_template.py` om nieuwe template te maken

### 📞 **Hulp Nodig?**
- Check de technische documentatie: `DEVELOPER.md`
- Bekijk de voorbeeldbestanden in de `samples/` map
- Contact de developer

---

## ✅ Checklist Eindafrekening

Gebruik deze checklist om zeker te zijn dat alles compleet is:

### **Algemeen Tabblad**
- [ ] Naam klant ingevuld
- [ ] Email ingevuld
- [ ] Object adres ingevuld
- [ ] Incheck datum ingevuld
- [ ] Uitcheck datum ingevuld
- [ ] Alle voorschotten ingevuld (Borg, GWE, Schoonmaak)
- [ ] Schoonmaak pakket gekozen (5_uur of 7_uur)

### **GWE_Detail Tabblad**
- [ ] Elektra begin meterstand
- [ ] Elektra eind meterstand
- [ ] Gas begin meterstand
- [ ] Gas eind meterstand
- [ ] Kostenregels ingevuld met juiste tarieven
- [ ] Extra regels toegevoegd indien nodig
- [ ] Grijze voorbeeldregels verwijderd (optioneel)

### **Schoonmaak Tabblad**
- [ ] Totaal uren gewerkt ingevuld

### **Schade Tabblad**
- [ ] Alle schadeposten ingevuld (of leeg als geen schade)
- [ ] Beschrijvingen zijn duidelijk
- [ ] Aantal en tarieven correct

### **Voor Verzenden**
- [ ] PDF's gegenereerd zonder errors
- [ ] OnePager PDF gecontroleerd
- [ ] Detail PDF gecontroleerd
- [ ] Bedragen controleren (Totaal Eindafrekening klopt)
- [ ] Excel bestand bewaard voor administratie

---

## 📊 Voorbeeld Workflow

**Scenario:** Familie Janssen verblijft 14 dagen in Zeezicht appartement.

1. **Open template** → `input_template.xlsx`
2. **Algemeen tab:**
   - Naam: Familie Janssen
   - Email: janssen@email.nl
   - Adres: Strandweg 42, Zandvoort
   - Data: 01-07-2024 tot 15-07-2024 (14 dagen automatisch)
   - Voorschotten: Borg €800, GWE €350, Schoonmaak €250
   - Pakket: 5_uur

3. **GWE_Detail tab:**
   - KWh: 10000 → 11250 (verbruik: 1250)
   - Gas: 5000 → 5150.50 (verbruik: 150.50)
   - Tarieven aanpassen naar Vattenfall tarieven

4. **Schoonmaak tab:**
   - Totaal uren gewerkt: 7.5 uur
   - Extra: 2.5 uur × €50 = €125

5. **Schade tab:**
   - Gebroken raam: 1 × €150 = €150
   - Beschadigde vloer: 3 × €45 = €135
   - Totaal: €285 (+ 21% BTW = €344.85)

6. **Sla op** als `eindafrekening_janssen_juli2024.xlsx`

7. **Genereer PDF:**
   ```bash
   python3 generate.py --input "eindafrekening_janssen_juli2024.xlsx"
   ```

8. **Check output:**
   - OnePager: Simpel overzicht voor Janssen
   - Detail: Volledige breakdown voor administratie

9. **Verstuur** OnePager naar janssen@email.nl

10. **Archiveer** Detail PDF + Excel in klantenmap

---

**Versie:** 2.0
**Laatste update:** November 2024
**Gemaakt voor:** RyanRent Team
