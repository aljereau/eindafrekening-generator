#!/bin/bash
# ==================================================
# RyanRent - New Eindafrekening Template Creator
# Double-click to create a fresh input template
# ==================================================

cd "$(dirname "$0")"

echo "🏠 RyanRent - Nieuwe Template Aanmaken"
echo "========================================"

# Activate virtual environment (check parent folder too)
if [ -d "../venv" ]; then
    source ../venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the template generator (relative to Eindafrekening folder)
python3 scripts/create_master_template.py

echo ""
echo "✅ Klaar! Template staat in: Eindafrekening Inputs/"
echo ""
read -p "👉 Druk op Enter om af te sluiten..."

