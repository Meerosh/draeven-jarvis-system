Set sh = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
folder = fs.GetParentFolderName(WScript.ScriptFullName)
sh.Run """C:\Python314\pythonw.exe"" """ & folder & "\launch.pyw""", 0, False
