@echo off
title Gen-Transform-AI Launcher
color 0B

echo ===============================================================
echo                GEN-TRANSFORM-AI PLATFORM
echo ===============================================================
echo.
echo [1/2] Starting FastAPI Backend (Port 8000)...
start "Gen-Transform-AI Backend" cmd /k "cd /d %~dp0Backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting Vite Frontend (Port 3000)...
start "Gen-Transform-AI Frontend" cmd /k "cd /d %~dp0Frontend && npm run dev"

echo.
echo ===============================================================
echo   All servers launched successfully in separate windows!
echo.
echo   - Frontend:  http://localhost:3000
echo   - Backend:   http://localhost:8000
echo   - API Docs:  http://localhost:8000/docs
echo   - Temp Logs: http://localhost:8000/api/temp
echo ===============================================================
echo.
echo Press any key to exit this launcher window...
pause >nul
