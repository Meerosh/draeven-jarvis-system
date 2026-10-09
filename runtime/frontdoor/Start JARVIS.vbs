Set sh = CreateObject("WScript.Shell")
here = "C:\Users\Arach\Documents\Jarvis\Citadel\desktop\draeven-jarvis-system\runtime\frontdoor"
logf = "C:\Users\Arach\Documents\Jarvis\Citadel\desktop\draeven-jarvis-system\hud\jarvis-start.log"
sh.Run "cmd /c cd /d """ & here & """ && """"C:\Python314\pythonw.exe"""" -u server.py >> """ & logf & """ 2>&1", 0, False
