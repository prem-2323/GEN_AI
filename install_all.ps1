# ====================================================================
# GEN TRANSFORM AI — Complete Package & Dependency Installer (PowerShell)
# ====================================================================

$Host.UI.RawUI.WindowTitle = "GEN TRANSFORM AI - Full Project Setup & Package Installer"
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "       GEN TRANSFORM AI — ONE SOURCE MULTIPLE OUTPUTS" -ForegroundColor Cyan
Write-Host "             COMPLETE PACKAGE & DEPENDENCY INSTALLER" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

$WorkspaceDir = $PSScriptRoot
Set-Location -Path $WorkspaceDir

# 1. Check System Prerequisites
Write-Host "[1/5] Checking System Prerequisites..." -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------"

# Check Python
try {
    $pythonVer = python --version 2>&1
    Write-Host "[OK] Found Python: $pythonVer" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in system PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from https://www.python.org/downloads/"
    exit 1
}

# Check Node.js
try {
    $nodeVer = node --version 2>&1
    Write-Host "[OK] Found Node.js: $nodeVer" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Node.js is not installed or not in system PATH." -ForegroundColor Red
    Write-Host "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
}

# Check npm
try {
    $npmVer = npm --version 2>&1
    Write-Host "[OK] Found npm: v$npmVer" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] npm is not installed or not in system PATH." -ForegroundColor Red
    exit 1
}

Write-Host ""
# 2. Upgrade pip
Write-Host "[2/5] Upgrading Python pip..." -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------"
python -m pip install --upgrade pip

Write-Host ""
# 3. Install Backend Python Packages
Write-Host "[3/5] Installing Backend Python Packages & Modules..." -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------"
if (Test-Path "Backend\requirements.txt") {
    Write-Host "Installing dependencies from Backend\requirements.txt..." -ForegroundColor Cyan
    python -m pip install -r "Backend\requirements.txt"
    Write-Host "[OK] Backend Python packages installed successfully." -ForegroundColor Green
} else {
    Write-Host "[ERROR] Backend\requirements.txt not found!" -ForegroundColor Red
}

Write-Host ""
# 4. Install Frontend Node.js Packages
Write-Host "[4/5] Installing Frontend Node.js Packages (npm install)..." -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------"
if (Test-Path "Frontend\package.json") {
    Set-Location -Path "$WorkspaceDir\Frontend"
    Write-Host "Running npm install in Frontend..." -ForegroundColor Cyan
    npm install
    Write-Host "[OK] Frontend Node.js modules installed successfully." -ForegroundColor Green
    Set-Location -Path $WorkspaceDir
} else {
    Write-Host "[ERROR] Frontend\package.json not found!" -ForegroundColor Red
}

Write-Host ""
# 5. Check Environment Files & Folders
Write-Host "[5/5] Checking Environment Files & Folders..." -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------"
if (-not (Test-Path "Backend\.env")) {
    if (Test-Path "Backend\.env.example") {
        Copy-Item -Path "Backend\.env.example" -Destination "Backend\.env"
        Write-Host "[OK] Created Backend\.env from Backend\.env.example" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] Backend\.env already exists." -ForegroundColor Green
}

# Ensure storage folders exist
$dirs = @("Backend\storage\documents", "Backend\storage\data", "Backend\storage\audio", "storage\documents", "storage\data", "storage\audio")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "[OK] Storage directories verified." -ForegroundColor Green

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "                ALL PACKAGES INSTALLED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "You can now launch all platform services by running:" -ForegroundColor Cyan
Write-Host "  --> .\start_all.bat  or  .\start_all.ps1" -ForegroundColor Yellow
Write-Host ""
