#!/bin/bash
# ==================================================
# RyanRent - Eindafrekening Generator
# Double-click to generate from Eindafrekening Inputs
# ==================================================

cd "$(dirname "$0")"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🏠 RyanRent Eindafrekening Generator                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Activate virtual environment (check parent folder too)
if [ -d "../venv" ]; then
    source ../venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the generator - it has built-in interactive file picker
# that looks in Eindafrekening Inputs folder
python3 src/generate.py

echo ""
read -p "👉 Druk op Enter om af te sluiten..."
