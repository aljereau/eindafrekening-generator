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

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ FOUT: Virtual environment niet gevonden!"
    echo "   Neem contact op met de developer."
    echo ""
    read -p "Druk op Enter om af te sluiten..."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if input_template.xlsx exists
if [ ! -f "input_template.xlsx" ]; then
    echo "❌ FOUT: input_template.xlsx niet gevonden!"
    echo "   Zorg dat het Excel bestand in deze map staat."
    echo ""
    read -p "Druk op Enter om af te sluiten..."
    exit 1
fi

# Run the generator with auto-open browser flag
python3 generate.py --no-pause --auto-open

# Check if generation was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Generatie voltooid!"
    echo "   De HTML bestanden zijn geopend in je browser."
    echo "   Gebruik Cmd+P om te printen of op te slaan als PDF."
    echo ""
else
    echo ""
    echo "❌ Er is een fout opgetreden tijdens het genereren."
    echo "   Controleer het Excel bestand en probeer opnieuw."
    echo ""
fi

# Pause so user can see the output
read -p "Druk op Enter om af te sluiten..."
