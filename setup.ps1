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
Write-Host "== 6. Creando acceso directo en el escritorio ==" -ForegroundColor Cyan
try {
    $proyectoDir = (Get-Location).Path
    $vbsPath = Join-Path $proyectoDir "iniciar_app.vbs"
    $escritorio = [Environment]::GetFolderPath("Desktop")
    $accesoDirecto = Join-Path $escritorio "Generador de Propuestas.lnk"

    $wsh = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut($accesoDirecto)
    $shortcut.TargetPath = "$env:SystemRoot\System32\wscript.exe"
    $shortcut.Arguments = "`"$vbsPath`""
    $shortcut.WorkingDirectory = $proyectoDir
    $shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,1"
    $shortcut.Description = "Generador de Propuestas Técnicas"
    $shortcut.Save()

    Write-Host "Acceso directo creado: $accesoDirecto" -ForegroundColor Green
} catch {
    Write-Host "No se pudo crear el acceso directo automáticamente ($($_.Exception.Message))." -ForegroundColor Yellow
    Write-Host "Podés crearlo a mano: click derecho en iniciar_app.vbs -> Crear acceso directo," -ForegroundColor Yellow
    Write-Host "y arrastrarlo al escritorio." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "== Listo ==" -ForegroundColor Green
Write-Host "Ya tenés un ícono 'Generador de Propuestas' en el escritorio: doble clic ahí"
Write-Host "abre la app en su propia ventana, sin necesidad de terminal."
Write-Host ""
Write-Host "(Alternativa para debug: .\iniciar.bat en esta carpeta abre lo mismo pero con"
Write-Host " la consola visible, útil si algo falla y necesitás ver el error.)"
Write-Host ""
Write-Host "IMPORTANTE: antes de generar propuestas reales, completá los archivos en" -ForegroundColor Yellow
Write-Host "servicios\*.md con los datos reales de la empresa (están marcados 'COMPLETAR CON DATOS REALES')." -ForegroundColor Yellow
