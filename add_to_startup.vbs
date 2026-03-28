Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get Startup folder path
startupPath = shell.SpecialFolders("Startup")
shortcutPath = startupPath & "\McDonaldMonitor.lnk"

' The silent VBS path
vbsPath = "D:\coding projects\McDonald monitor Project\start_silent.vbs"

' Create the shortcut
Set shortcut = shell.CreateShortcut(shortcutPath)
shortcut.TargetPath = "wscript.exe"
shortcut.Arguments = """" & vbsPath & """"
shortcut.WorkingDirectory = "D:\coding projects\McDonald monitor Project"
shortcut.Description = "Auto Start McDonald Monitor Silently"
shortcut.Save

WScript.Echo "Success: McDonald Monitor has been added to Startup!"
