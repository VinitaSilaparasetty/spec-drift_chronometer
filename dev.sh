#!/bin/bash

echo "🛡️  Initializing Spec-Drift Chronometer: Sovereign Warden Suite..."

# 1. Backend Setup & Activation
echo "⚙️  Configuring Warden Engine (Backend)..."
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt --quiet

# Start Backend in the background
echo "🚀 Starting Warden Engine heartbeat..."
python backend/main.py &
BACKEND_PID=$!

# 2. Frontend Setup & Activation
echo "🎨 Initializing Dashboard (Frontend)..."
cd frontend
# Install npm packages if node_modules is missing
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install --quiet
fi

# Start Frontend
echo "🌐 Launching Sovereign Dashboard at http://localhost:3000"
npm run dev &
FRONTEND_PID=$!

# 3. Graceful Exit
echo "✅ System is LIVE. Press [CTRL+C] to power down the Warden."

# This ensures that when you press CTRL+C, both the Python and Node processes are killed
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
