#!/bin/bash
# RyanRent V2 Launcher

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "🚀 Starting RyanRent V2..."

# 1. Start Backend in background
echo "Starting API Server..."
source .venv/bin/activate
python3 -m uvicorn ryan_v2.api:app --reload --port 8000 > ryan_api.log 2>&1 &
BACKEND_PID=$!
echo "API Server PID: $BACKEND_PID"

# 2. Start Frontend
echo "Starting Web Client..."
cd ryan_v2/web_client
npm run dev > ../../ryan_web.log 2>&1 &
FRONTEND_PID=$!
echo "Web Client PID: $FRONTEND_PID"

# 3. Open Browser
sleep 2
open http://localhost:5173

echo "✅ RyanRent V2 is running!"
echo "   - Backend: http://localhost:8000"
echo "   - Frontend: http://localhost:5173"
echo "   - Logs: ryan_api.log, ryan_web.log"
echo ""
echo "Press any key to stop servers..."
read -n 1

kill $BACKEND_PID
kill $FRONTEND_PID
echo "🛑 Stopped."
