' Lanzador "app-like": corre _iniciar_interno.bat sin mostrar ninguna
' ventana de consola, y ese .bat abre el Generador de Propuestas en una
' ventana de navegador en modo app (sin pestañas ni barra de direcciones).
'
' Doble clic acá (o en el acceso directo del escritorio que crea setup.ps1)
' para abrir la herramienta como si fuera una aplicación de escritorio.

Dim shell, carpeta
Set shell = CreateObject("WScript.Shell")
carpeta = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = carpeta
shell.Run """" & carpeta & "\_iniciar_interno.bat""", 0, False
