@echo off
REM Stops anything serving JARVIS (front door :4719, Laya engine :8090), then starts fresh copies hidden.
cd /d "%~dp0"
echo %date% %time% restart requested > restart.log
for %%P in (4719 8090) do (
  for /f "tokens=5" %%I in ('netstat -ano ^| findstr /r /c:"127.0.0.1:%%P .*LISTENING"') do (
    echo stopping PID %%I on port %%P >> restart.log
    taskkill /PID %%I /T /F >> restart.log 2>&1
  )
)
timeout /t 3 /nobreak > nul
wscript "%~dp0Start JARVIS.vbs"
echo started >> restart.log
