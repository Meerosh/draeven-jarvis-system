Set sh = CreateObject("WScript.Shell")
script = "C:\Users\Arach\my-agent\JARVIS-START.ps1"
sh.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & script & """", 0, False
