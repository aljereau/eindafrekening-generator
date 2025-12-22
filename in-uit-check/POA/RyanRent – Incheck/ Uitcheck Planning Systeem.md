# RyanRent – Incheck / Uitcheck Planning Systeem

## Doel van dit document
Dit document beschrijft **het totale systeem** dat we bouwen voor RyanRent:

- van bestaande data (huizen + Excel)
- naar een gestructureerde database
- naar een operationele mini-app
- met AI-gedreven planning aanbevelingen

Het document dient als **single source of truth** voor:
- database ontwerp
- datamigratie
- applicatie-architectuur
- AI planning logica

---

## 1. Waar we nu staan (huidige situatie)

### Wat bestaat al
- Een **bestaande SQL database**
- Een **huizen tabel** (masterdata)
  - bevat `huis_id`
  - bevat adresgegevens
  - is leidend en stabiel
- Een **werkende chatbot**
  - kan SQLite lezen en schrijven
  - kan queries uitvoeren
  - kan views genereren
  - kan Excel/JSON exporteren

### Operationele realiteit
- Medewerkers werken nu met **Excel**
- Die Excel bevat:
  - incheck / uitcheck informatie
  - planning
  - schoonmaak
- De data is:
  - inhoudelijk correct
  - maar niet structureel afgedwongen
  - niet geschikt voor schaal of planning

---

## 2. Wat we bouwen (eindbeeld)

### Kernidee
We bouwen een **operationeel proces-systeem** waarin:

- elke woning door een **levenscyclus** gaat
- acties feitelijk worden vastgelegd
- status wordt bewaakt
- planning wordt ondersteund door AI

### Eindgebruikers
- operationeel medewerkers
- planners
- (later) management

### Belangrijk principe
> **De database is de bron van waarheid.**  
> Gebruikers werken via een app/interface, niet direct in SQL.

---

## 3. Conceptueel model

### 3.1 Huizen (bestaat al)
- `huizen`
- bevat alle woningen
- wordt niet aangepast door dit project

### 3.2 Woning cycli (nieuw)
Elke woning kan meerdere cycli hebben over tijd  
(maar maximaal 1 actieve tegelijk)

Een cyclus beschrijft:
- waar de woning zich bevindt in het proces
- voor wie / met welk doel
- tot wanneer iets moet gebeuren

### 3.3 Woning acties (nieuw)
Acties zijn **feiten**, geen status.

Voorbeelden:
- voorinspectie gepland
- uitcheck uitgevoerd
- schoonmaak gedaan
- incheck bevestigd

---

## 4. Lifecycle model (NL)

Een cyclus beweegt sequentieel door deze statussen:

- NIET_GESTART
- VOORINSPECTIE_GEPLAND
- VOORINSPECTIE_UITGEVOERD
- UITCHECK_GEPLAND
- UITCHECK_UITGEVOERD
- SCHOONMAAK_NODIG
- KLAAR_VOOR_INCHECK
- INCHECK_GEPLAND
- INCHECK_UITGEVOERD
- TERUG_NAAR_EIGENAAR
- AFGESLOTEN

❗ Status ≠ actie  
Status is een **samenvatting**, acties zijn de onderbouwing.

---

## 5. Database structuur (high level)

### Kern tabellen
- `huizen` (bestaat al)
- `woning_cycli`
- `woning_acties`

### Ondersteunend
- `teams`
- `team_beschikbaarheid` (optioneel)
- lookup tables (status, actie_type, etc.)

### Kernregels
- 1 actieve cyclus per huis
- acties horen altijd bij een cyclus
- status mag alleen vooruit, niet achteruit

---

## 6. Excel → Database migratie

### Doel
Bestaande Excel-data correct inladen als startpunt.

### Belangrijk
- `huis_id` uit Excel = leidend
- `cyclus_id` uit Excel = negeren
- nieuwe `cyclus_id` wordt gegenereerd in DB

### Strategie
1. Excel → staging tabellen
2. valideren
3. 1 cyclus per huis aanmaken
4. acties koppelen aan die cyclus
5. status-check uitvoeren

Na migratie moet alles **direct operationeel bruikbaar** zijn.

---

## 7. Mini-app (operationele workspace)

### Doel
Medewerkers kunnen:
- zien wat prioriteit heeft
- acties registreren
- status controleren
- planning volgen

### Kern schermen
1. **Werkvoorraad**
   - prioriteitenlijst
   - deadlines
   - blokkades
2. **Woningdetail**
   - status
   - tijdlijn van acties
   - status-check feedback
3. **Actie registreren**
   - context-afhankelijk formulier
4. **Planner**
   - uren
   - teams
   - deadlines

Gebruikers werken op **adresniveau**, systeem werkt op IDs.

---

## 8. Status-check systeem

Voor elke actieve cyclus:
- controleert of vereiste acties bestaan
- valideert of data compleet is
- bepaalt:
  - OK
  - WAARSCHUWING
  - BLOKKADE

Deze check voedt:
- dashboards
- planning
- AI aanbevelingen

---

## 9. AI Planning Recommendation Engine

### Doel
AI helpt bij:
- prioriteren
- plannen
- capaciteitsverdeling
- uitleggen waarom

### Wat AI wel doet
- aanbevelingen maken
- uitleg genereren
- alternatieven voorstellen

### Wat AI niet doet
- data aanpassen
- status wijzigen
- acties aanmaken

### Input
- status
- deadlines
- verwachte uren
- open acties
- teamcapaciteit

### Output
- “wat eerst”
- “welke actie”
- “welk team”
- “hoeveel uren”
- “waarom”

---

## 10. Feedback & leren
Na uitvoering:
- verwachte uren vs werkelijke uren
- afwijkingen opslaan
- later gebruiken voor betere inschatting

Geen automatische zelf-aanpassing zonder menselijke bevestiging.

---

## 11. Wat er nog gebouwd moet worden

### Database
- definitieve tabellen
- views:
  - status_check
  - planning_inputs
  - team_capacity

### Logica
- prioriteitsscore berekening
- status-overgang validatie

### Mini-app
- basis UI
- actie formulieren
- planning scherm

### AI layer
- planning explanation
- dag-/weekplanning voorstel
- conflict detectie

---

## 12. Succescriteria
Dit systeem is succesvol als:
- Excel niet meer nodig is
- medewerkers weten wat ze vandaag moeten doen
- planning voorspelbaar wordt
- data consistent blijft
- AI helpt zonder te overrulen

---

## 13. Scope grenzen
✔ Operationele ondersteuning  
✔ Planning aanbevelingen  
✔ Transparantie  

✖ Volledig autonome planning  
✖ Onzichtbare beslissingen  
✖ Black-box logica  

---