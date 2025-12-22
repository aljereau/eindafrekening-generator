# RyanRent Inspectie Workflow - Complete Uitleg

## 📋 Inhoudsopgave

1. [Overzicht van het Proces](#overzicht-van-het-proces)
2. [De Twee Scenario's](#de-twee-scenarios)
3. [Inspectie Types Uitgelegd](#inspectie-types-uitgelegd)
4. [Complete Workflow Stap-voor-Stap](#complete-workflow-stap-voor-stap)
5. [Financiële Flow](#financiele-flow)
6. [Foto Documentatie](#foto-documentatie)
7. [Schade Afhandeling](#schade-afhandeling)
8. [Prioriteiten Systeem](#prioriteiten-systeem)
9. [Systeem Verbeteringen](#systeem-verbeteringen)

---

## Overzicht van het Proces

### Het Grote Plaatje

RyanRent beheert verhuurpanden. Wanneer een huurder vertrekt (uitcheck) en er een nieuwe huurder intrekt (incheck), doorloopt het pand een reeks inspecties om:

1. **De staat van het pand vast te leggen**
2. **Kosten eerlijk te verdelen** (wie betaalt voor schade/vervuiling?)
3. **Het pand klaar te maken** voor de volgende huurder
4. **Financiële eindafrekeningen te maken**

### De Kern van de Operatie

```
VERTREKKENDE HUURDER
        ↓
   [INSPECTIES]
        ↓
   [SCHOONMAAK + HERSTEL]
        ↓
   NIEUWE HUURDER
```

---

## De Twee Scenario's

### ⚡ SCENARIO A: Nieuwe Klant Staat Al Klaar (HOGE PRIORITEIT)

**Kenmerken:**
- Nieuwe huurder is al bekend
- Intrek datum is al gepland
- Tijd is kritisch - huis moet OP TIJD klaar zijn
- Volledige inspectie cyclus nodig

**Waarom hoge prioriteit?**
- Contract met nieuwe huurder staat
- Kan niet uitgesteld worden
- Revenue loopt als huis niet op tijd klaar is
- Nieuwe huurder verwacht leefbare staat

### 🕐 SCENARIO B: Geen Nieuwe Klant Gepland (LAGERE PRIORITEIT)

**Kenmerken:**
- Huis gaat terug naar eigenaar
- OF: Huis wacht op toekomstige huurder (nog niet bekend)
- Minder tijdsdruk
- Kan flexibeler gepland worden

**Waarom lagere prioriteit?**
- Geen directe deadline
- Eigenaar neemt verantwoordelijkheid over
- Werk kan gespreid worden
- Minder financiële urgentie

---

## Inspectie Types Uitgelegd

### 1️⃣ **INCHECK INSPECTIE** (Start van Huurperiode)

**Wanneer:** Bij intrek van een huurder  
**Doel:** Vastleggen van de beginstaat van het pand  
**Wie is erbij:** RR inspecteur + nieuwe huurder  

**Wat gebeurt er:**
- Foto's van ALLES in het pand
- Staat van muren, vloeren, apparatuur, etc.
- Eventuele bestaande schade documenteren
- Huurder tekent rapport

**Belangrijk:** Deze staat is het REFERENTIEPUNT. Bij uitcheck wordt hiermee vergeleken!

**In het systeem:**
- Wordt getrackt in **Inchecks** tab
- Datum vastgelegd
- Foto's opgeslagen
- VIS referentie (als gebruikt)

---

### 2️⃣ **PRE-INSPECTIE / VOOR-OPLEVERING** (Vóór Uitcheck)

**Wanneer:** ~1-2 weken VOOR de geplande uitcheck  
**Doel:** Huurder een kans geven om schade/vervuiling te herstellen  
**Wie is erbij:** RR inspecteur (huurder kan aanwezig zijn)  

**Wat gebeurt er:**
1. Inspecteur komt langs
2. Maakt foto's van huidige staat
3. Vergelijkt met incheck foto's
4. Maakt rapport: "Dit moet nog opgelost worden"
5. Huurder krijgt het rapport

**Keuze voor de huurder:**

**Optie A: Zelf Oplossen** (Gratis)
- Huurder krijgt tijd om zelf op te lossen
- Voor uitcheck datum alles klaar hebben
- Geen extra kosten

**Optie B: RyanRent Laat Oplossen** (Betaald)
- Huurder kiest: "Jullie doen het maar"
- RR rekent schoonmaak/herstel kosten
- Komt op eindafrekening

**In het systeem:**
- Kolom: `Pre_Inspectie_Datum`
- Kolom: `Schoonmaak_Vereist` → "RR Schoonmaak" of "Eigenaar Schoonmaak"
- Foto's: Pre-inspectie foto's opslaan

---

### 3️⃣ **UITCHECK INSPECTIE / EIND INSPECTIE** (Bij Vertrek)

**Wanneer:** Op de dag dat de huurder het pand verlaat  
**Doel:** Definitief vaststellen wat er moet gebeuren + financiën afrekenen  
**Wie is erbij:** RR inspecteur + eventueel huurder  

**Wat gebeurt er:**
1. Inspecteur komt langs
2. Maakt foto's van huidige staat
3. Vergelijkt met:
   - Incheck foto's (beginstaat)
   - Pre-inspectie foto's (wat was afgesproken)
4. Sleutels innemen
5. Rapport maken

**Verschil Analyse:**
```
INCHECK STAAT (begin)
    ↓
    [Huurperiode]
    ↓
PRE-INSPECTIE (waarschuwing)
    ↓
    [Huurder had kans om op te lossen]
    ↓
UITCHECK STAAT (eind)

VERSCHIL = WAT HUURDER MOET BETALEN
```

**Bijvoorbeeld:**
- **Incheck:** Muur was wit en schoon
- **Pre-inspectie:** Muur heeft vlekken → rapport gestuurd
- **Uitcheck:** Muur nog steeds vies
- **Resultaat:** Huurder betaalt voor herschilderen

**Eindafrekening:**
- Schade die niet hersteld is
- Vervuiling die niet schoongemaakt is
- Ontbrekende items
- Schoonmaak kosten (als gekozen bij pre-inspectie)

**In het systeem:**
- Kolom: `Werkelijke_Datum` (wanneer uitcheck was)
- Kolom: `Sleutels_Ontvangen` → Ja/Nee
- Kolom: `Schade_Gemeld` → Ja/Nee
- Kolom: `Afrekening_Status` → tracking van financiën
- Kolom: `Opmerkingen` → details over schade/kosten

---

### 4️⃣ **SCHOONMAAK & HERSTEL FASE** (Na Uitcheck, Voor VIS)

**Wanneer:** Direct na uitcheck, voor nieuwe huurder komt kijken  
**Doel:** Pand leefbaar maken voor de volgende huurder  
**Wie doet het:** RyanRent (of externe partij)  

**Wat gebeurt er:**
1. **Schoonmaak uitvoeren**
   - Indien gekozen bij pre-inspectie: RR krijgt betaald door vertrekkende huurder
   - Indien niet gedekt: RR betaalt zelf of eigenaar

2. **Schade Herstellen**
   - **Gedekt door eindafrekening:** Huurder betaalt via eindafrekening
   - **Niet gedekt:** RR betaalt of eigenaar
   - **Ontdekt later:** Gaat naar eigenaar of RR neemt op zich

3. **Prioriteit:**
   - **Kritisch (nieuwe huurder wacht):** Alles wat leefbaarheid beïnvloedt MOET klaar
   - **Nice-to-have:** Kan na incheck nieuwe huurder nog gedaan worden

**Voorbeeld Scenario:**

```
Situatie: Nieuwe huurder trekt in over 5 dagen

KRITISCH (NU doen):
✅ Schoonmaak hele huis
✅ Kapotte keukenla repareren
✅ Lekkende kraan fixen
✅ Gaten in muur vullen + schilderen

NIET KRITISCH (kan later):
❌ Schilderwerk bijwerken in berging
❌ Tuinonderhoud (huis is leefbaar)
❌ Kleine cosmetische issues
```

**In het systeem:**
- Kolom: `Schoonmaak_Vereist` → wie doet schoonmaak?
- Kolom: `Meubilair_Verwijderen` → als RR meubels moet meenemen
- Kolom: `Schade_Gemeld` → wat is er kapot?
- Kolom: `Opmerkingen` → details van herstelwerk
- **Voorstel:** Extra kolom `Schade_Kosten` en `Schade_Gedekt_Door`

---

### 5️⃣ **VIS (VOOR-INCHECK INSPECTIE)** (Nieuwe Huurder Kijkt)

**Wanneer:** Vóór de nieuwe huurder intrekt, maar NA schoonmaak/herstel  
**Doel:** Nieuwe huurder laten zien: "Dit wordt jouw pand"  
**Wie is erbij:** RR inspecteur + nieuwe huurder  

**Wat gebeurt er:**
1. Nieuwe huurder komt kijken
2. Pand moet leefbaar zijn (niet perfect!)
3. Foto's maken van de staat
4. Eventuele issues bespreken:
   - "Dit wordt nog opgelost voor je intrekt"
   - "Dit kun je zelf doen als je wil"
5. Huurder akkoord → gaat door met incheck

**Belangrijk:**
- Huis hoeft niet 100% perfect
- Moet wel leefbaar en veilig zijn
- Kleine resterende issues kunnen later
- Dit is de basis voor de nieuwe INCHECK foto's

**In het systeem:**
- **MIST NU:** `VIS_Datum` kolom
- Staat nu in `VIS_Referentie` kolom (Inchecks tab)
- **Voorstel:** Los VIS veld in Uitchecks tab voor betere tracking

---

### 6️⃣ **INCHECK (Nieuwe Huurder Trekt In)**

**Wanneer:** Op de dag dat nieuwe huurder intrekt  
**Doel:** Nieuwe cyclus starten met schone lei  
**Wie is erbij:** RR inspecteur + nieuwe huurder  

**Wat gebeurt er:**
1. Finale foto's van de staat maken
2. Dit is de nieuwe REFERENTIE staat
3. Sleutels overhandigen
4. Contract afronden
5. Huurder tekent incheck rapport

**Deze foto's worden gebruikt bij:**
- Volgende pre-inspectie (over X maanden/jaren)
- Volgende uitcheck
- Volgende eindafrekening

**Cycle herhaalt zich!** 🔄

**In het systeem:**
- Getrackt in **Inchecks** tab
- Gekoppeld aan oude uitcheck via `Gekoppelde_Uitcheck_ID`
- Nieuwe referentie punt begint

---

## Complete Workflow Stap-voor-Stap

### 🔄 VOLLEDIGE CYCLUS (Nieuwe Klant Wacht)

```
┌─────────────────────────────────────────────────────────────────────┐
│ STAP 1: HUURDER MELDT VERTREK                                       │
└─────────────────────────────────────────────────────────────────────┘
   ↓
   • Huurder zegt: "Ik ga weg op 15 december"
   • Klant (verhuurder) meldt dit aan RyanRent
   • Check: Is er al nieuwe huurder? JA → HOGE PRIORITEIT
   
   IN SYSTEEM:
   ✓ Nieuwe rij in Uitchecks tab
   ✓ Adres invullen
   ✓ Klant selecteren
   ✓ Geplande_Datum: 15-12-2025
   ✓ Status: "Gepland"
   ✓ Prioriteit: HOOG (nieuwe huurder wacht)

┌─────────────────────────────────────────────────────────────────────┐
│ STAP 2: PRE-INSPECTIE PLANNEN (1-2 weken voor uitcheck)            │
└─────────────────────────────────────────────────────────────────────┘
   ↓
   • Plan pre-inspectie: 5 december (10 dagen voor uitcheck)
   • Wijs inspecteur toe: Ana
   
   IN SYSTEEM:
   ✓ Pre_Inspectie_Datum: 05-12-2025
   ✓ Inspecteur: Ana

┌─────────────────────────────────────────────────────────────────────┐
│ STAP 3: PRE-INSPECTIE UITVOEREN                                     │
└─────────────────────────────────────────────────────────────────────┘
   ↓
   • Ana gaat naar het pand
   • Maakt foto's van huidige staat
   • Vergelijkt met incheck foto's
   • Ziet: Keuken vies, gat in muur, tuin verwaarloosd
   • Maakt rapport voor huurder
   
   RAPPORT NAAR HUURDER:
   "Voordat u vertrekt moet het volgende opgelost:
    - Keuken grondig schoonmaken
    - Gat in muur woonkamer herstellen
    - Tuin opruimen
    
    U kunt dit zelf doen (gratis)
    OF wij doen het (kosten: geschat €450)"
   
   HUURDER KIEST: "Jullie doen het maar, ik heb geen tijd"
   
   IN SYSTEEM:
   ✓ Pre_Inspectie_Datum voltooid
   ✓ Schoonmaak_Vereist: "RR Schoonmaak"
   ✓ Opmerkingen: "Keuken vies, gat in muur, tuin verwaarloosd. 
                   Huurder kiest voor RR schoonmaak. Geschat €450"

┌─────────────────────────────────────────────────────────────────────┐
│ STAP 4: UITCHECK INSPECTIE (Vertrek Dag)                           │
└─────────────────────────────────────────────────────────────────────┘
   ↓
   • 15 december: Ana gaat naar het pand
   • Huurder is er (of niet, maakt niet uit)
   • Ana checkt alles opnieuw
   
   BEVINDINGEN:
   ✓ Keuken: Nog steeds vies (huurder heeft niks gedaan)
   ✓ Gat in muur: Nog steeds niet gerepareerd
   ✓ Tuin: Een beetje opgeruimd maar niet genoeg
   ✓ EXTRA: Kapotte keukenkastdeur ontdekt (was niet bij pre-inspectie)
   
   • Sleutels innemen van huurder
   • Foto's maken van alles
   
   EINDAFREKENING BEREKENEN:
   - Schoonmaak keuken: €200 (zoals geschat)
   - Tuin opruimen: €100
   - Gat in muur herstellen: €150
   - Keukenkastdeur vervangen: €150 (nieuwe schade!)
   TOTAAL: €600 → wordt ingehouden van borg/gefactureerd
   
   IN SYSTEEM:
   ✓ Werkelijke_Datum: 15-12-2025
   ✓ Tijd: 14:00
   ✓ Sleutels_Ontvangen: Ja
   ✓ Schade_Gemeld: Ja
   ✓ Status: "Bezig" (want nu moet schoonmaak/herstel)
   ✓ Afrekening_Status: "In Afwachting"
   ✓ Opmerkingen: "Eindafrekening €600. Keuken nog vies, gat in muur,
                   tuin half gedaan, keukenkast kapot. Nieuwe huurder 
                   trekt in op 22-12!"

┌─────────────────────────────────────────────────────────────────────┐
│ STAP 5: SCHOONMAAK & HERSTEL (16-20 december)                      │
└─────────────────────────────────────────────────────────────────────┘
   ↓
   DEADLINE: Nieuwe huurder komt VIS doen op 20 december!
   
   PRIORITEIT WERK (16-19 december):
   ✅ KRITISCH (MOET voor VIS):
      • Keuken volledig schoonmaken → 16 dec
      • Gat in muur vullen + schilderen → 17 dec (droogtijd!)
      • Keukenkast repareren/vervangen → 18 dec
      • Hele huis schoonmaken → 19 dec
      • Tuin netjes maken → 19 dec
   
   ⏰ KAN LATER (na VIS/incheck):
      • Schilderwerk bijwerken (kleine plekjes)
      • Berging opruimen
   
   IN SYSTEEM:
   ✓ Schoonmaak_Vereist: "RR Schoonmaak" (bevestigd)
   ✓ Status: "Bezig"
   ✓ Opmerkingen bijwerken: "Schoonmaak gepland 16-19 dec.
                              Klaar voor VIS op 20 dec."

┌─────────────────────────────────────────────────────────────────────┐
│ STAP 6: VIS - VOOR-INCHECK INSPECTIE (20 december)                 │
└─────────────────────────────────────────────────────────────────────┘
   ↓
   • Nieuwe huurder komt kijken met Ana
   • Pand is schoon en leefbaar
   • Foto's maken van huidige staat
   
   NIEUWE HUURDER ZIET:
   ✓ Keuken: Schoon! ✨
   ✓ Muur: Gerepareerd, nog een paar kleine plekjes maar prima
   ✓ Keukenkast: Nieuw!
   ✓ Tuin: Netjes
   
   Ana: "Die kleine plekjes op de muur worden nog even bijgewerkt, 
         maar het huis is klaar om in te trekken."
   
   Nieuwe huurder: "Perfect! Ziet er goed uit!"
   
   • Nieuwe huurder akkoord
   • Deze foto's worden basis voor nieuwe INCHECK
   
   IN SYSTEEM (Uitchecks):
   ✓ Status nog "Bezig" (want incheck moet nog)
   ✓ Opmerkingen: "VIS gedaan 20 dec. Nieuwe huurder akkoord.
                   Incheck gepland 22 dec."
   
   IN SYSTEEM (Inchecks tab - nieuwe rij):
   ✓ Incheck_ID: IC-2025-042
   ✓ Adres: [zelfde adres]
   ✓ Gekoppelde_Uitcheck_ID: UC-2025-038
   ✓ Nieuwe_Huurder_Naam: "Jan Pieters"
   ✓ Nieuwe_Huurder_Bedrijf: "Bouwman B.V."
   ✓ Intrek_Datum: 22-12-2025
   ✓ VIS_Referentie: "VIS gedaan 20-12, akkoord"
   ✓ Status: "Gepland"
   ✓ Inspecteur: Ana

┌─────────────────────────────────────────────────────────────────────┐
│ STAP 7: INCHECK - NIEUWE HUURDER TREKT IN (22 december)            │
└─────────────────────────────────────────────────────────────────────┘
   ↓
   • 22 december: Nieuwe huurder Jan Pieters trekt in
   • Ana is erbij voor officiële incheck
   • Finale foto's maken (dit is de NIEUWE referentie!)
   • Contract ondertekenen
   • Sleutels overhandigen
   
   IN SYSTEEM (Inchecks):
   ✓ Incheck_Voltooid: Ja
   ✓ Status: "Voltooid"
   ✓ Opmerkingen: "Incheck succesvol. Sleutels overhandigd.
                   Kleine schilderwerkjes worden nog gedaan."
   
   IN SYSTEEM (Uitchecks - oude rij afsluiten):
   ✓ Status: "Voltooid"
   ✓ Afrekening_Status: "Voltooid"
   ✓ Opmerkingen toevoegen: "Nieuwe huurder ingetrokken 22 dec.
                             Resterende werkzaamheden gepland."

┌─────────────────────────────────────────────────────────────────────┐
│ STAP 8: POST-INCHECK WERKZAAMHEDEN (23-24 december)                │
└─────────────────────────────────────────────────────────────────────┘
   ↓
   • Kleine schilderwerkjes bijwerken
   • Berging opruimen
   • Nieuwe huurder is er al, geen probleem
   
   CYCLUS COMPLEET! 🎉
   
   VOLGENDE CYCLUS:
   → Over X maanden/jaren meldt Jan Pieters dat hij vertrekt
   → Dan herhalen we dit hele proces
   → VIS foto's van NU worden dan de INCHECK referentie
```

---

## Financiële Flow

### 💰 Wie Betaalt Wat?

#### 1. **Schoonmaak Kosten**

**Scenario A: Huurder Kiest Zelf Schoonmaken** (Pre-inspectie)
```
Pre-inspectie → Huurder krijgt rapport
              → Huurder: "Ik doe het zelf"
              → Uitcheck: Als het schoon is → GEEN KOSTEN
              → Uitcheck: Als het NIET schoon is → WEL KOSTEN (op eindafrekening)
```

**Scenario B: Huurder Kiest RR Schoonmaak** (Pre-inspectie)
```
Pre-inspectie → Huurder krijgt rapport
              → Huurder: "Jullie doen het maar"
              → RR doet schoonmaak
              → Kosten gaan naar eindafrekening huurder
              → RR krijgt betaald voor schoonmaak
```

**Scenario C: Huurder Doet Niks, Kiest Niks**
```
Pre-inspectie → Huurder krijgt rapport
              → Huurder: [ignoreert]
              → Uitcheck: Nog steeds vies
              → RR moet het toch schoonmaken
              → Kosten gaan naar eindafrekening huurder
```

#### 2. **Schade Herstel Kosten**

**Gedekt door Eindafrekening** (Normaal Scenario)
```
Schade veroorzaakt door huurder
  ↓
Verschil tussen incheck ↔ uitcheck
  ↓
Huurder betaalt via eindafrekening
  ↓
RR gebruikt dat geld om te repareren
```

**Voorbeeld:**
- Incheck: Muur wit
- Uitcheck: Gat in muur
- Herstel kost: €150
- Huurder betaalt: €150 (via eindafrekening)
- RR repareert met dat geld

**NIET Gedekt door Eindafrekening** (Problemen)

**Situatie 1: Schade Ontdekt NA Incheck Nieuwe Huurder**
```
Nieuwe huurder al ingetrokken
  ↓
Ontdekken schade die niet eerder gezien was
  ↓
Kan niet meer op oude huurder verhalen
  ↓
OPTIES:
  A) RR neemt kosten zelf (operationele kost)
  B) Melden aan eigenaar → eigenaar betaalt
  C) Afschrijven als verlies
```

**Voorbeeld:**
- Uitcheck gedaan, leek alles oké
- Nieuwe huurder intrekt
- Week later: Lekkage in plafond ontdekt (verborgen schade)
- Oude huurder is al weg, kan niet bewijzen dat het hun schuld was
- RR lost op met eigenaar of neemt zelf

**Situatie 2: Normale Slijtage / Oude Schade**
```
Schade was er al voor deze huurder
  ↓
Niet eerlijk om huidige huurder te laten betalen
  ↓
Eigenaar betaalt OF RR neemt op zich
```

**Voorbeeld:**
- Incheck foto's tonen al een scheur in de muur
- Bij uitcheck is scheur nog steeds daar (niet erger)
- Huurder hoeft niet te betalen
- Als het gerepareerd moet worden → eigenaar/RR betaalt

#### 3. **Situatie: Huis Niet 100% Klaar Bij VIS**

**Wat is Acceptabel?**
```
KRITISCH (MOET klaar):
✓ Schoon
✓ Veilig
✓ Functioneel
✓ Leefbaar

NIET KRITISCH (mag later):
✗ Perfecte staat
✗ Cosmetische issues
✗ Kleine verbeteringen
```

**Financieel:**
- Kritisch werk: Wordt gedaan VOOR VIS
  - Kosten: Gedekt door eindafrekening oude huurder OF RR
- Niet-kritisch werk: Kan NA incheck
  - Kosten: Zoals afgesproken (eindafrekening/RR/eigenaar)

**Voorbeeld:**
```
VIS Dag:
✓ Huis is schoon → Klaar
✓ Keuken werkt → Klaar
✓ Geen lekkages → Klaar
✗ Kleine verfvlekje op plint → KAN LATER
✗ Tuinonderhoud perfect → KAN LATER

Nieuwe huurder trekt in → Kleine dingen worden nog gedaan
```

---

## Foto Documentatie

### 📸 Waarom Foto's Cruciaal Zijn

**Juridische Bewijsvoering:**
- Bij dispuut met huurder over eindafrekening
- "U zegt dat het schoon was, maar foto's tonen anders"
- Bewijslast bij RR: goede foto's = sterk bewijs

**Operationele Tracking:**
- Wat moet er precies gedaan worden?
- Is het werk goed uitgevoerd?
- Verschil tussen voor/na zichtbaar maken

**Klant Communicatie:**
- Eigenaar/klant kan zien wat er gebeurt
- Transparantie over uitgevoerd werk
- Verantwoording van kosten

### 📸 Foto Momenten

| Moment | Doel | Wat Fotograferen | Wie Gebruikt Het |
|--------|------|------------------|------------------|
| **Incheck** | Referentie beginstaat | Alles in het pand | Bij volgende uitcheck (jaren later) |
| **Pre-Inspectie** | Waarschuwen huurder | Probleemgebieden | Huurder (in rapport), RR (bewijs) |
| **Uitcheck** | Eindafrekening onderbouwen | Alles + probleemgebieden | Financiën, juridisch |
| **Na Schoonmaak/Herstel** | Bewijs werk gedaan | Opgeloste gebieden | Eigenaar (verantwoording) |
| **VIS** | Nieuwe huurder tonen | Alles in huidige staat | Nieuwe huurder (akkoord) |
| **Incheck (nieuwe cyclus)** | Nieuwe referentie | Alles in het pand | Bij volgende uitcheck (start nieuwe cyclus) |

### 📸 Wat Moet Je Fotograferen?

**Bij ELKE Inspectie:**
- Alle kamers (overzicht)
- Alle muren (vlekken, gaten, schade)
- Alle vloeren (krassen, vlekken)
- Keuken (apparatuur, kasten, aanrecht)
- Badkamer (toilet, douche, tegels)
- Ramen en kozijnen
- Deuren
- Plafonds (vlekken, scheuren)
- Tuin/balkon (als van toepassing)

**Extra bij Probleemgebieden:**
- Close-up van schade
- Meerdere hoeken
- Met iets voor schaal (meetlat, hand)
- Voor/na vergelijking

### 📸 In Het Systeem (Voorstel)

**Huidige Situatie:**
- Foto's worden gemaakt maar niet centraal getrackt in het systeem
- Foto's zitten waarschijnlijk in aparte mappen/systemen

**Voorstel voor Verbetering:**
Kolommen toevoegen:
- `Pre_Inspectie_Fotos` → Link naar map/album
- `Uitcheck_Fotos` → Link naar map/album
- `Schoonmaak_Fotos` → Link naar map/album (voor/na)
- `VIS_Fotos` → Link naar map/album
- `Incheck_Fotos` → Link naar map/album

OF gebruik een foto management systeem en link via:
- `Foto_Album_ID` → Centraal systeem

---

## Schade Afhandeling

### 🔧 Types Schade

#### 1. **Gebruikersschade** (Huurder Verantwoordelijk)

**Voorbeelden:**
- Gaten in muren (van spijkers, meubels)
- Vlekken op muren/vloeren
- Kapotte apparatuur (door verkeerd gebruik)
- Beschadigde deuren/kasten
- Tuin verwaarloosd

**Wie Betaalt:** Huurder (via eindafrekening)

**Proces:**
1. Documenteren bij uitcheck
2. Kosten schatten/offerte vragen
3. Eindafrekening sturen naar huurder
4. Geld ontvangen
5. Herstel uitvoeren met dat budget

#### 2. **Normale Slijtage** (Eigenaar Verantwoordelijk)

**Voorbeelden:**
- Verf die verkleurt over jaren
- Vloer die slijt door normaal gebruik
- Apparatuur die stuk gaat door ouderdom
- Kleine krassen van normaal wonen

**Wie Betaalt:** Eigenaar of RR (afhankelijk van contract)

**Proces:**
1. Documenteren bij uitcheck
2. Bepalen: "Dit is normale slijtage, niet huurder schuld"
3. Overleggen met eigenaar
4. Eigenaar betaalt OF RR neemt op zich

#### 3. **Verborgen Schade** (Ontdekt Later)

**Voorbeelden:**
- Lekkage in plafond (was niet zichtbaar)
- Schimmel achter kasten
- Gebroken leidingen onder vloer
- Elektrische problemen

**Wie Betaalt:** Complexe situatie

**Proces:**
1. Ontdekken na incheck nieuwe huurder
2. Analyseren: Wanneer ontstaan?
   - Als duidelijk oude huurder: Proberen te verhalen (moeilijk)
   - Als onduidelijk: RR/eigenaar betaalt
   - Als nieuwe huurder: Nieuwe huurder betaalt (bij volgende uitcheck)
3. Prioriteit herstel: HOOG (veiligheid/leefbaarheid)
4. Afhandelen: Meestal RR of eigenaar neemt op zich

#### 4. **Acute Schade** (Tijdens Huurperiode)

**Voorbeelden:**
- Lekkage ontstaat
- Verwarming stuk
- Inbraak schade
- Storm schade

**Wie Betaalt:** 
- Als schuld huurder: Huurder
- Als niet schuld huurder: Eigenaar/verzekering

**Proces:**
1. Huurder meldt direct
2. RR/eigenaar lost direct op
3. Kosten worden later verrekend
4. Bij uitcheck: Checken of alles goed hersteld is

### 🔧 Schade Tracking (Voorstel)

**Huidige Situatie:**
- Kolom `Schade_Gemeld` → Ja/Nee
- Details in `Opmerkingen`

**Probleem:**
- Geen gestructureerde tracking van schade
- Kosten niet duidelijk
- Wie betaalt niet duidelijk
- Status herstel niet duidelijk

**Voorstel: Extra Kolommen**

| Kolom | Type | Doel |
|-------|------|------|
| `Schade_Type` | Dropdown | Gebruikersschade / Slijtage / Verborgen / Acute |
| `Schade_Details` | Tekst | Wat precies? "Gat in muur woonkamer 30x30cm" |
| `Schade_Kosten_Geschat` | Getal | Geschatte kosten €150 |
| `Schade_Kosten_Werkelijk` | Getal | Werkelijke kosten na herstel €175 |
| `Schade_Gedekt_Door` | Dropdown | Huurder / Eigenaar / RR / Verzekering |
| `Schade_Herstel_Status` | Dropdown | Te Plannen / Gepland / Bezig / Voltooid |
| `Schade_Herstel_Datum` | Datum | Wanneer gerepareerd? |
| `Schade_Fotos` | Link | Link naar voor/na foto's |

**Voorbeeld in Gebruik:**
```
Uitcheck op 15-12-2025:
- Schade_Gemeld: Ja
- Schade_Type: Gebruikersschade
- Schade_Details: "Gat in muur woonkamer (TV beugel), vlekken op vloerbedekking slaapkamer"
- Schade_Kosten_Geschat: €250
- Schade_Gedekt_Door: Huurder
- Schade_Herstel_Status: Gepland
- Schade_Herstel_Datum: 18-12-2025

Update na herstel:
- Schade_Kosten_Werkelijk: €275 (iets duurder dan gedacht)
- Schade_Herstel_Status: Voltooid
- Schade_Fotos: [link naar foto album]
```

---

## Prioriteiten Systeem

### ⚡ Waarom Prioriteiten Belangrijk Zijn

**Operationeel:**
- Niet alles kan tegelijk
- Team moet weten: wat eerst?
- Planning maken

**Financieel:**
- Hoge prioriteit = kan niet wachten = hogere kosten mogelijk
- Lage prioriteit = kan gespreid worden = lagere kosten

**Klant Tevredenheid:**
- Nieuwe huurder wacht = ontevreden klant als het niet op tijd klaar is
- Eigenaar terugname = meer tijd = tevreden klant

### ⚡ Prioriteit Levels

| Level | Wanneer | Kenmerken | Actie |
|-------|---------|-----------|-------|
| **🔴 KRITISCH** | Nieuwe huurder staat klaar | - Vaste datum<br>- Contract getekend<br>- Geen uitstel mogelijk | **Direct plannen**<br>Alles moet OP TIJD klaar |
| **🟡 HOOG** | Nieuwe huurder komt binnenkort | - Datum bijna bekend<br>- VIS gepland<br>- Enkele weken tijd | **Snel plannen**<br>Voorbereiden voor VIS |
| **🟢 NORMAAL** | Terug naar eigenaar | - Geen directe deadline<br>- Eigenaar flexibel<br>- Enkele weken/maanden tijd | **Inplannen**<br>Kan gespreid worden |
| **⚪ LAAG** | Wachten op nieuwe huurder | - Geen huurder bekend<br>- Onbepaalde tijd<br>- Geen urgentie | **Wachtlijst**<br>Doen als tijd/budget beschikbaar |

### ⚡ Prioriteit in Planning

**Voorbeeld Week Planning:**

```
WEEK 10-16 DECEMBER 2025

🔴 KRITISCH (Moet deze week):
├─ Uitcheck Adres A (nieuwe huurder 18 dec) → Ana
│  └─ Schoonmaak + herstel → Ricky + externe
├─ VIS Adres B (nieuwe huurder 20 dec) → Christa
├─ Incheck Adres C (nieuwe huurder 15 dec) → Ana
└─ Acute herstel Adres D (lekkage) → Direct

🟡 HOOG (Deze/volgende week):
├─ Pre-inspectie Adres E (uitcheck 22 dec) → Dion
└─ Schoonmaak Adres F (VIS volgende week) → Externe

🟢 NORMAAL (Binnen 2 weken):
├─ Uitcheck Adres G (terug naar eigenaar) → Jamie
└─ Herstel Adres H (geen haast) → Ricky

⚪ LAAG (Wanneer tijd):
└─ Cosmetisch werk Adres I → Later
```

### ⚡ In Het Systeem (Voorstel)

**Huidige Situatie:**
- Geen prioriteit kolom
- Moeilijk te zien wat urgent is

**Voorstel: Prioriteit Kolom**

| Kolom | Type | Opties | Wanneer Gebruiken |
|-------|------|--------|-------------------|
| `Prioriteit` | Dropdown | Kritisch / Hoog / Normaal / Laag | Bij elke nieuwe uitcheck |

**Auto-bepalen Prioriteit:**
```
IF nieuwe huurder bekend EN intrek_datum < 14 dagen
  → Prioriteit = KRITISCH

IF nieuwe huurder bekend EN intrek_datum < 30 dagen
  → Prioriteit = HOOG

IF terug naar eigenaar
  → Prioriteit = NORMAAL

IF geen nieuwe huurder bekend
  → Prioriteit = LAAG
```

**Gebruik in Filters:**
```
Filter View: "Deze Week Kritisch"
- Prioriteit = Kritisch
- Geplande_Datum = Deze Week
- Status ≠ Voltooid

→ Geeft direct overzicht van urgente zaken!
```

---

## Systeem Verbeteringen

### 🎯 Wat Nu Goed Werkt

✅ **Basis Tracking:**
- Adressen
- Klanten
- Datums
- Status
- Inspecteurs

✅ **Dropdowns:**
- Gestandaardiseerde waardes
- Minder fouten
- Sneller invoeren

✅ **Structuur:**
- Duidelijke scheiding Uitchecks / Inchecks
- Referentie tabellen voor Klanten/Panden

### 🔧 Wat Kan Beter - Voorstellen

#### 1. **VIS Tracking Toevoegen**

**Probleem:**
- VIS is een kritieke stap
- Wordt nu niet goed getrackt
- Zit ergens in opmerkingen of inchecks

**Oplossing:**
Voeg kolom toe in **Uitchecks** tab:
- `VIS_Datum` (datum)
- `VIS_Inspecteur` (dropdown - zelfde als Inspecteur)
- `VIS_Akkoord` (Ja/Nee - heeft nieuwe huurder akkoord gegeven?)

**Workflow:**
```
Pre-Inspectie → Uitcheck → Schoonmaak → VIS → Incheck
                                        ↑
                                    Track hier!
```

#### 2. **Schoonmaak Tracking Verbeteren**

**Probleem:**
- Wel "wie doet het", maar niet "is het gedaan?"
- Geen kosten tracking
- Niet duidelijk of betaald

**Oplossing:**
Nieuwe kolommen:
- `Schoonmaak_Betaald_Door` (dropdown: Huurder/RR/Eigenaar)
- `Schoonmaak_Kosten` (getal)
- `Schoonmaak_Status` (dropdown: Te Plannen/Gepland/Bezig/Voltooid)
- `Schoonmaak_Datum` (datum)

#### 3. **Schade Management Systeem**

**Probleem:**
- Nu alleen "Schade_Gemeld: Ja/Nee"
- Geen details, geen kosten, geen status

**Oplossing:**
Zie sectie "Schade Afhandeling" hierboven - uitgebreide kolommen voor:
- Type schade
- Details
- Kosten (geschat/werkelijk)
- Wie betaalt
- Herstel status
- Foto's

**Alternatief: Aparte Tab**
Maak een **Schade** tab:
- Gekoppeld aan Uitcheck_ID
- Elke schade = aparte rij
- Beter voor meerdere schade items per uitcheck

#### 4. **Prioriteit Systeem**

**Probleem:**
- Niet duidelijk wat urgent is
- Planning lastig
- Team weet niet wat eerst

**Oplossing:**
- `Prioriteit` kolom (Kritisch/Hoog/Normaal/Laag)
- Filter views: "Kritisch Deze Week"
- Auto-bepalen op basis van nieuwe huurder datum

#### 5. **Foto Management**

**Probleem:**
- Foto's worden gemaakt maar niet centraal getrackt
- Moeilijk terug te vinden
- Geen link in systeem

**Oplossing Optie A: Links**
Kolommen voor foto album links:
- `Pre_Inspectie_Fotos_Link`
- `Uitcheck_Fotos_Link`
- `VIS_Fotos_Link`
- `Incheck_Fotos_Link`

**Oplossing Optie B: Centraal Systeem**
- Gebruik foto management systeem
- Elke uitcheck = één album met subfolders
- Link album ID in uitchecks systeem

#### 6. **Uitcheck ↔ Incheck Koppeling Versterken**

**Probleem:**
- Gekoppelde_Uitcheck_ID in Inchecks tab
- Maar niet andersom
- Moeilijk te zien: "is er nieuwe huurder voor deze uitcheck?"

**Oplossing:**
Voeg toe in **Uitchecks**:
- `Gekoppelde_Incheck_ID` (automatisch invullen)
- `Nieuwe_Huurder_Naam` (copy van Inchecks)
- `Intrek_Datum` (copy van Inchecks)

**Of:** Slimme formule die checkt:
"Is er een Incheck rij met Gekoppelde_Uitcheck_ID = deze ID?"

#### 7. **Status Workflow Uitbreiden**

**Huidig:**
- Gepland → Bezig → Voltooid

**Te Basic Voor Jullie Proces!**

**Voorstel: Gedetailleerdere Status**
- `Gepland` - Uitcheck staat gepland
- `Pre-Inspectie Gedaan` - Voor-oplevering uitgevoerd
- `Uitcheck Gedaan` - Eind inspectie gedaan, sleutels binnen
- `Schoonmaak Bezig` - Schoonmaak/herstel aan de gang
- `VIS Gepland` - Wachten op VIS met nieuwe huurder
- `VIS Gedaan` - Voor-incheck gedaan, huurder akkoord
- `Klaar voor Incheck` - Wachten op intrek datum
- `Incheck Gedaan` - Nieuwe huurder ingetrokken
- `Voltooid` - Alles afgerond, inclusief eindafrekening

**Of: Meerdere Status Kolommen**
- `Inspectie_Status` (Pre/Uitcheck/VIS/Incheck)
- `Schoonmaak_Status` (Te Doen/Bezig/Klaar)
- `Herstel_Status` (Te Doen/Bezig/Klaar)
- `Financieel_Status` (Te Maken/Verzonden/Betaald)

#### 8. **Dashboard / Overzicht Views**

**Probleem:**
- Veel data maar geen overzicht
- Moeilijk te zien: "Wat moet ik VANDAAG doen?"

**Oplossing: Gefilterrde Views Maken**

In Excel (of beter in Notion):
- **View: Deze Week Kritisch**
  - Prioriteit = Kritisch
  - Geplande Datum = Deze Week
  - Status ≠ Voltooid

- **View: Mijn Taken (Ana)**
  - Inspecteur = Ana
  - Status = Gepland of Bezig
  - Sorteer op Geplande Datum

- **View: Wacht op VIS**
  - Status = VIS Gepland
  - Sorteer op Prioriteit

- **View: Financieel Openstaand**
  - Afrekening_Status ≠ Voltooid
  - Uitcheck_Datum < 30 dagen geleden

---

## Conclusie & Next Steps

### 📊 Wat We Nu Hebben

✅ **Basis Systeem Werkt:**
- Uitchecks worden getrackt
- Inchecks worden getrackt
- Data is schoon en gestructureerd
- Nederlands interface

### 🚀 Wat We Kunnen Verbeteren

**Quick Wins** (Makkelijk toe te voegen):
1. `VIS_Datum` kolom
2. `Prioriteit` kolom
3. Filter views maken
4. `Nieuwe_Huurder_Naam` en `Intrek_Datum` in Uitchecks

**Medium Effort** (Wat meer werk):
1. Schoonmaak tracking uitbreiden
2. Status workflow detailleren
3. Foto links toevoegen

**Grotere Projecten** (Overweeg later):
1. Complete schade management systeem
2. Migratie naar Notion (beter voor workflows)
3. Automatiseringen (emails, herinneringen)
4. Dashboard met grafieken

### ❓ Vragen Voor Jou

1. **VIS Tracking:** Wil je VIS apart tracken in Uitchecks tab?

2. **Prioriteit:** Wil je auto-prioriteit op basis van nieuwe huurder datum?

3. **Schade:** Aparte tab voor schade, of gewoon meer kolommen in Uitchecks?

4. **Foto's:** Hoe beheren jullie nu foto's? Willen jullie dit gekoppeld aan het systeem?

5. **Status:** Wil je gedetailleerdere status (8 stappen) of is huidig (3 stappen) genoeg?

6. **Platform:** Blijven we in Excel of overwegen jullie Notion?
   - Excel: Bekend, werkt, maar gelimiteerd
   - Notion: Krachiger, mooiere workflows, betere samenwerking, kan koppelingen maken

### 🎯 Mijn Aanbeveling

**Fase 1: Quick Wins (Deze Week)**
- Voeg `VIS_Datum`, `Prioriteit`, `Nieuwe_Huurder_Naam` kolommen toe
- Maak 3-4 handige filter views
- Train team op huidige systeem

**Fase 2: Verbeteringen (Volgende Maand)**
- Schoonmaak & schade tracking verbeteren
- Status workflow uitbreiden
- Foto management oplossen

**Fase 3: Evaluatie (Over 2-3 Maanden)**
- Is Excel nog genoeg?
- Overweeg Notion voor betere workflows
- Automatiseringen toevoegen

---

**Laat me weten wat je wil dat ik aanpas/toevoeg! 🚀**