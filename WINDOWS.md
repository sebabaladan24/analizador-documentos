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
   el entorno virtual de Python, instala las dependencias, y **crea un ícono
   "Generador de Propuestas" en tu escritorio**. Puede pedirte cerrar y volver a
   abrir la terminal una vez (para que el PATH tome el instalador de Ollama) —
   en ese caso, volvé a correr `.\setup.ps1`.

## Uso diario: como si fuera una aplicación

Después de correr `setup.ps1` una vez, no hace falta abrir PowerShell nunca más:

- Doble clic en el ícono **"Generador de Propuestas"** del escritorio.
- Se abre una ventana propia (sin pestañas ni barra de direcciones de
  navegador — Chrome o Edge en "modo app") con la herramienta, como si fuera
  una aplicación de escritorio normal.
- Por atrás se abre además una ventanita de consola minimizada (el "motor" —
  Ollama + el servidor de la app). Es normal, no hace falta tocarla; queda
  minimizada en la barra de tareas.

**Para cerrar del todo**: cerrar la ventana de la app no alcanza para apagar el
servidor de atrás (queda corriendo en la ventanita minimizada, por si querés
volver a abrir la app sin esperar que arranque de nuevo). Si querés apagarlo
por completo, buscá esa ventana minimizada en la barra de tareas y cerrala
(o Administrador de tareas → buscar "streamlit"/"python" → Finalizar tarea).

Si el ícono del escritorio no se creó solo (`setup.ps1` avisa si falló), se
puede crear a mano:

1. Click derecho sobre `iniciar_app.vbs` → **Crear acceso directo**.
2. Cortá ese acceso directo (`Ctrl+X`) y pegalo (`Ctrl+V`) en el Escritorio.
3. Si querés cambiarle el nombre, click derecho → **Cambiar nombre** → ej.
   "Generador de Propuestas".

### Si algo falla: `iniciar.bat`

`iniciar_app.vbs` no muestra ninguna consola, así que si algo sale mal no vas
a ver el error. Para eso está `iniciar.bat` (en la misma carpeta): hace
exactamente lo mismo pero con la consola visible, mostrando los logs y
cualquier error en pantalla — útil para diagnosticar problemas.

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
- **El ícono del escritorio abre una pestaña de navegador normal (con barra de
  direcciones), no una "ventana de app"**: no se encontró Chrome ni Edge en las
  rutas habituales de instalación — igual funciona, solo que con la interfaz
  normal del navegador en vez del modo app.
- **Doble clic en el ícono y no pasa nada visible**: esperá unos 10-15
  segundos (Ollama + Streamlit tardan en levantar la primera vez). Si después
  de eso sigue sin abrir nada, corré `iniciar.bat` en su lugar para ver el
  error en pantalla.
