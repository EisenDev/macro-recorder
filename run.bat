@echo off
title Macro Automator
cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install / upgrade dependencies
echo [INFO] Installing dependencies...
pip install -r requirements.txt --quiet

:: Warn about admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] You are NOT running as Administrator.
    echo           Global keyboard/mouse capture (pynput) may not work correctly.
    echo           Right-click run.bat and select "Run as administrator" for best results.
    echo.
    timeout /t 3 >nul
)

:: Launch the app
echo [INFO] Starting Macro Automator...
python app.py

deactivate
