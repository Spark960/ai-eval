@echo off
echo ===================================================
echo   Multimodal AI Evaluation Framework (Windows)
echo ===================================================

echo [1/2] Starting FastAPI Backend...
start "Backend (uvicorn)" cmd /k "cd backend && if not exist venv (python -m venv venv) && call venv\Scripts\activate && pip install -r requirements.txt && uvicorn main:app --reload"

echo [2/2] Starting Vite Frontend...
start "Frontend (vite)" cmd /k "cd frontend && if not exist node_modules (npm install) && npm run dev"

echo.
echo  Both servers are booting in separate windows.
echo  Open http://localhost:5173 in your browser.
echo  Close the terminal windows to stop the servers.