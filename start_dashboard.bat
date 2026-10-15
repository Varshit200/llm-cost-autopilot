@echo off
title LLM Cost Autopilot - Dashboard
cd /d "%~dp0"
echo ===================================================
echo Starting LLM Cost Autopilot Streamlit Dashboard...
echo URL: http://localhost:8501
echo ===================================================
call .venv\Scripts\activate.bat
python run_dashboard.py
pause
