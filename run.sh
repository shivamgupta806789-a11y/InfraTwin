#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "=========================================================="
echo " Starting InfraTwinAI (FastAPI + React + Three.js) "
echo "=========================================================="

# Check and free ports 8000 and 5173 if already occupied
echo "Checking ports 8000 and 5173..."
PID_8000=$(lsof -ti :8000 || true)
if [ -n "$PID_8000" ]; then
    echo "Port 8000 in use by PID $PID_8000. Releasing port..."
    kill -9 $PID_8000 2>/dev/null || true
    sleep 1
fi

PID_5173=$(lsof -ti :5173 || true)
if [ -n "$PID_5173" ]; then
    echo "Port 5173 in use by PID $PID_5173. Releasing port..."
    kill -9 $PID_5173 2>/dev/null || true
    sleep 1
fi

# 1. Setup & Start Backend in background
echo "-> Starting Backend on http://127.0.0.1:8000 ..."
cd "$DIR/backend"
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!
echo "Backend running with PID $BACKEND_PID"

# Wait a second for backend to bind
sleep 2

# 2. Setup & Start Frontend in foreground
echo "-> Starting Frontend on http://localhost:5173 ..."
cd "$DIR/frontend"
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Automatically open browser once Vite starts
(sleep 2 && open http://localhost:5173) &

# Cleanup on exit (Ctrl+C)
trap "echo 'Shutting down services...'; kill $BACKEND_PID 2>/dev/null || true; exit" SIGINT SIGTERM

npm run dev
