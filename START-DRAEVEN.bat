@echo off
REM Draeven HUD - Simple Startup Script
REM This is the recommended way to start Draeven after the port fix
REM The fix in serve.py now allows immediate restarts via socket reuse

setlocal enabledelayedexpansion

title Draeven HUD Server

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3 and add it to your PATH
    pause
    exit /b 1
)

REM Navigate to HUD directory
cd /d "C:\Users\Arach\Documents\Jarvis\Citadel\desktop\jarvis-hud"
if not exist "run_hud.py" (
    echo ERROR: run_hud.py not found in:
    echo %CD%
    echo Please ensure Draeven is properly installed
    pause
    exit /b 1
)

REM Start the server
echo.
echo Draeven HUD Starting...
echo.
python run_hud.py

REM If we reach here, the user pressed Ctrl+C or there was an error
if %errorlevel% neq 0 (
    echo.
    echo Server stopped with error code %errorlevel%
    pause
)
