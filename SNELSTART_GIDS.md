# 🚀 RyanRent Eindafrekening Generator - Snelstart Gids

**Voor niet-technische gebruikers** - Geen Terminal kennis nodig!

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

### **Mac gebruikers:**
1. **Dubbelklik** op `Genereer_Eindafrekening.command`
2. Als je een waarschuwing krijgt:
   - Klik rechts → **Open**
   - Klik nogmaals **Open** in de popup

### **Windows gebruikers:**
1. **Dubbelklik** op `Genereer_Eindafrekening.bat`

### ⏳ Wacht even...
- Een Terminal/Command venster opent
- Je ziet voortgangsmeldingen
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

---

## ❓ Veelgestelde Vragen

### Q: Het programma start niet, wat nu?
**A:** Zorg dat je het Excel bestand eerst hebt opgeslagen. Als het probleem blijft, neem contact op met Aljereau.

### Q: Ik zie geen browser openen?
**A:** Check of er geen foutmeldingen in het Terminal/Command venster staan. Mogelijk staan er fouten in de Excel data.

### Q: Kan ik meerdere eindafrekeningen tegelijk maken?
**A:** Nee, doe één per keer. Vul Excel in, genereer, bewaar de PDF's, en begin opnieuw voor de volgende klant.

### Q: Waar staan de gegenereerde bestanden?
**A:** In de `output/` map in dezelfde folder als het Excel bestand.

### Q: Moet ik het Excel bestand hernoemen?
**A:** Nee! Houd het als `input_template.xlsx`. De gegenereerde PDF's krijgen automatisch de klantnaam en data in de bestandsnaam.

---

## 📞 Hulp Nodig?

**Contact:** Aljereau Marten
**Locatie:** OneDrive → RyanRent → Aljereau → Eindafrekening Generator

---

## 🎨 Voorbeeld Workflow

```
1. Open input_template.xlsx
2. Vul gegevens Familie Jansen in
3. Sla op (Cmd+S / Ctrl+S)
4. Dubbelklik "Genereer_Eindafrekening"
5. Browser opent automatisch
6. Print beide tabbladen naar PDF
7. Stuur OnePager naar Familie Jansen
8. Bewaar Detail in administratie
9. Klaar! ✅
```

---

**Versie:** 2.0
**Laatst bijgewerkt:** November 2024
