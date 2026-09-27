@echo off
echo ====================================================
echo Starting SIH26162 Platform Locally (No Docker)
echo ====================================================

echo Starting FastAPI Backend on http://localhost:8000 ...
start "SIH26162 Backend" cmd /k "cd /d %~dp0 && .\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

echo Starting Vite Frontend on http://localhost:5173 ...
start "SIH26162 Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo [OK] Both servers are launching in separate windows!
echo - Frontend UI : http://localhost:5173
echo - Backend Docs: http://localhost:8000/docs
echo ====================================================
