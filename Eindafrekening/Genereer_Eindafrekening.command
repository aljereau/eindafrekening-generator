#!/bin/bash
#
# RyanRent Eindafrekening Generator - Easy Launcher
# Double-click this file to generate eindafrekening
#

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Clear screen and show header
clear
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🏠 RyanRent Eindafrekening Generator                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Bezig met genereren..."
echo ""

# 2. Activeer Virtual Environment (als die bestaat)
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  Geen 'venv' map gevonden. We proberen de standaard python3..."
fi

# 3. Check of input bestand bestaat (in root map)
if [ ! -f "input_template.xlsx" ]; then
    echo "❌ FOUT: 'input_template.xlsx' niet gevonden!"
    echo "   Zorg dat dit bestand in de map '$PWD' staat."
    read -p "Druk op Enter om te sluiten..."
    exit 1
fi

# 4. Start de generator (vanuit src map)
# --no-pause: Zodat we hieronder zelf de pause kunnen beheren
# --auto-open: Open browser automatisch
python3 src/generate.py --no-pause --auto-open

# 5. Check resultaat
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Klaar! Je kunt dit venster sluiten."
    echo "   De HTML bestanden zijn geopend in je browser."
    echo "   Gebruik Cmd+P om te printen of op te slaan als PDF."
fi

# Pause so user can see the output
read -p "Druk op Enter om af te sluiten..."
