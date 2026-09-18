@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo No se encontro el entorno virtual ^(.venv^).
    echo Corre primero setup.ps1 para prepararlo ^(ver WINDOWS.md^).
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

where ollama >nul 2>nul
if errorlevel 1 (
    echo No se encontro Ollama instalado.
    echo Instalalo desde https://ollama.com/download/windows y volve a intentar.
    pause
    exit /b 1
)

echo Verificando que Ollama este corriendo...
ollama list >nul 2>nul
if errorlevel 1 (
    echo Iniciando Ollama en segundo plano...
    start "" /min ollama serve
    timeout /t 5 /nobreak >nul
)

echo.
echo Abriendo el Generador de Propuestas Tecnicas...
echo (Se va a abrir sola una pestana del navegador. No cierres esta ventana
echo  mientras la estes usando - dejala minimizada.)
echo.

streamlit run app.py

pause
