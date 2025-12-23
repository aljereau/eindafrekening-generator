Je hebt nu genoeg regels om dit als een deterministisch prioriteitsmodel te bouwen (dus voorspelbaar, uitlegbaar, en later door AI te “verwoorden”). Hieronder is een concreet voorstel dat precies jouw prioriteits-sequence vangt.

⸻

1) Inputs die we nodig hebben per woning-cyclus

Van elke actieve cyclus willen we deze velden (of afleidingen):
	•	klant_type (TRADIRO / EXTERN / EIGENAAR)
	•	startdatum_nieuwe_huurder (kan NULL zijn)
	•	status (voor volgende actie)
	•	verwachte_schoonmaak_uren (uit laatste UITCHECK)
	•	dirty_class (afgeleid uit verwachte uren + woninggrootte of simpel thresholds)
	•	vandaag (runtime)
	•	min_lead_days (afhankelijk van dirty_class)
	•	deadline = startdatum_nieuwe_huurder (als gepland) anders een “soft deadline” (optioneel)

⸻

2) “Dirty” logic: liever als lead-time dan subjectieve labels

Je zei al: dirty in uren is beter. Mee eens. Maar voor planning heb je alsnog een categorie nodig om “minimum dagen vóór deadline” te bepalen.

Voorstel: dirty_class = op basis van verwachte uren
	•	LAAG: 0 – 2 uur → min_lead_days = 1
	•	MIDDEL: >2 – 5 uur → min_lead_days = 2
	•	HOOG: >5 uur → min_lead_days = 3 (of 4 bij extreme)

Dit zijn startwaarden, je verfijnt later met expected vs actual.

⸻

3) Prioriteits-sequence als regels (hard gates)

In praktijk wil je eerst “gates” bepalen, dan pas score.

Gate A — Tradiro altijd voorrang

Als klant_type = TRADIRO → zet client_priority_rank = 1
Anders → client_priority_rank = 2 (EXTERN) / 3 (EIGENAAR)

Dit betekent: Tradiro komt altijd bovenaan, tenzij je zelf uitzonderingsregels toevoegt.

Gate B — Heeft nieuwe huurder ingepland?

Als startdatum_nieuwe_huurder IS NOT NULL → urgentie omhoog.
Dit is jullie “contractuele realiteit”.

Gate C — Kan het überhaupt nog op tijd?

Voor woningen die nog schoongemaakt moeten worden:
	•	bereken required_ready_date = startdatum_nieuwe_huurder - min_lead_days
	•	als vandaag > required_ready_date → CRITICAL (achterstand / escalation)

Hier zit jouw “really dirty needs minimum days before check-in” precies.

⸻

4) Daarna: scoremodel (binnen de gates)

Binnen dezelfde gate-rangorde sorteer je met een priority_score.

Componenten
	1.	Deadline druk
	•	days_to_movein = (startdatum_nieuwe_huurder - vandaag)
	•	Hoe kleiner, hoe hoger de score
	2.	Lead-time druk (dirty-lead-days)
	•	days_until_required_ready = (required_ready_date - vandaag)
	•	<= 0 → enorme boost
	3.	Werkload
	•	hogere verwachte_schoonmaak_uren krijgt hogere urgency als deadline dichtbij is
	•	(dus niet: “veel uren altijd eerst”, maar: “veel uren + krappe deadline eerst”)
	4.	Status blokkade
	•	als status-check rood is → boost, want je planning is anders onbetrouwbaar

⸻

5) Concreet sorteer-criterium (simpel en sterk)

Je kunt dit letterlijk als ORDER BY logica gebruiken:
	1.	client_priority_rank (Tradiro eerst)
	2.	has_movein_date (true eerst)
	3.	is_critical_late (true eerst)
	4.	days_until_required_ready (kleinste eerst)
	5.	days_to_movein (kleinste eerst)
	6.	verwachte_schoonmaak_uren (grootste eerst)
	7.	status_severity (ERROR > WARN > OK)

Dat geeft jouw “prio sequence” zonder vage AI.

⸻

6) Output: wat de planner ziet

Per woning wil je direct tonen:
	•	Prioriteit: CRITICAL / HIGH / NORMAL / LOW
	•	Waarom (regels in plain text)
	•	“Tradiro woning”
	•	“Nieuwe huurder op 3 dagen”
	•	“Verwachte schoonmaak 6 uur, min lead-time 3 dagen”
	•	“Moet klaar zijn uiterlijk: 2025-01-05”
	•	Volgende actie (uit status + checks)
	•	“Plan schoonmaak”
	•	“Voer uitcheck uit”
	•	“Bevestig sleutels”

⸻

7) Belangrijk: waar ‘dirty’ vandaan komt

Je noemde “echt vies”. In jullie model:
	•	na UITCHECK vul je verwachte_schoonmaak_uren
	•	daaruit volgt dirty_class
	•	dat bepaalt min_lead_days

Dus je hebt geen subjectieve “vies/medium” kolom nodig, alleen uren.

⸻

Als je wil, schrijf ik dit nu in een .md als “Prioriteringsregels v1” én geef ik je:
	•	een SQL view v_prioriteit die deze velden uitrekent
	•	en een sample ORDER BY query die meteen je werkvoorraad sorteert