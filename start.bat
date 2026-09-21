@echo off
title TeleStream Instant — Kavimo Edition
cd /d "%~dp0"

echo ========================================================
echo   TeleStream Instant (Kavimo Edition) Running...
echo ========================================================
echo.

if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe bot.py
) else if exist ..\TelegramStreamer\venv\Scripts\python.exe (
    ..\TelegramStreamer\venv\Scripts\python.exe bot.py
) else (
    python bot.py
)

if errorlevel 1 (
    echo.
    echo [!] Server exited with an error.
    pause
)
