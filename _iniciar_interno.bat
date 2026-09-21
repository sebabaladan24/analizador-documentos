@echo off
REM No corras este archivo directamente: es el motor interno de iniciar_app.vbs
REM (que lo lanza oculto). Para uso normal, doble clic en iniciar_app.vbs o en
REM el acceso directo del escritorio.
REM Si algo falla y necesitás ver los errores, usá iniciar.bat en su lugar,
REM que corre lo mismo con la consola visible.

cd /d "%~dp0"

call .venv\Scripts\activate.bat

where ollama >nul 2>nul
if not errorlevel 1 (
    ollama list >nul 2>nul
    if errorlevel 1 (
        start "" /min ollama serve
        timeout /t 5 /nobreak >nul
    )
)

start "Generador de Propuestas - servidor (no cerrar)" /min cmd /c "streamlit run app.py --server.headless true"

timeout /t 6 /nobreak >nul

set URL=http://localhost:8501

where chrome >nul 2>nul
if not errorlevel 1 (
    start "" chrome --app=%URL% --window-size=1280,800
    exit /b 0
)
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" --app=%URL% --window-size=1280,800
    exit /b 0
)
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" --app=%URL% --window-size=1280,800
    exit /b 0
)
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" --app=%URL% --window-size=1280,800
    exit /b 0
)
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" --app=%URL% --window-size=1280,800
    exit /b 0
)

REM Fallback: ningún Chrome/Edge encontrado en las rutas típicas, abrir con
REM el navegador default (con pestañas y barra de direcciones normales).
start "" %URL%
