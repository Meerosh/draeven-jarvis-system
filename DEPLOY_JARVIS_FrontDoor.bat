@echo off
REM JARVIS Front Door v2 - Windows Deployment Script
REM Run this script to deploy and start the upgraded Front Door

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo JARVIS Front Door v2 - Deployment & Startup
echo ============================================================
echo.

REM Set deployment directory
set DEPLOY_DIR=C:\Users\Arach\my-agent\jarvis-frontdoor
set REPO_DIR=C:\Users\Arach\Documents\Jarvis\Citadel\desktop\draeven-jarvis-system

REM Check if repository exists
if not exist "%REPO_DIR%" (
    echo ERROR: Repository not found at %REPO_DIR%
    echo Please clone the repository first
    pause
    exit /b 1
)

echo [1/5] Updating repository...
cd /d "%REPO_DIR%"
git pull origin main
if errorlevel 1 (
    echo ERROR: Failed to pull latest code
    pause
    exit /b 1
)
echo [OK] Repository updated

REM Copy updated files to deployment directory
echo.
echo [2/5] Copying updated files to deployment directory...
if not exist "%DEPLOY_DIR%" mkdir "%DEPLOY_DIR%"
xcopy /E /I /Y "%REPO_DIR%\runtime\frontdoor\*" "%DEPLOY_DIR%\"
if errorlevel 1 (
    echo ERROR: Failed to copy files
    pause
    exit /b 1
)
echo [OK] Files copied to %DEPLOY_DIR%

REM Create logs directory
echo.
echo [3/5] Creating logs directory...
if not exist "%DEPLOY_DIR%\logs" mkdir "%DEPLOY_DIR%\logs"
echo [OK] Logs directory ready

REM Verify Python syntax
echo.
echo [4/5] Verifying Python syntax...
python -m py_compile "%DEPLOY_DIR%\server.py" "%DEPLOY_DIR%\provider_gateway.py"
if errorlevel 1 (
    echo ERROR: Python syntax check failed
    pause
    exit /b 1
)
echo [OK] Python syntax verified

REM Configure environment variables (optional)
echo.
echo [5/5] Environment Configuration
echo.
echo Setting JARVIS environment variables (optional):
echo   - JARVIS_FRONTDOOR_PORT: 4719 (default)
echo   - JARVIS_VAULT: C:\Users\Arach\Documents\Jarvis
echo   - JARVIS_PENDING_TTL: 1800 seconds (30 min)
echo.
echo Default values will be used if not set.
echo To customize, set environment variables before running server.

REM Start the server
echo.
echo ============================================================
echo Starting JARVIS Front Door v2...
echo ============================================================
echo.
echo Server will be available at: http://127.0.0.1:4719
echo Logs will be written to: %DEPLOY_DIR%\logs\
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%DEPLOY_DIR%"
python server.py

pause
