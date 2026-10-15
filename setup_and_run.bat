@echo off
title LLM Cost Autopilot - Setup & Launch
cd /d "%~dp0"
echo =========================================================
echo Setting up LLM Cost Autopilot...
echo =========================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH! Please install Python 3.11+.
    pause
    exit /b 1
)

REM Create virtual environment if not present
if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
    echo Installing dependencies...
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

echo.
echo =========================================================
echo Launching LLM Cost Autopilot API & Web Dashboard...
echo Web Dashboard: http://localhost:8000
echo Swagger Docs:  http://localhost:8000/docs
echo =========================================================
start http://localhost:8000
python run_api.py
pause
