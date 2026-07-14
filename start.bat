@echo off
chcp 65001 >nul
title Learning System
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
)
set "PYTHON=.venv\Scripts\python.exe"
echo.
echo  Learning System (Python / SQL / C++ / R)
echo  Starting... please wait, browser will open automatically.
echo  Close this window to stop the server.
echo.
"%PYTHON%" -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false
pause
