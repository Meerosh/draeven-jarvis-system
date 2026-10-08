@echo off
REM Draeven Port Cleanup and Service Restart Script
REM Fixes "Port 4783 is occupied" and related port conflicts
REM Root cause: serve.py had allow_reuse_address = False (now fixed)
REM Run as Administrator

setlocal enabledelayedexpansion
set LOG_FILE=C:\Users\Arach\Documents\Jarvis\Citadel\logs\draeven_startup.log

mkdir "C:\Users\Arach\Documents\Jarvis\Citadel\logs" >nul 2>&1

echo. >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"
echo DRAEVEN STARTUP - %date% %time% >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"

echo.
echo ========================================================================
echo DRAEVEN - Starting Services (with port cleanup)
echo ========================================================================
echo.

REM Step 1: Terminate any existing Draeven/Python processes
echo [1/6] Cleaning up existing processes...
echo [1/6] Cleaning up existing processes... >> "%LOG_FILE%"
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM python3.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM npm.exe >nul 2>&1
echo [OK] Processes cleaned
echo [OK] Processes cleaned >> "%LOG_FILE%"

REM Step 2: Kill any remaining processes holding service ports
echo [2/6] Releasing service ports...
echo [2/6] Releasing service ports... >> "%LOG_FILE%"

for %%P in (4783, 4719, 4091, 8090, 8091) do (
    netstat -ano 2>nul | findstr ":%%P" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   - Checking port %%P...
        echo   - Checking port %%P... >> "%LOG_FILE%"
        for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":%%P"') do (
            if "%%a" neq "" (
                echo   - Killing process %%a on port %%P
                echo   - Killing process %%a on port %%P >> "%LOG_FILE%"
                taskkill /F /PID %%a >nul 2>&1
            )
        )
    )
)
echo [OK] Ports released
echo [OK] Ports released >> "%LOG_FILE%"

REM Step 3: Wait for OS to release port (TIME_WAIT state)
echo [3/6] Waiting for OS port release (30 seconds)...
echo [3/6] Waiting for OS port release... >> "%LOG_FILE%"
timeout /t 30 /nobreak >nul 2>&1
echo [OK] Wait complete

REM Step 4: Verify Python installation
echo [4/6] Verifying Python installation...
echo [4/6] Verifying Python installation... >> "%LOG_FILE%"
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do (
        echo [OK] %%v
        echo [OK] %%v >> "%LOG_FILE%"
    )
) else (
    echo [ERROR] Python not found in PATH
    echo [ERROR] Python not found in PATH >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Step 5: Clean log files
echo [5/6] Cleaning old log files...
echo [5/6] Cleaning old log files... >> "%LOG_FILE%"
if exist "C:\Users\Arach\Documents\Jarvis\Citadel\logs\*.log" (
    del /Q "C:\Users\Arach\Documents\Jarvis\Citadel\logs\*.log" >nul 2>&1
)
echo [OK] Logs cleaned

REM Step 6: Launch Draeven HUD with retry logic
echo [6/6] Launching Draeven HUD...
echo [6/6] Launching Draeven HUD... >> "%LOG_FILE%"
cd /d "C:\Users\Arach\Documents\Jarvis\Citadel\desktop\draeven-jarvis-system\hud"

if exist "run_hud.py" (
    echo. >> "%LOG_FILE%"
    echo ✓ Starting: python run_hud.py >> "%LOG_FILE%"

    start "Draeven HUD" /D "C:\Users\Arach\Documents\Jarvis\Citadel\desktop\draeven-jarvis-system\hud" python run_hud.py

    echo.
    echo ========================================================================
    echo ✓ DRAEVEN SERVICES STARTING
    echo ========================================================================
    echo.
    echo Draeven HUD: http://127.0.0.1:4783
    echo.
    echo ✓ The service should be ready within 5-10 seconds.
    echo ✓ If you see "Address already in use" errors:
    echo   1. Wait 30 seconds and try again (OS needs time to release port)
    echo   2. Restart your computer if the issue persists
    echo   3. Check Windows Firewall: Settings ^> Allow app through firewall
    echo.
    echo Log file: %LOG_FILE%
    echo.
    pause
) else (
    echo [ERROR] run_hud.py not found
    echo [ERROR] run_hud.py not found >> "%LOG_FILE%"
    echo Expected location: C:\Users\Arach\Documents\Jarvis\Citadel\desktop\draeven-jarvis-system\hud\run_hud.py
    pause
    exit /b 1
)

echo. >> "%LOG_FILE%"
echo STARTUP COMPLETE >> "%LOG_FILE%"
