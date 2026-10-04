@echo off
REM One-time install of the REAL Laya decision model for JARVIS.
REM Downloads PyTorch + the model (~2-3 GB total). Takes several minutes.
cd /d "%~dp0"
echo Installing laya (open-source, Apache 2.0) ...
python -m pip install --upgrade laya
if %errorlevel% neq 0 (
  echo.
  echo INSTALL FAILED. Copy the red error text above and paste it to Claude.
  pause & exit /b 1
)
echo.
echo Running self-test (first run downloads the model)...
python laya_selftest.py > laya_selftest_result.txt 2>&1
type laya_selftest_result.txt
echo.
echo Result saved to laya_selftest_result.txt - Claude can read it from here.
pause
