@echo off
TITLE DocLink Grounded RAG Platform Launcher
COLOR 0A

echo ====================================================================
echo               DOCLINK GROUNDED RAG PLATFORM LAUNCHER
echo ====================================================================
echo.

REM Set Workspace Root Path
set WORKSPACE_DIR=%~dp0
cd /d "%WORKSPACE_DIR%"

REM 0. Start Stable Diffusion Forge for Image / Video generation (Port 7860)
echo [0/4] Starting Stable Diffusion Forge (Port 7860)...
REM Keep START's title argument empty; start_forge.bat sets its own window title.
if exist "%WORKSPACE_DIR%start_forge.bat" (
    start "" "%ComSpec%" /k ""%WORKSPACE_DIR%start_forge.bat""
) else (
    echo [NOTICE] start_forge.bat not found - image generation will use placeholders
)

REM Wait briefly so Forge can begin initializing while other services start
timeout /t 2 /nobreak >nul

REM 1. Start Ollama Server for Gemma / Qwen models
echo [1/4] Starting Ollama Local Server (Port 11434)...
start "DocLink - Ollama Server" cmd /k "echo Starting Ollama Local Server... && ollama serve"

REM Wait 3 seconds for Ollama server to initialize
timeout /t 3 /nobreak >nul

REM Pull/verify Gemma & Qwen models in background window
start "DocLink - Ollama Model Puller" cmd /k "echo Ensuring Gemma & Qwen models are pulled... && ollama pull qwen2.5:0.5b && ollama pull gemma:2b && echo. && echo [OK] Ollama models ready! && timeout /t 5"

REM 2. Start / Check Neo4j Database
echo [2/4] Checking Neo4j Graph Database (Port 7687 / 7474)...
start "DocLink - Neo4j Database" cmd /k "echo Initializing Neo4j Graph Database... && (docker start doclink-neo4j 2>nul || docker run -d --name doclink-neo4j -p 7474:7474 -p 7687:7687 --env NEO4J_AUTH=neo4j/password neo4j:latest 2>nul || echo [NOTICE] Docker CLI not found in PATH. Please start Neo4j Desktop or local Neo4j service at bolt://localhost:7687) && echo. && echo Neo4j service check complete."

REM 3. Start FastAPI Backend Server
echo [3/4] Starting FastAPI Backend Server (Port 8000)...
start "DocLink - FastAPI Backend" cmd /k "cd /d "%WORKSPACE_DIR%" && set PYTHONPATH=%WORKSPACE_DIR%Backend;%WORKSPACE_DIR% && echo Starting FastAPI Backend on http://localhost:8000... && python -m uvicorn Backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait 3 seconds for backend initialization
timeout /t 3 /nobreak >nul

REM 4. Start React + Vite Frontend Server
echo [4/4] Starting React + Vite Frontend (Port 5173)...
start "DocLink - React Frontend" cmd /k "cd /d "%WORKSPACE_DIR%Frontend" && echo Starting Vite Dev Server on http://localhost:5173... && npm run dev"

echo.
echo ====================================================================
echo                  ALL SERVICES LAUNCHED SUCCESSFULLY!
echo ====================================================================
echo.
echo   - Frontend UI:          http://localhost:5173
echo   - Backend API Root:     http://localhost:8000
echo   - Swagger API Docs:     http://localhost:8000/docs
echo   - Health Check:         http://localhost:8000/health
echo   - Ollama Local Server:  http://localhost:11434
echo   - Forge Image API:      http://localhost:7860
echo   - Neo4j Web Console:    http://localhost:7474
echo.
echo Launching Web Application in browser...
timeout /t 4 /nobreak >nul
start http://localhost:5173

echo.
echo Press any key to exit launcher window (services will continue running).
pause >nul
