@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python is not installed or not on PATH.
    echo Install Python 3.11+ from https://www.python.org/downloads/windows/
    echo Then reopen this script.
    pause
    exit /b 1
)

if not exist .venv (
    echo Creating local Python environment...
    python -m venv .venv
)

call .venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if not exist .env (
    copy .env.example .env >nul
    echo Created .env from template.
)

echo.
echo Starting Draeven Jarvis API...
echo Open http://localhost:8000/docs in your browser when it starts.
echo.

python api\server.py

pause
