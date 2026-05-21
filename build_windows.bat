@echo off
title Building Macro Automator...
cd /d "%~dp0"

echo ============================================
echo   Macro Automator - Windows EXE Builder
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install from https://www.python.org/downloads/
    pause & exit /b 1
)

:: Create/activate venv
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat

:: Install dependencies + PyInstaller
echo [INFO] Installing dependencies...
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

:: Build the exe
echo.
echo [INFO] Building EXE (this may take a minute)...
pyinstaller --onefile ^
    --windowed ^
    --name "MacroAutomator" ^
    --icon NONE ^
    --add-data "." ^
    app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed. See output above.
    pause & exit /b 1
)

echo.
echo ============================================
echo   BUILD SUCCESSFUL!
echo   Find your EXE at: dist\MacroAutomator.exe
echo ============================================
echo.
echo NOTE: Run the EXE as Administrator for full
echo       global keyboard/mouse capture to work.
pause
