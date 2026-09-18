# Instalación en Windows

## Opción rápida: script automático

1. Descomprimí el proyecto en una carpeta, por ejemplo `C:\Proyectos\analizador-documentos`.
2. Abrí PowerShell parado en esa carpeta (click derecho dentro de la carpeta en el
   Explorador → "Abrir en Terminal", o `cd` manual).
3. Si PowerShell bloquea la ejecución de scripts, corré primero:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```
4. Corré:
   ```powershell
   .\setup.ps1
   ```
   El script instala Ollama (si falta), descarga los dos modelos necesarios, crea
   el entorno virtual de Python e instala las dependencias. Puede pedirte cerrar y
   volver a abrir la terminal una vez (para que el PATH tome el instalador de
   Ollama) — en ese caso, volvé a correr `.\setup.ps1`.

Al terminar, para arrancar la app:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Se abre solo en el navegador en `http://localhost:8501`.

## Arrancarlo con doble clic (después de la instalación inicial)

Una vez que corriste `setup.ps1` al menos una vez, no hace falta volver a abrir
PowerShell. En la carpeta del proyecto hay un archivo `iniciar.bat`:

- Doble clic sobre `iniciar.bat` → activa el entorno, se asegura de que Ollama
  esté corriendo, y abre la app sola en el navegador.
- Se abre una ventana negra de consola (es normal, ahí se ven los logs) —
  dejala minimizada mientras usás la app; cerrarla apaga la app.

### Crear un acceso directo en el escritorio (opcional)

1. Click derecho sobre `iniciar.bat` → **Crear acceso directo**.
2. Cortá ese acceso directo (`Ctrl+X`) y pegalo (`Ctrl+V`) en el Escritorio.
3. Si querés cambiarle el nombre, click derecho → **Cambiar nombre** → ej.
   "Generador de Propuestas".

Con eso queda un ícono en el escritorio para abrir la herramienta con un solo
doble clic, sin terminal ni comandos.

## Opción manual (si el script falla o preferís hacerlo paso a paso)

### 1. Instalar Ollama

Descargar e instalar desde https://ollama.com/download/windows (instalador normal,
"Next, Next, Finish"). Se instala como servicio, no hace falta dejar nada abierto.

Verificar en PowerShell:
```powershell
ollama --version
```

### 2. Descargar los modelos

```powershell
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
```

Esto baja unos cuantos GB — puede tardar. Con 8-16GB de RAM sin GPU corren bien,
pero cada propuesta puede tardar 1-3 minutos en generarse (es normal, no es un
flujo en tiempo real).

### 3. Instalar Python

Si no lo tenés: https://www.python.org/downloads/ — al instalar, **marcar la
casilla "Add python.exe to PATH"** en la primera pantalla del instalador.

Verificar:
```powershell
python --version
```

### 4. Crear el entorno virtual e instalar dependencias

Parado en la carpeta del proyecto:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Completar el catálogo de servicios

Antes de generar propuestas reales, editar los archivos en `servicios\*.md`
(Housing, Nube Empresarial, Backup, Conectividad, Nube Híbrida) reemplazando los
valores marcados "COMPLETAR CON DATOS REALES" por las specs/SLA reales de la
empresa. Sin esto el sistema no tiene nada real contra qué comparar.

### 6. Correr la app

```powershell
streamlit run app.py
```

Las próximas veces, solo hace falta repetir el paso 6 (activando antes el venv
con `.\.venv\Scripts\Activate.ps1` si abrís una terminal nueva) — Ollama queda
corriendo como servicio en segundo plano.

## Problemas comunes

- **`ollama` no se reconoce como comando**: cerrá y volvé a abrir la terminal
  después de instalar Ollama (el instalador actualiza el PATH, pero las terminales
  ya abiertas no se enteran).
- **La descarga de un modelo se traba o falla**: volvé a correr el mismo
  `ollama pull ...`, retoma donde quedó.
- **Error de "execution policy" al correr `setup.ps1`**: ver el paso 3 de la
  opción rápida arriba.
- **Streamlit no abre el navegador solo**: entrá manualmente a
  `http://localhost:8501`.
