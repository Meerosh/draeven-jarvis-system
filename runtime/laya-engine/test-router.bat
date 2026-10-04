@echo off
cd /d "%~dp0"
python jarvis_router.py --test > router_test_log.txt 2>&1
