#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting Optimised Math Learning Platform..."

# 1. Start the Python FastAPI backend in the background
echo "⚡ Launching FastAPI Backend on port 8000..."
if [ -d ".venv" ]; then
    .venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
else
    python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
    echo "⚠️ Warning: .venv folder not found. Using system python3."
fi

# Save the backend Process ID so we can shut it down gracefully later
BACKEND_PID=$!

# 2. Open a separate Mac terminal window to run the Next.js dev server
echo "🎨 Launching Next.js Frontend on port 3000..."
osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR/frontend' && npm run dev\""

# 3. Wait 3 seconds for the servers to warm up, then open the browser
sleep 3
echo "🌐 Opening the Math Arena arena..."
open http://localhost:3000/arena

# Keep this script window responsive so you can close everything cleanly
echo "------------------------------------------------"
echo "🟢 App is running! Press [CTRL+C] in this window to stop the backend."
echo "------------------------------------------------"

# Trap Ctrl+C to kill the backend server process when you're done
trap "echo '🛑 Stopping backend...'; kill $BACKEND_PID; exit" INT
wait