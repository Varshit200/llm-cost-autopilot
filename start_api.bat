@echo off
title LLM Cost Autopilot - API Service
cd /d "%~dp0"
echo ===================================================
echo Starting LLM Cost Autopilot API on port 8000...
echo Swagger UI: http://localhost:8000/docs
echo ===================================================
call .venv\Scripts\activate.bat
python run_api.py
pause
