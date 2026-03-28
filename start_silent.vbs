Set WshShell = CreateObject("WScript.Shell")
' 0 = Hide the window, 1 = Show the window normal
' Run the batch file in hidden mode (0)
WshShell.Run chr(34) & "D:\coding projects\McDonald monitor Project\start_app.bat" & Chr(34), 0
Set WshShell = Nothing
