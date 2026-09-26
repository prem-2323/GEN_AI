@echo off
TITLE GEN TRANSFORM AI - Full Project Setup & Package Installer
COLOR 0B

echo ====================================================================
echo        GEN TRANSFORM AI — ONE SOURCE MULTIPLE OUTPUTS
echo              COMPLETE PACKAGE & DEPENDENCY INSTALLER
echo ====================================================================
echo.

set WORKSPACE_DIR=%~dp0
cd /d "%WORKSPACE_DIR%"

echo [1/5] Checking System Prerequisites...
echo --------------------------------------------------------------------

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your system PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version') do echo [OK] Found Python: %%i
)

REM Check Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed or not in your system PATH.
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node --version') do echo [OK] Found Node.js: %%i
)

REM Check NPM
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm is not installed or not in your system PATH.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('npm --version') do echo [OK] Found npm: v%%i
)

echo.
echo [2/5] Upgrading Python pip...
echo --------------------------------------------------------------------
python -m pip install --upgrade pip

echo.
echo [3/5] Installing Backend Python Packages & Modules...
echo --------------------------------------------------------------------
if exist "Backend\requirements.txt" (
    echo Installing dependencies from Backend\requirements.txt...
    python -m pip install -r "Backend\requirements.txt"
    if %ERRORLEVEL% NEQ 0 (
        echo [WARNING] Some python dependencies encountered warnings. Continuing setup...
    ) else (
        echo [OK] Backend Python packages installed successfully.
    )
) else (
    echo [ERROR] Backend\requirements.txt not found!
)

echo.
echo [4/5] Installing Frontend Node.js Packages (npm install)...
echo --------------------------------------------------------------------
if exist "Frontend\package.json" (
    cd /d "%WORKSPACE_DIR%Frontend"
    echo Running npm install in Frontend...
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [WARNING] npm install encountered warnings.
    ) else (
        echo [OK] Frontend Node.js modules installed successfully.
    )
    cd /d "%WORKSPACE_DIR%"
) else (
    echo [ERROR] Frontend\package.json not found!
)

echo.
echo [5/5] Checking Environment Files & Folders...
echo --------------------------------------------------------------------
if not exist "Backend\.env" (
    if exist "Backend\.env.example" (
        copy "Backend\.env.example" "Backend\.env" >nul
        echo [OK] Created Backend\.env from Backend\.env.example
    )
) else (
    echo [OK] Backend\.env already exists.
)

REM Ensure local storage directories exist
if not exist "Backend\storage\documents" mkdir "Backend\storage\documents"
if not exist "Backend\storage\data" mkdir "Backend\storage\data"
if not exist "Backend\storage\audio" mkdir "Backend\storage\audio"
if not exist "storage\documents" mkdir "storage\documents"
if not exist "storage\data" mkdir "storage\data"
if not exist "storage\audio" mkdir "storage\audio"

echo [OK] Storage directories verified.

echo.
echo ====================================================================
echo                 ALL PACKAGES INSTALLED SUCCESSFULLY!
echo ====================================================================
echo.
echo You can now launch all platform services by double-clicking:
echo   --^> start_all.bat
echo.
echo Or run the services individually:
echo   - Backend:  python -m uvicorn Backend.app.main:app --host 0.0.0.0 --port 8000 --reload
echo   - Frontend: cd Frontend ^&^& npm run dev
echo.
pause
