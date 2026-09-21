# Generador de Propuestas Técnicas

Herramienta 100% local (sin llamadas a servicios externos) que:

1. Ingesta un documento técnico de un cliente (requisitos, pliego, especificación).
2. Cruza sus requisitos contra un catálogo propio de servicios (`/servicios/*.md`).
3. Genera un borrador de propuesta técnica, indicando qué servicio cubre cada
   requisito y señalando explícitamente los que no tienen cobertura clara.

También conserva la funcionalidad original de resumir y comparar documentos
sueltos.

## Instalación en Windows

Ver [`WINDOWS.md`](WINDOWS.md) — incluye un script automático (`setup.ps1`) y
el paso a paso manual (instalar Ollama, descargar modelos, crear el entorno
virtual).

## Requisitos previos (Linux/macOS o referencia general)

- [Ollama](https://ollama.com) corriendo localmente, con los modelos:
  ```bash
  ollama pull qwen2.5:7b-instruct
  ollama pull nomic-embed-text
  ```
  (`qwen2.5:7b-instruct` o `mistral:7b-instruct` para el modelo de razonamiento/extracción
  JSON; `llama3.2:3b` es más liviano pero rinde peor en la extracción estructurada — ver
  `CLAUDE.md`, sección 5, para el detalle de esta decisión).
- Python 3.11+.

## Instalación

```bash
pip install -r requirements.txt
```

## Completar el catálogo de servicios

Los archivos en `servicios/*.md` (excepto `_template.md`) son **placeholders** con
specs de ejemplo marcadas `X` o "COMPLETAR CON DATOS REALES". Hay que editarlos con
los datos reales de la empresa antes de generar propuestas — un modelo de este
tamaño no va a inventar SLAs correctos, y tampoco debe hacerlo.

Para agregar un servicio nuevo, dos formas:

- A mano: copiar `servicios/_template.md` y completar sus secciones (Descripción,
  Especificaciones técnicas, SLA, Cuándo ofrecerlo / Cuándo NO ofrecerlo).
- Asistido: pestaña "Catálogo de servicios" de la app — subís un PDF/Word/folleto
  que ya tengas del servicio, la IA arma un borrador con esas mismas secciones, y
  lo revisás/editás antes de guardarlo. Los campos que el documento no dice
  explícitamente quedan marcados "[Verificar...]" en vez de inventarse.

## Uso

```bash
streamlit run app.py
```

1. Catálogo de servicios: pestaña "Catálogo de servicios" (asistido por IA, ver
   arriba) o editar `servicios/*.md` a mano y tocar "Cargar / recargar catálogo
   de servicios" en la barra lateral.
2. Pestaña "Cargar documento": subir el documento del cliente.
3. Pestaña "Generar propuesta": elegir el documento, extraer requisitos,
   revisarlos/editarlos, generar la propuesta y exportarla a Word.
4. Pestaña "Documentos PMI": elegir el documento y generar, de a uno, los
   documentos base de arranque (Acta de Inicio, Documento de Formulación,
   Gestión del Cambio, Lecciones Aprendidas, Documento de Cierre). Cada uno
   es editable antes de exportarlo a Word; las secciones sin información
   suficiente en el documento del cliente quedan como "[Completar]".

## Tests

```bash
pytest
```

Los tests cubren únicamente las partes puras del pipeline (chunking, parseo de
secciones, validación de JSON, exportación a Word) — no requieren Ollama ni
Chroma corriendo.

## Alcance

Ver `CLAUDE.md` para el detalle de arquitectura, decisiones y qué queda
explícitamente fuera de alcance (multiusuario, pricing automático,
integración con CRM).
