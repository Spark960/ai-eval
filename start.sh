#!/bin/bash

echo "==================================================="
echo "   Multimodal AI Evaluation Framework (Mac/Linux)"
echo "==================================================="
echo "First run will take a few minutes to install dependencies."

# Catch Ctrl+C to cleanly kill both background processes
trap 'echo ""; echo "Shutting down servers..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit' INT

echo "[1/2] Starting FastAPI Backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -q
uvicorn main:app --reload &
BACKEND_PID=$!
cd ..

echo "[2/2] Starting Vite Frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing NPM modules..."
    npm install
fi
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Both servers are running."
echo "Open http://localhost:5173 in your browser."
echo "Press Ctrl+C in this terminal to stop both servers."

# Wait indefinitely so the script doesn't exit until Ctrl+C is pressed
wait