#!/bin/bash

echo "RyanRent Eindafrekening Generator"
echo "================================="
echo ""

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Fout: Python 3 is niet gevonden!"
    echo "Installeer Python van https://www.python.org/downloads/"
    exit 1
fi

# Check/Create virtual environment
if [ ! -d "venv" ]; then
    echo "Eerste keer opstarten: virtuele omgeving aanmaken..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install requirements if needed
if ! pip show openpyxl &> /dev/null; then
    echo "Bibliotheken installeren..."
    pip install -r requirements.txt
fi

# Run the script
python generate.py

# Deactivate
deactivate
