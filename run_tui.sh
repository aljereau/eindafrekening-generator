#!/bin/bash

# RyanRent Bot Local Launcher
# Runs the Textual TUI from the local python environment

echo "========================================"
echo "  RyanRent Intelli-Bot (Local)"
echo "========================================"

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 1. Check for Virtual Environment
if [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment (venv)..."
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found!"
    echo "   Recommended: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    echo "   Attempting to use system python3..."
fi

# 2. Check for dependencies (basic check)
python3 -c "import textual" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: 'textual' library not found."
    echo "   Please run: pip install -r requirements.txt"
    read -p "Press Enter to exit..."
    exit 1
fi

# 3. Launch TUI
# We run as a module (-m TUI.app) OR directly pointing to the file, 
# ensuring the PYTHONPATH includes the root directory.
export PYTHONPATH="$DIR:$PYTHONPATH"

echo "Launching TUI..."
python3 TUI/app.py
