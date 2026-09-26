# DocLink Master PowerShell Launcher
# Launches Ollama, Neo4j, FastAPI Backend, and React Frontend in separate windows

$WORKSPACE_DIR = $PSScriptRoot
Set-Location $WORKSPACE_DIR

Write-Host "====================================================================" -ForegroundColor Green
Write-Host "               DOCLINK GROUNDED RAG PLATFORM LAUNCHER               " -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Green
Write-Host ""

# 1. Start Ollama Server
Write-Host "[1/4] Starting Ollama Local Server (Port 11434)..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList '/k "echo Starting Ollama Server... && ollama serve"' -WorkingDirectory $WORKSPACE_DIR

Start-Sleep -Seconds 3

# Pull Ollama models
Start-Process cmd.exe -ArgumentList '/k "echo Pulling Ollama models... && ollama pull qwen2.5:0.5b && ollama pull gemma:2b && timeout /t 5"' -WorkingDirectory $WORKSPACE_DIR

# 2. Start Neo4j Database
Write-Host "[2/4] Checking Neo4j Graph Database (Port 7687)..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList '/k "echo Checking Neo4j... && (docker start doclink-neo4j 2>nul || docker run -d --name doclink-neo4j -p 7474:7474 -p 7687:7687 --env NEO4J_AUTH=neo4j/password neo4j:latest 2>nul || echo [NOTICE] Docker CLI not found. Start Neo4j Desktop at bolt://localhost:7687)"' -WorkingDirectory $WORKSPACE_DIR

# 3. Start FastAPI Backend
Write-Host "[3/4] Starting FastAPI Backend Server (Port 8000)..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList '/k "set PYTHONPATH=%WORKSPACE_DIR%Backend;%WORKSPACE_DIR% && echo Starting FastAPI Backend... && python -m uvicorn Backend.app.main:app --host 0.0.0.0 --port 8000 --reload"' -WorkingDirectory $WORKSPACE_DIR

Start-Sleep -Seconds 3

# 4. Start React Frontend
Write-Host "[4/4] Starting React + Vite Frontend (Port 5173)..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList '/k "echo Starting Vite Dev Server... && npm run dev"' -WorkingDirectory "$WORKSPACE_DIR\Frontend"

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "                  ALL SERVICES LAUNCHED SUCCESSFULLY!               " -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  - Frontend UI:          http://localhost:5173" -ForegroundColor White
Write-Host "  - Backend API Root:     http://localhost:8000" -ForegroundColor White
Write-Host "  - Swagger API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Ollama Local Server:  http://localhost:11434" -ForegroundColor White
Write-Host "  - Neo4j Web Console:    http://localhost:7474" -ForegroundColor White
Write-Host ""

Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"
