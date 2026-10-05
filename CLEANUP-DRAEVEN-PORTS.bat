@echo off
REM Draeven Port Cleanup and Service Restart Script
REM Fixes "Port 4783 is occupied" and related port conflicts
REM Run as Administrator

setlocal enabledelayedexpansion

echo.
echo ========================================================================
echo DRAEVEN - Force Starting Services (with aggressive cleanup)
echo ========================================================================
echo.

REM Step 1: Aggressive cleanup - Terminate all Python processes
echo [1/5] Aggressive cleanup: Terminating all Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM python3.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM npm.exe >nul 2>&1
echo [OK] Python processes terminated

REM Step 2: Check for stuck processes on service ports
echo [2/5] Checking for stuck processes on service ports...
netstat -ano | findstr ":4783" >nul 2>&1
if %errorlevel% equ 0 (
    echo Finding process on port 4783...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":4783"') do (
        echo Killing process %%a...
        taskkill /F /PID %%a >nul 2>&1
    )
)
netstat -ano | findstr ":4719" >nul 2>&1
if %errorlevel% equ 0 (
    echo Finding process on port 4719...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":4719"') do (
        echo Killing process %%a...
        taskkill /F /PID %%a >nul 2>&1
    )
)
echo [OK] Port cleanup complete

REM Step 3: Verify Python installation
echo [3/5] Verifying Python installation...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python available
) else (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
)

REM Step 4: Prepare for fresh start
echo [4/5] Preparing for fresh start...
if exist "C:\Users\Arach\Documents\Jarvis\Citadel\logs" (
    del /Q "C:\Users\Arach\Documents\Jarvis\Citadel\logs\*.log" >nul 2>&1
)
echo [OK] Log files cleaned

REM Step 5: Launch Draeven HUD
echo [5/5] Launching Draeven HUD...
cd /d "C:\Users\Arach\Documents\Jarvis\Citadel\desktop\jarvis-hud"
if exist "run_hud.py" (
    start "Draeven HUD" python run_hud.py
    echo.
    echo ========================================================================
    echo ✓ Draeven services launched
    echo ========================================================================
    echo.
    echo Draeven HUD should be accessible at: http://127.0.0.1:4783
    echo.
    echo If the service fails to start, check:
    echo 1. C:\Users\Arach\Documents\Jarvis\Citadel\logs\preview-server.log
    echo 2. C:\Users\Arach\Documents\Jarvis\Citadel\desktop\jarvis-hud\run_hud.py
    echo 3. Ensure port 4783 is not blocked by firewall
    echo.
    pause
) else (
    echo [ERROR] run_hud.py not found
    pause
    exit /b 1
)
