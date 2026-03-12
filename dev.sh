#!/bin/bash

echo "🛡️  Initializing Spec-Drift Chronometer: Sovereign Warden Suite..."

# 1. Backend Setup & Activation
echo "⚙️  Configuring Warden Engine (Backend)..."
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt --quiet

# Start Backend from the ROOT so it can find the 'backend' module
echo "🚀 Starting Warden Engine heartbeat..."
export PYTHONPATH=$PYTHONPATH:$(pwd)
python backend/main.py &
BACKEND_PID=$!

# 2. Frontend Setup & Activation
echo "🎨 Initializing Dashboard (Frontend)..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install --quiet
fi

echo "🌐 Launching Sovereign Dashboard at http://localhost:3000"
npm run dev &
FRONTEND_PID=$!

echo "✅ System is LIVE. Press [CTRL+C] to power down the Warden."

trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
