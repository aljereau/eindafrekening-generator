# RyanRent – Excel → Database Integratie (AI Context)

## Doel van dit document
Dit document beschrijft hoe bestaande operationele data (Excel) moet worden geïntegreerd in een bestaande SQL-database, zodat de nieuwe operationele workspace direct bruikbaar is.

De AI moet dit document gebruiken als **leidraad voor migratie, validatie en integratie**, niet als functionele UI-specificatie.

---

## Huidige situatie

### Wat bestaat al
- Er is een **bestaande SQL-database**
- Deze database bevat o.a. een **huizen/masterdata tabel**
- Elke woning heeft een **stabiele `huis_id`** die al in productie wordt gebruikt
- De AI kan:
  - SQLite databases lezen/schrijven
  - data structureren
  - views genereren
  - Excel en JSON output maken

### Wat nieuw is
- Een **nieuwe operationele datamodel** bestaande uit:
  - `woning_cycli` (lifecycle / status)
  - `woning_acties` (planning + uitvoering)
- Een **nieuwe Excel** met echte operationele data die:
  - inhoudelijk klopt
  - maar **tijdelijke / gegenereerde cyclus_id’s** bevat
- Deze Excel wordt gebruikt als **initiële dataload**

---

## Belangrijk uitgangspunt (zeer belangrijk)
❗ **De database is de bron van waarheid voor IDs.**

- `huis_id` uit Excel **is leidend** en moet matchen met de bestaande huizen tabel
- `cyclus_id` uit Excel **mag NIET worden overgenomen**
- Nieuwe `cyclus_id`’s worden **gegenereerd in de database**

---

## Conceptueel model (samenvatting)

- **Huis**  
  Bestaat al in DB (`huizen` tabel). Wordt niet aangepast.

- **Cyclus**  
  Eén actieve proces-cyclus per huis.
  Beschrijft:
  - status
  - bestemming
  - klanttype
  - context (datums)

- **Actie**  
  Feitelijke gebeurtenissen die bij een cyclus horen.
  Beschrijft:
  - planning
  - uitvoering
  - uren
  - sleutelstatus
  - inspectie-informatie

---

## Importstrategie (initial load)

### Kernregel
Voor elk `huis_id` dat in Excel voorkomt:
- maak **exact één actieve cyclus** aan in de database
- koppel **alle acties uit Excel** aan die cyclus

Dit is een **snapshot-import**, geen historisch reconstructiemodel.

---

## Aanbevolen aanpak (staging-first)

### Stap 1 — Maak staging tabellen
De AI moet eerst staging tabellen gebruiken:

- `stg_woning_cycli`
- `stg_woning_acties`

Excel data wordt **eerst hier geladen**, niet direct in productie-tabellen.

---

### Stap 2 — Laad Excel data in staging
Voor elke rij:

#### Cycli (stg_woning_cycli)
Overnemen:
- `huis_id`
- `status`
- `klant_type`
- `bestemming`
- `einddatum_huurder`
- `startdatum_nieuwe_huurder`
- `interne_opmerking`

Niet overnemen:
- `cyclus_id` (negeren / droppen)

---

#### Acties (stg_woning_acties)
Overnemen:
- `huis_id`
- `actie_type`
- `gepland_op`
- `uitgevoerd_op`
- `uitgevoerd_door`
- `verwachte_schoonmaak_uren`
- `werkelijke_schoonmaak_uren`
- `fotos_gemaakt`
- `issues_gevonden`
- `sleutels_bevestigd`
- `sleuteloverdracht_methode`
- `opmerking`

---

### Stap 3 — Validatie vóór insert
De AI moet vóór insert controleren:

- bestaat elke `huis_id` in de huizen tabel?
- zijn `status` waarden geldig (NL lifecycle lijst)?
- zijn `actie_type` waarden geldig?
- zijn uren numeriek en ≥ 0?
- zijn datumvelden valide ISO datums?

Rijen die falen:
- niet inserten
- rapporteren als “rejects” met reden

---

### Stap 4 — Insert naar echte tabellen

#### 4A) Insert cycli
Voor elke unieke `huis_id` in `stg_woning_cycli`:

- genereer een nieuwe `cyclus_id`
- insert in `woning_cycli` met:
  - `huis_id`
  - `is_actief = 1`
  - overige velden uit staging

Houd een mapping bij:

---

#### 4B) Insert acties
Voor elke rij in `stg_woning_acties`:

- lookup `cyclus_id` via mapping `huis_id → cyclus_id`
- insert in `woning_acties` met die `cyclus_id`

---

### Stap 5 — Post-import checks
Na import moet de AI:

- controleren dat er max 1 actieve cyclus per huis is
- een status-check uitvoeren (via `v_status_check`)
- rapporteren:
  - aantal cycli OK
  - aantal cycli met blokkades
  - meest voorkomende fouten

---

## Verwachte output voor de gebruiker

Na succesvolle import moet de gebruiker kunnen:

- direct een **operationeel dashboard** openen
- per woning zien:
  - status
  - acties
  - blokkades
- verder werken zonder dat handmatige correcties nodig zijn

---

## Wat de AI mag doen
- staging tabellen maken
- data valideren
- inserts uitvoeren
- rapportages genereren
- views gebruiken voor checks

## Wat de AI NIET mag doen
- bestaande huizen aanpassen
- bestaande productie-data overschrijven
- cyclus_id’s uit Excel hergebruiken
- aannames maken bij ontbrekende data zonder expliciete toestemming

---

## Succescriteria
Deze integratie is geslaagd als:
- alle woningen uit Excel zichtbaar zijn in het dashboard
- acties correct aan cycli hangen
- status-checks correct rood/groen tonen
- gebruikers direct kunnen doorwerken

---