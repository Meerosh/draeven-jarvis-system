' Starts the JARVIS Laya engine hidden (no window). Safe to run twice:
' a second copy sees port 8090 in use and exits. Status: laya_engine_status.txt
Set sh = CreateObject("WScript.Shell")
dir = "C:\Users\Arach\my-agent\laya-engine"
sh.CurrentDirectory = dir
sh.Run "cmd /c python -u laya_engine_server.py > laya_engine.log 2>&1", 0, False
