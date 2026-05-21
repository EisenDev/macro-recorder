# Macro Automator - PowerShell Runner
# Run with: Right-click > "Run with PowerShell" (preferably as Administrator)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "=== Macro Automator ===" -ForegroundColor Cyan

# Check if Python is available
try {
    $pyVersion = python --version 2>&1
    Write-Host "[OK] Found $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Install from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "        Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create venv if missing
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate venv
& "venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

# Check for admin rights
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host ""
    Write-Host "[WARNING] Not running as Administrator." -ForegroundColor Yellow
    Write-Host "          Global keyboard/mouse capture may not work correctly." -ForegroundColor Yellow
    Write-Host "          For best results, run this script as Administrator." -ForegroundColor Yellow
    Write-Host ""
    Start-Sleep -Seconds 3
}

# Launch the app
Write-Host "[INFO] Starting Macro Automator..." -ForegroundColor Green
python app.py

deactivate
