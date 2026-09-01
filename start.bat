@echo off
chcp 65001 >nul
title Learning System
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if not exist ".venv\Scripts\python.exe" (
    echo.
    echo [ERROR] Failed to create virtual environment.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo and make sure "python" is on PATH (not the Microsoft Store stub).
    pause
    exit /b 1
  )
)
set "PYTHON=.venv\Scripts\python.exe"
echo.
echo  Learning System (Python / SQL / C++ / R)
echo  Starting... please wait, browser will open automatically.
echo  Close this window to stop the server.
echo.
REM 自动找空闲端口（8511 起，与心理系统 8501 错开）；headless false 确保自动打开浏览器
for /f %%p in ('"%PYTHON%" scripts\find_port.py') do set "PORT=%%p"
"%PYTHON%" -m streamlit run app.py --server.port %PORT% --server.headless false --server.fileWatcherType none --browser.gatherUsageStats false
pause
