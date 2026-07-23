#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Prevent macOS WiFi/corporate proxy (WPAD) from hijacking local backend requests
export NO_PROXY="localhost,127.0.0.1,*.local"
export no_proxy="$NO_PROXY"

echo "🚀 Starting Optimised Math Learning Platform..."

# 1. Start the Python FastAPI backend in the background
echo "⚡ Launching FastAPI Backend on port 8000..."
if [ -d ".venv" ]; then
    .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
else
    python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
    echo "⚠️ Warning: .venv folder not found. Using system python3."
fi

# Save the backend Process ID so we can shut it down gracefully later
BACKEND_PID=$!

# Wait for the backend to accept connections before opening the browser
echo "⏳ Waiting for backend..."
for _ in {1..30}; do
    if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready"
        break
    fi
    sleep 1
done

# 2. Open a separate Mac terminal window to run the Next.js dev server
echo "🎨 Launching Next.js Frontend on port 3000..."
osascript -e "tell application \"Terminal\" to do script \"export NO_PROXY='localhost,127.0.0.1,*.local'; export no_proxy='localhost,127.0.0.1,*.local'; cd '$SCRIPT_DIR/frontend' && npm run dev\""

# 3. Wait for the frontend, then open the browser
echo "⏳ Waiting for frontend..."
for _ in {1..30}; do
    if curl -sf http://127.0.0.1:3000 > /dev/null 2>&1; then
        echo "✅ Frontend is ready"
        break
    fi
    sleep 1
done

echo "🌐 Opening the app..."
open http://127.0.0.1:3000/login

# Keep this script window responsive so you can close everything cleanly
echo "------------------------------------------------"
echo "🟢 App is running! Press [CTRL+C] in this window to stop the backend."
echo "------------------------------------------------"

# Trap Ctrl+C to kill the backend server process when you're done
trap "echo '🛑 Stopping backend...'; kill $BACKEND_PID; exit" INT
wait
