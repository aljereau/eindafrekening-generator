# 🚀 RyanRent Eindafrekening Generator - Snelstart Gids

**Voor niet-technische gebruikers** - Geen installatie nodig!

---

## 📋 Stap 1: Vul de Excel In

1. **Open** `input_template.xlsx` in Excel
2. **Vul de 4 tabbladen in:**

   ### 🔵 Tabblad 1: Algemeen
   - Klantnaam, email, adres
   - Check-in en check-out data
   - Voorschotten (Borg, GWE, Schoonmaak)
   - Schoonmaak pakket (5_uur of 7_uur)

   ### 🟢 Tabblad 2: GWE_Detail
   - Meterstanden (elektra en gas)
   - Kostenregels met tarieven invullen

   ### 🟠 Tabblad 3: Schoonmaak
   - Totaal uren gewerkt

   ### 🔴 Tabblad 4: Schade
   - Eventuele schadeposten (of leeglaten)

3. **Sla het bestand op** (Cmd+S of Ctrl+S)

---

## 🖱️ Stap 2: Genereer de Eindafrekening

1. **Dubbelklik** op het programma:
   - **Mac**: `RyanRent_Generator` (in de `dist` map)
   - **Windows**: `RyanRent_Generator.exe`

2. **Wacht even...**
   - Het programma start op
   - De berekeningen worden gemaakt
   - De HTML bestanden openen automatisch in je browser

---

## 🌐 Stap 3: Print naar PDF

Als de browser opent, zie je **2 tabbladen**:
- **OnePager** - Simpel overzicht voor de klant
- **Detail** - Uitgebreid met alle details

### Print/Opslaan als PDF:

**Mac:**
1. Druk `Cmd + P` (of Bestand → Print)
2. Kies **"Opslaan als PDF"** onderaan links
3. Kies locatie en klik **Opslaan**

**Windows:**
1. Druk `Ctrl + P` (of Bestand → Afdrukken)
2. Kies **"Microsoft Print to PDF"**
3. Klik **Afdrukken**
4. Kies locatie en klik **Opslaan**

---

## ✅ Klaar!

Je hebt nu:
- ✓ **OnePager PDF** - Stuur naar de klant
- ✓ **Detail PDF** - Bewaar in administratie
- ✓ **Database Backup** - De afrekening is automatisch opgeslagen in de database

---

## ❓ Veelgestelde Vragen

### Q: Waar staat het programma?
**A:** In de `dist` map. Je kunt dit bestand naar je Bureaublad slepen (zorg wel dat `input_template.xlsx` in dezelfde map staat als je het start).

### Q: Het programma start niet?
**A:** Op Mac moet je de eerste keer misschien rechtsklikken en kiezen voor "Open" als de beveiliging klaagt.

### Q: Waar staan de gegenereerde bestanden?
**A:** In de `output/` map.

---

## 📞 Hulp Nodig?

**Contact:** Aljereau Marten
**Locatie:** OneDrive → RyanRent → Aljereau → Eindafrekening Generator

---

**Versie:** 2.1 (Standalone App)
**Laatst bijgewerkt:** November 2024
