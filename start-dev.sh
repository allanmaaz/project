#!/bin/bash

# Clarify AI local development startup script.
# Boots up backend (FastAPI) and frontend (Next.js) concurrently.

# Exit immediately if any command fails
set -e

echo "◈ Starting Clarify AI Local Development Environment..."

# ── Step 1: Check Python environment ──
if [ ! -d "backend/venv" ]; then
  echo "⚡ Creating Python virtual environment in backend/venv..."
  python3 -m venv backend/venv
fi

echo "⚡ Installing backend dependencies..."
source backend/venv/bin/activate
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install --upgrade pip
pip install -r backend/requirements.txt

# ── Step 2: Check Node environment ──
echo "⚡ Installing frontend dependencies..."
cd frontend
if command -v pnpm &> /dev/null; then
  pnpm install
else
  npm install
fi
cd ..

# ── Step 3: Boot servers concurrently ──
echo "🚀 Booting backend (Port 8000) and frontend (Port 3000)..."

# Trap CTRL+C to kill both background processes
trap "kill 0" EXIT

# Start backend
source backend/venv/bin/activate
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
cd ..

# Start frontend
cd frontend
if command -v pnpm &> /dev/null; then
  pnpm dev &
else
  npm run dev &
fi
cd ..

# Wait for both processes
wait
