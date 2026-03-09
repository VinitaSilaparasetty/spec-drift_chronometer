#!/bin/bash

# 1. Kill any existing processes on ports 8000 (API) and 3000 (UI)
echo "--- Cleaning environment ---"
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

# 2. Start the Backend (Brain) in the background
echo "--- Igniting Warden Brain ---"
uv run chronometer & 

# 3. Wait 2 seconds for the API to stabilize
sleep 2

# 4. Start the Frontend (Face)
echo "--- Launching Brand Portal ---"
cd frontend && npm run dev
