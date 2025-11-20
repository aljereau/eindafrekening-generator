# **📘 RyanRent Eindafrekening System – Builder Implementation Guide**

### *Internal Documentation for AI Builder / Developer*

---

# **1. Doel van dit document**

Dit document legt uit:

* Wat er al bestaat in het eindafrekeningssysteem
* Wat er nog gebouwd moet worden
* Hoe de **developer mapping JSON** gebruikt moet worden
* Hoe Excel → Python → HTML → Eindafrekening samenwerkt
* Welke output het team uiteindelijk moet kunnen genereren (one-pager + detailview)

Het is bedoeld voor de **AI Builder of developer** die het systeem verder gaat implementeren en afronden.

---

# **2. Wat er al bestaat (baseline components)**

Het team heeft al:

### **2.1 Een werkende HTML front-end**

* Layout in de stijl die we gekozen hebben (cards, minimalistisch, horizontale bars)
* Het systeem kan HTML genereren vanuit Python

### **2.2 Een bestaande input Excel-file**

* Sheets bevatten een basisstructuur voor G/W/E, schoonmaak, schade en klantinfo
* Excel is gekoppeld aan Python
* Python leest de waarden al uit
* HTML wordt gegenereerd op basis van Python-output

### **2.3 Een Python script (generator.py)**

* Leest input.xlsx
* Produceert HTML
* Export naar PDF is al mogelijk

Dit is de **fundering**.

Nu moet het systeem compleet worden gemaakt zodat:

* medewerkers (Anna en team) **echt** met de input kunnen werken
* data volledig is
* output correct, consistent en professioneel is
* de eindafrekening duidelijk en klantvriendelijk is

---

# **3. Wat nog gebouwd moet worden**

Het werk nu bestaat uit:

### **3.1 Excel-template afronden**

* Velden structureren volgens de mapping JSON
* Named ranges aanmaken
* Velden berekenbaar maken (computed → Excel formules)
* Input velden gebruikersvriendelijk maken

  * Drop-downs
  * Validators
  * Verplichte velden
  * Automatische berekeningen (verbruik, extra uren, borg, totals)

### **3.2 Python generator uitbreiden**

* Mapping JSON gebruiken om data gestructureerd in te lezen
* Clean datamodel maken in Python (dicts/classes)
* Python moet **twee output JSON’s** genereren:

  * `onepager.json`
  * `detail.json`

### **3.3 HTML templates afmaken**

* One-pager HTML vullen met de variabelen uit `onepager.json`
* Detail HTML vullen met variabelen uit `detail.json`
* Styling consistent houden
* Bars dynamisch op basis van waarden (conceptueel of proportioneel)
* Tabelstructuren gebruiken voor G/W/E en schade

### **3.4 Einde: werkende end-to-end flow**

De medewerker moet:

1. `input.xlsx` openen
2. Velden invullen
3. `generator.py` draaien
4. Automatisch krijgen:

   * `onepager.html` → als PDF
   * `detail.html` → als PDF
   * gecombineerd pakket dat naar klant kan

Dat is het eindproduct.

---

# **4. Wat de Mapping JSON doet (heel belangrijk)**

De mapping JSON is de **centrale waarheid** van het systeem.
Het beschrijft:

* Alle velden die er bestaan
* Waar ze vandaan komen (Excel sheet + cell namen)
* Hoe ze heten in de output (onepager.json en detail.json)
* Welke data in welke HTML-sectie thuishoort
* Welke velden computed worden (door Excel of Python)

Zonder deze mapping zou het team elke keer moeten raden:

* Hoe heten velden?
* Waar staat welke waarde?
* Hoe vult Anna het systeem in?
* Wat verwacht de HTML template?

Met de mapping JSON wordt dit allemaal **één-op-één verbonden**:

```
Excel input → Python model → HTML templates → PDF output
```

Het is letterlijk de **datastructuur en handleiding** voor het gehele eindafrekeningssysteem.

Daarom krijgt de AI Builder hiermee:

* Volledige context
* Alle entiteiten (Client, Object, GWE, Schoonmaak, Schade, Borg)
* Alle variabelen
* De exacte namen
* De logische structuur
* Hoe het eindresultaat gevisualiseerd wordt

---

# **5. Stappen die de Builder moet uitvoeren**

## **Stap 1 – Excel Input Structuur klaarmaken**

Gebruik `excel-template.json`.

Acties:

* Sheets opbouwen: Algemeen, GWE_Detail, Schoonmaak, Schade
* Kolommen plaatsen volgens JSON
* Named ranges aanmaken
* Alle computed velden als Excel formules zetten
* Validatie toevoegen (dropdowns, nummering, verplichte velden)
* Een nette template maken voor Anna

## **Stap 2 – Python Model Bouwen**

Gebruik:

* `onepager.json`
* `detail.json`
* `entities.json`

Acties:

* Data inlezen vanuit Excel via named ranges
* Structureren in Python objecten
* Output JSON genereren (clean)
* Logging en foutafhandeling

## **Stap 3 – HTML Templates Bouwen**

Acties:

* Variabelen injecteren in:

  **One-pager template**
  voorbeelden:

  * `{{settlement.borg.terug}}`
  * `{{gwe.meer_minder}}`
  * `{{cleaning.extra_bedrag}}`

  **Detail template**

  * G/W/E regels dynamisch mappen
  * Schadetabel vullen
  * Schoonmaakblok vullen
  * Meterstanden tonen

* Bars dynamisch maken (prepaid / used / extra / refund)

## **Stap 4 – End-to-End testen**

Testcases:

* Schoonmaak zonder extra uren
* Schoonmaak met extra uren
* Schade lager dan borg
* Schade hoger dan borg
* G/W/E verbruik hoger dan voorschot
* G/W/E lager dan voorschot
* Meerdere schadeposten
* Combineerde scenario’s

Doel = stabiliteit + correctheid.

---

# **6. Output die het systeem moet leveren**

### **6.1 One-pager PDF**

Met:

* Borg
* G/W/E
* Schoonmaak
* Schade totaal
* Eindafrekening
* Bars
* Klantinfo & object info
* Visueel clean

### **6.2 Detail PDF**

Met:

* Meterstanden begin/eind
* G/W/E berekening (volledige Vattenfall/Stedin blokk)
* Schoonmaak pakket + extra uren
* Schadeposten uitgesplitst
* Totalen incl/excl btw

### **6.3 Logging / archief**

Optioneel:

* JSON input
* JSON output
* PDF dumps

---

# **7. Wanneer het systeem “DONE” is**

Het is af wanneer:

✔ Excel voldoet aan alle velden uit `excel-template.json`
✔ Python kan alle data mappen naar `onepager.json` en `detail.json`
✔ HTML templates gevuld worden met variabelen uit die JSON's
✔ De output PDF professioneel, compleet en foutloos is
✔ Anna en het team het *zonder uitleg* kunnen invullen
✔ Elke klant een duidelijke en eerlijke eindafrekening krijgt

Dat is het eindstation.

---

# **8. Conclusie**

De mapping JSON’s dienen als:

* handleiding
* datastructuur
* contract tussen Excel → Python → HTML
* en context voor AI Builder zodat hij niets hoeft te raden

Het enige wat nu nog moet gebeuren is:

**bouwen → testen → polish → live**


