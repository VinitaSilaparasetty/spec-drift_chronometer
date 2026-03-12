#!/bin/bash

echo "🛡️  Initializing Spec-Drift Chronometer: Sovereign Warden Suite..."

cleanup() {
    echo -e "\n🛑 Shutting down Sovereign Warden..."
    # Kill the processes
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    sleep 1
    # Force kill if still hanging
    kill -9 $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "✅ System offline. Cursor restored."
    exit 0
}

# 1. Backend Setup
echo "⚙️  Configuring Warden Engine (Backend)..."
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt --quiet
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Start Backend
python backend/main.py &
BACKEND_PID=$!

# 2. Frontend Setup
echo "🎨 Initializing Dashboard (Frontend)..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install --quiet
fi

# Start Frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ System is LIVE at http://localhost:3000"
echo "💡 Press [CTRL+C] to power down."

trap cleanup INT
wait
