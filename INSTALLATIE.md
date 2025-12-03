# 🏠 RYAN - Installatie Instructies

## Voor Niet-Technische Gebruikers

### Stap 1: Download Docker Desktop (EENMALIG)

**Windows:**
1. Ga naar: https://www.docker.com/products/docker-desktop
2. Klik op "Download for Windows"
3. Open het gedownloade bestand
4. Klik steeds op "Next" en dan "Install"
5. Start je computer opnieuw op als het vraagt
6. Open "Docker Desktop" vanuit je Start menu
7. Wacht tot je een groen icoontje ziet rechtsonder (betekent: klaar!)

**Mac:**
1. Ga naar: https://www.docker.com/products/docker-desktop
2. Klik op "Download for Mac"
3. Sleep Docker naar je Applications folder
4. Open Docker vanuit Applications
5. Klik "Open" als het vraagt of je het vertrouwt
6. Wacht tot je een groen icoontje ziet bovenin (betekent: klaar!)

---

### Stap 2: Krijg de RyanRent folder van Aljereau

Aljereau stuurt je een folder genaamd "Eindafrekening Generator".
Zet deze ergens op je computer (bijv. op je Bureaublad of in Documenten).

---

### Stap 3: Maak een .env bestand

1. Open de "Eindafrekening Generator" folder
2. Zoek het bestand `.env.example`
3. **Kopieer** dit bestand (Ctrl+C, Ctrl+V op Windows / Cmd+C, Cmd+V op Mac)
4. **Hernoem** de kopie naar `.env` (zonder "example")
5. Open `.env` met Kladblok (Windows) of TextEdit (Mac)
6. Vraag Aljereau om de API keys en plak ze in:
   ```
   ANTHROPIC_API_KEY=sk-ant-hier-komt-de-key
   OPENAI_API_KEY=sk-hier-komt-de-key
   ```
7. Sla op en sluit

---

### Stap 4: Start RYAN

**Windows:**
- Dubbelklik op `start.bat` in de folder
- Een zwart scherm opent → wacht 1-2 minuten (eerste keer duurt langer)
- Als je "Select a model" ziet → gebruik pijltjestoetsen en Enter
- Klaar! Je kunt nu chatten met RYAN

**Mac:**
- Dubbelklik op `start.sh` in de folder
- Als het niet werkt: open Terminal, typ `cd ` (met spatie), sleep de folder naar Terminal, druk Enter
- Typ: `./start.sh` en druk Enter
- Wacht 1-2 minuten
- Als je "Select a model" ziet → gebruik pijltjestoetsen en Enter
- Klaar! Je kunt nu chatten met RYAN

---

## Hulp Nodig?

### "Docker is not running"
→ Open Docker Desktop en wacht tot het groen is

### "Permission denied" (Mac)
→ Vraag Aljereau om hulp (eenmalige fix nodig)

### Andere problemen?
→ Stuur screenshot naar Aljereau

---

## Wat je NIET hoeft te doen:
❌ Python installeren  
❌ Pip installeren  
❌ Dependencies installeren  
❌ Code begrijpen  

## Wat Docker voor je doet:
✅ Installeert alles automatisch  
✅ Werkt hetzelfde op elke computer  
✅ Geen gedoe met versies  

---

**Eerste keer opstarten duurt 2-3 minuten. Daarna start het in 10 seconden!**
