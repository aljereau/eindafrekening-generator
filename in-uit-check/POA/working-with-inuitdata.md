# AI / Database regels (Cursor implementatie)

## Doel
De AI helpt met:
- statusoverzichten
- open acties / bottlenecks
- prioriteit voorstellen
- data toevoegen/aanpassen op expliciet verzoek

De AI neemt geen stille beslissingen. Alles wat impact heeft op planning/status gebeurt expliciet.

---

## Kernregels

### 1) Cyclus is leidend
- `woning_cycli.status` wordt bewust gezet door de gebruiker (of expliciete AI-opdracht).
- `woning_acties` bewijzen of de status klopt.

### 2) Maximaal 1 actieve cyclus per huis
- `woning_cycli.is_actief = 1` mag maar één keer per huis voorkomen.
- Bij `status = AFGEROND`: zet `is_actief = 0`.

### 3) Acties zijn append-only
In principe:
- nieuwe feiten = nieuwe actie rij
- alleen corrigeren als het echt een fout was (verkeerde datum, typo)

---

## Status-validatie (wat “klopt” betekent)
De AI/Dashboard mag checks tonen zoals “STATUS_KLOPT_NIET” + reden.

### VOORINSPECTIE_GEPLAND
Vereist:
- actie_type = VOORINSPECTIE met `gepland_op` gevuld

### VOORINSPECTIE_UITGEVOERD
Vereist:
- VOORINSPECTIE met `uitgevoerd_op` gevuld

### UITCHECK_GEPLAND
Vereist:
- UITCHECK met `gepland_op` gevuld

### UITCHECK_UITGEVOERD
Vereist:
- UITCHECK met `uitgevoerd_op` gevuld
- `verwachte_schoonmaak_uren` is NOT NULL

### SCHOONMAAK_NODIG
Vereist:
- UITCHECK uitgevoerd met `verwachte_schoonmaak_uren > 0`
- en bij voorkeur een SCHOONMAAK actie met `gepland_op` (planning)

### KLAAR_VOOR_INCHECK
Vereist (één van):
- `verwachte_schoonmaak_uren = 0`
- OF SCHOONMAAK actie uitgevoerd met `werkelijke_schoonmaak_uren` gevuld

### INCHECK_GEPLAND
Vereist:
- INCHECK met `gepland_op` gevuld

### INCHECK_UITGEVOERD
Vereist:
- INCHECK met `uitgevoerd_op` gevuld
- `sleutels_bevestigd = JA`

### TERUG_NAAR_EIGENAAR
Vereist:
- bestemming = TERUG_NAAR_EIGENAAR
- OVERDRACHT_EIGENAAR actie gepland/uitgevoerd (afhankelijk hoe strak je wil)

### AFGEROND
Vereist:
- als bestemming = OPNIEUW_VERHUREN: INCHECK_UITGEVOERD
- als bestemming = TERUG_NAAR_EIGENAAR: OVERDRACHT_EIGENAAR uitgevoerd
- zet is_actief = 0

---

## Planning / prioriteit (basis)
Prioriteit is een score, geen handmatig veld.

Inputs:
- `status`
- `startdatum_nieuwe_huurder` (deadline)
- open acties (geen uitgevoerd_op)
- `verwachte_schoonmaak_uren` (workload)
- `klant_type`

Output:
- prioriteitenlijst: “wat moet eerst”

---

## AI Mutatie-regels (veiligheid)
AI mag alleen schrijven als de gebruiker expliciet vraagt om:
- cyclus aanmaken
- status wijzigen
- actie toevoegen
- actie corrigeren

AI moet bij schrijven altijd:
- exact tonen wat er gewijzigd wordt (voor/na)
- en welke velden gebruikt zijn
- en welke checks nu groen/rood worden