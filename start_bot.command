#!/bin/bash
# RyanRent Bot Launcher
# Double-click to start!

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "╔════════════════════════════════════╗"
echo "║       🤖 RyanRent Bot              ║"
echo "╚════════════════════════════════════╝"
echo ""

# 1. Activate Virtual Environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  No 'venv' found. Using system python3..."
fi

# 2. Check for dependencies
python3 -c "import textual" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
fi

# 3. Launch the Bot
# We use the HuizenManager/src/chat.py entry point
echo "🚀 Launching (Type 'q' to quit)..."
python3 HuizenManager/src/chat.py

# Pause on exit
echo ""
echo "Bot stopped."
read -p "Press Enter to close..."
