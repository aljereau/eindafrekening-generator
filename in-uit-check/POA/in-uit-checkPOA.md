# RyanRent – Operationele Planning Database

## Doel van dit document
Dit document beschrijft het doel, de scope en de ontwerpprincipes van de operationele database die we bouwen voor RyanRent.  
Deze database vormt de ruggengraat voor planning, statusoverzicht en prioritering van woningen in het uitcheck → incheck proces.

De database wordt gebruikt door:
- operationele medewerkers (dagelijks werk)
- planners (prioriteit & workload)
- een AI-chatbot die data kan lezen, bewerken en exporteren (SQLite-based)

---

## Hoofddoel van het systeem
Het systeem moet **operationele duidelijkheid** brengen in het woningproces door:

1. Het expliciet vastleggen van **waar een woning zich bevindt in het proces**
2. Het vastleggen van **wat er daadwerkelijk is gedaan**
3. Het zichtbaar maken van **verschillen tussen planning en realiteit**
4. Het ondersteunen van **planning op basis van tijd, prioriteit en capaciteit**

Het systeem is **geen ticket-systeem**, maar een **proces- en waarheidssysteem**.

---

## Kernconcepten (mentaal model)

### 1. Woning
Een fysieke woning (adres), afkomstig uit een bestaande huizen-database.
Deze data is **masterdata** en wordt niet handmatig aangepast in dit systeem.

### 2. Cyclus (Lifecycle)
Een **cyclus** is één doorloop van een woning door het proces:
- uitcheck
- eventuele schoonmaak / herstel
- incheck of overdracht

Een woning kan meerdere cycli hebben over tijd, maar **maximaal één actieve cyclus tegelijk**.

De cyclus beschrijft:
- de **intentie / status** (waar denken we dat de woning staat)
- context zoals klanttype, bestemming en relevante datums

### 3. Acties
Acties zijn **feitelijke gebeurtenissen**:
- voorinspectie
- uitcheck
- schoonmaak
- incheck
- overdracht aan eigenaar

Acties bevatten:
- planning (gepland_op)
- uitvoering (uitgevoerd_op)
- meetbare data (bijv. schoonmaakuren)

Acties zijn het **bewijs** dat een cyclusstatus klopt.

### 4. Dashboard / AI-laag
De AI en dashboards:
- vergelijken **cyclusstatus** met **acties**
- signaleren inconsistenties
- helpen bij planning, prioriteit en analyse
- wijzigen zelf geen data zonder expliciete instructie

---

## Ontwerpprincipes

### Cyclus is leidend, acties zijn bewijslast
- Een gebruiker **zet de status**
- Acties bepalen of die status valide is
- Het systeem controleert, maar beslist niet autonoom

### Status ≠ automatische berekening
Status is een **bewuste keuze**, geen afgeleide.
Dit voorkomt dat uitzonderingen en menselijke beslissingen het systeem breken.

### Planning op basis van uren, niet “gevoel”
Schoonmaak en werkbelasting worden gestuurd op:
- verwachte uren
- werkelijke uren

Dit maakt prioritering, capaciteitsplanning en verbetering mogelijk.

---

## Lifecycle status (Nederlands, vaste set)

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
- AFGEROND

---

## Verwachte workflow (happy flow, hoog niveau)

1. Woning wordt relevant → nieuwe cyclus aangemaakt
2. Cyclus krijgt status (bijv. VOORINSPECTIE_GEPLAND)
3. Bijbehorende actie wordt gepland
4. Actie wordt uitgevoerd en geregistreerd
5. Status schuift door (mits acties kloppen)
6. Verwachte vs werkelijke uren worden vastgelegd
7. Cyclus wordt afgerond

---

## Rol van de AI-chatbot

De chatbot kan:
- statusoverzichten maken (per woning, per fase)
- open acties en bottlenecks tonen
- prioriteiten voorstellen op basis van:
  - status
  - deadlines
  - verwachte uren
  - klanttype
- data toevoegen of aanpassen op expliciet verzoek
- exports genereren (Excel / JSON)

De chatbot:
- **interpreteert data**
- **doet voorstellen**
- **handelt niet autonoom**

---

## Einddoel (lange termijn)
Een stabiele operationele database die:
- realtime inzicht geeft in de woningportefeuille
- planning voorspelbaar maakt
- historisch leert van afwijkingen
- eenvoudig uitbreidbaar is naar:
  - web dashboards
  - automatische planning
  - AI-gestuurde optimalisatie

---

## Wat we nu bouwen (scope nu)
- SQLite database schema
- duidelijke relaties tussen woning, cyclus en acties
- geschikt voor menselijke invoer én AI-interpretatie
- gericht op operationeel gebruik, niet rapportage alleen