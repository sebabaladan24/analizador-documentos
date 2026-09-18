# setup.ps1 - Prepara el ambiente local para el Generador de Propuestas Técnicas.
# Ejecutar desde PowerShell, parado en la carpeta del proyecto (donde está este archivo).
#
# Si PowerShell bloquea la ejecución de scripts, corré antes (en esa misma terminal):
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

$ErrorActionPreference = "Stop"

Write-Host "== 1. Verificando Ollama ==" -ForegroundColor Cyan
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "Ollama no está instalado."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Instalando Ollama con winget..."
        winget install --id Ollama.Ollama -e
        Write-Host ""
        Write-Host "Cerrá y volvé a abrir esta terminal de PowerShell (para que el PATH se actualice)"
        Write-Host "y volvé a correr este script."
        exit 0
    } else {
        Write-Host "winget no está disponible en este equipo. Descargá e instalá Ollama a mano desde:"
        Write-Host "  https://ollama.com/download/windows"
        Write-Host "Después de instalarlo, volvé a correr este script."
        exit 1
    }
}
Write-Host "Ollama encontrado: $(ollama --version)"

Write-Host ""
Write-Host "== 2. Descargando modelos (puede tardar bastante según tu conexión) ==" -ForegroundColor Cyan
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text

Write-Host ""
Write-Host "== 3. Verificando Python ==" -ForegroundColor Cyan
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python no está instalado o no está en el PATH."
    Write-Host "Descargalo desde https://www.python.org/downloads/"
    Write-Host "IMPORTANTE al instalar: marcar la casilla 'Add python.exe to PATH'."
    Write-Host "Después de instalarlo, volvé a correr este script."
    exit 1
}
Write-Host "Python encontrado: $(python --version)"

Write-Host ""
Write-Host "== 4. Creando entorno virtual (.venv) ==" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1

Write-Host ""
Write-Host "== 5. Instalando dependencias de Python ==" -ForegroundColor Cyan
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host ""
Write-Host "== Listo ==" -ForegroundColor Green
Write-Host "Para arrancar la app, en una terminal parada en esta carpeta:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  streamlit run app.py"
Write-Host ""
Write-Host "IMPORTANTE: antes de generar propuestas reales, completá los archivos en" -ForegroundColor Yellow
Write-Host "servicios\*.md con los datos reales de la empresa (están marcados 'COMPLETAR CON DATOS REALES')." -ForegroundColor Yellow
