@echo off
title TeleStream — Setup
cd /d "%~dp0"

echo ========================================================
echo   TeleStream Instant (Kavimo Edition) Setup
echo ========================================================
echo.

if not exist venv (
    echo [*] Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [!] Failed to create venv with global python, trying local venv...
    )
)

echo [*] Installing requirements...
if exist venv\Scripts\pip.exe (
    venv\Scripts\pip.exe install --upgrade pip
    venv\Scripts\pip.exe install -r requirements.txt
) else (
    pip install -r requirements.txt
)

echo.
echo [+] Setup complete!
echo [+] Edit config.json if needed, then run start.bat
echo.
pause
