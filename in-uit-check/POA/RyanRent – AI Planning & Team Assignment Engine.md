# RyanRent – AI Planning & Team Assignment Engine

## Doel van dit document
Dit document beschrijft hoe een AI-gedreven **planning recommendation systeem** wordt opgebouwd bovenop de bestaande operationele database (huizen, cycli, acties).

Het systeem moet:
- prioriteiten bepalen
- voorstellen welke actie wanneer moet gebeuren
- rekening houden met teamtoewijzing en beschikbaarheid
- transparant uitleggen *waarom* iets wordt aanbevolen

De AI **stuurt aan**, maar **beslist niet autonoom**.

---

## Kernprincipe
> **Data bepaalt de volgorde, AI bepaalt de uitleg en optimalisatie.**

De database levert feiten en scores.  
De AI vertaalt dit naar begrijpelijke, operationele aanbevelingen.

---

## Overzicht architectuur

### Datalaag (bron van waarheid)
- `huizen`
- `woning_cycli`
- `woning_acties`
- `teams`
- `team_beschikbaarheid` (optioneel / later)

### Logica-laag
- SQL views (deterministisch)
- prioriteitsscores
- status-checks

### AI-laag
- planning recommendations
- uitleg (“waarom dit eerst”)
- dag- en weekplanning voorstellen
- alternatieven bij conflicten

---

## Inputdata voor planning (vereist)

Per **actieve cyclus** moet beschikbaar zijn:

### Vanuit `woning_cycli`
- `cyclus_id`
- `huis_id`
- `status`
- `klant_type`
- `bestemming`
- `startdatum_nieuwe_huurder`
- `is_actief`

### Vanuit `woning_acties`
- open acties (gepland, niet uitgevoerd)
- laatste UITCHECK:
  - `verwachte_schoonmaak_uren`
- laatste SCHOONMAAK:
  - `werkelijke_schoonmaak_uren`
- toegewezen team / persoon

### Afgeleid (views)
- status-check severity (OK / WARN / ERROR)
- volgende vereiste actie
- deadline druk (dagen tot startdatum)

---

## Kernview: `v_planning_inputs`
Deze view is de **basis voor alle aanbevelingen**.

Per actieve cyclus:
- `adres`
- `status`
- `volgende_actie`
- `deadline_dagen`
- `verwachte_uren`
- `open_acties_count`
- `status_severity`
- `klant_type`
- `bestemming`
- `laatst_toegewezen_team`

Geen AI-logica hier. Alleen feiten.

---

## Prioriteitsscore (deterministisch)

De AI mag **nooit zelf prioriteit verzinnen**.  
Die komt uit een vaste formule.

### Voorbeeld gewichten
- Deadline druk: 40%
- Status blokkade: 25%
- Verwachte uren (effort): 15%
- Klanttype impact: 10%
- Bestemming: 10%

### Output
- `priority_score` (0–100)
- `priority_band`:
  - CRITICAL
  - HIGH
  - NORMAL
  - LOW

---

## Team & beschikbaarheid model

### Team tabel
- `team_id`
- `team_naam`
- `team_type` (INTERN / SCHOONMAAK / CONTRACTOR)
- `standaard_capaciteit_uren_per_dag`

### Beschikbaarheid (optioneel)
- `team_id`
- `datum`
- `beschikbare_uren`
- `ingepland_uren`

### Actie toewijzing
Elke actie kan hebben:
- `assigned_team`
- `assigned_person` (optioneel)

---

## Wat de planning engine doet

### Stap 1 — Selectie
- Pak alle actieve cycli
- Filter op:
  - open acties
  - status != GESLOTEN

### Stap 2 — Scoring
- Bereken `priority_score`
- Sorteer aflopend

### Stap 3 — Capaciteitscheck
Per team:
- beschikbare uren vandaag / morgen
- reeds geplande acties

### Stap 4 — Recommendation
Voor elke top-priority cyclus:
- **welke actie**
- **welk team**
- **welke dag**
- **hoeveel uren reserveren**

---

## AI verantwoordelijkheden (belangrijk)

De AI mag:
- uitleggen waarom iets prioriteit heeft
- voorstellen doen
- conflicten signaleren
- alternatieve volgordes tonen

De AI mag NIET:
- status wijzigen
- acties aanmaken
- uren aanpassen
- data verzinnen

Alle mutaties vereisen expliciete user-actie.

---

## Output formaat (planning recommendation)

```json
{
  "adres": "Akkerweg 12",
  "huidige_status": "SCHOONMAAK_NODIG",
  "aanbevolen_actie": "SCHOONMAAK_PLANNEN",
  "aanbevolen_team": "Intern Team A",
  "aanbevolen_datum": "2025-01-03",
  "verwachte_uren": 3.5,
  "prioriteit": "HIGH",
  "uitleg": [
    "Nieuwe huurder start over 2 dagen",
    "Schoonmaak is vereist na uitcheck",
    "Intern team heeft vandaag nog 4 uur capaciteit"
  ]
}