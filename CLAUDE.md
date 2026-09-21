# analizador-documentos — contexto para Claude Code

Generador de propuestas técnicas 100% local. Evoluciona una herramienta que
originalmente solo resumía/comparaba documentos sueltos hacia un sistema que
cruza los requisitos de un documento de cliente contra un catálogo propio de
servicios (Housing, Nube Empresarial, Backup, Conectividad, Nube Híbrida,
etc.) y genera un borrador de propuesta técnica ajustada.

Todo corre 100% local (Ollama + Chroma), sin llamadas a servicios externos:
los documentos de cliente son confidenciales.

## Por qué es distinto a "resumir un documento"

Resumir es una tarea de una sola fuente. Generar una propuesta ajustada es una
tarea de dos fuentes que hay que cruzar sin confundirlas:

- **Fuente A** (`coleccion_clientes`): documentos que sube el PM, uno por
  cliente/proyecto — de acá se extraen los requisitos.
- **Fuente B** (`coleccion_servicios`): el catálogo propio, cargado una sola
  vez desde `/servicios/*.md` y reutilizado en todas las propuestas.

Por eso las dos colecciones de Chroma están siempre separadas — nunca se
mezclan en una sola búsqueda.

## Stack

Python 3.11 · Streamlit (UI) · ChromaDB (persistente, en `data/chroma/`,
gitignored) · Ollama (LLM + embeddings, todo local) · `python-docx`
(exportación) · `pypdf` / `python-docx` (lectura de PDF/DOCX de cliente) ·
`python-frontmatter` (parseo de `/servicios/*.md`).

## Estructura

- `app.py` — UI de Streamlit (6 pestañas + barra lateral).
- `src/config.py` — paths, nombres de modelo y de colecciones. Todos los
  parámetros ajustables van acá (con override por variable de entorno), nunca
  hardcodeados en otro módulo.
- `src/vectorstore.py` — único punto de acceso a Chroma. Los embeddings se
  calculan a mano con Ollama (`Client.embed()`, en **un solo pedido en lote**
  para toda la lista de fragmentos — no uno por fragmento, eso es la
  diferencia entre segundos y minutos con un documento de varias páginas) y
  se pasan directo a Chroma (`add`/`query` con `embeddings=`), no se usa el
  mecanismo de `embedding_function` de chromadb.
- `src/texto.py` — `chunkear_texto()`, compartido por `ingesta.py` y
  `servicios_loader.py`. Existe aparte porque las dos cosas lo necesitan: sin
  trocear un texto largo antes de mandarlo a embeddings, Ollama tira
  `the input length exceeds the context length` en vez de indexarlo.
- `src/ingesta.py` — extracción de texto (PDF/DOCX/TXT/MD), chunking (vía
  `texto.chunkear_texto`) e indexado de documentos de **cliente** en
  `coleccion_clientes`.
- `src/servicios_loader.py` — parseo de `/servicios/*.md` (frontmatter +
  secciones `##`) e indexado en `coleccion_servicios`. Cada sección se
  trocea con `texto.chunkear_texto` antes de indexarla (una sección puede
  ser larga, sobre todo si viene de `servicios_extraccion.py`). Recarga
  completa (`reemplazar=True` por default) para que el catálogo indexado
  siempre refleje el estado actual de los archivos.
- `src/servicios_extraccion.py` — camino alternativo para poblar el catálogo:
  a partir de un PDF/Word/folleto suelto que el usuario ya tenga, extrae un
  borrador de ficha de servicio en JSON (mismos 5 campos que la plantilla) y
  lo convierte a markdown con `borrador_a_markdown()`. A diferencia de
  `servicios_loader.py` (que solo lee `.md` ya estructurados, sin ninguna
  IA de por medio), acá el modelo sí interpreta texto libre — por eso el
  resultado NUNCA se guarda directo: `app.py` (pestaña "Catálogo de
  servicios") lo muestra editable primero, y recién al tocar "Guardar" se
  escribe a `/servicios/*.md` y se reindexa. Los campos que el documento
  fuente no menciona con claridad quedan como
  `"[Verificar - no especificado en el documento fuente]"` en vez de
  inventarse.
- `src/llm.py` — wrapper sobre Ollama. `chat()` para prosa libre;
  `generar_json()` fuerza `format="json"` y reintenta pasándole el error de
  parseo al modelo si la respuesta no es JSON válido. Estos dos modos están
  deliberadamente separados (ver sección 5 de la guía original: un modelo de
  7B con `format="json"` sigue instrucciones de formato mucho mejor que uno
  de 3B). Usa un `ollama.Client` propio con `timeout=config.LLM_TIMEOUT_SEGUNDOS`
  (900s por default) — las funciones sueltas del paquete (`ollama.chat`) usan
  un cliente con `timeout=None`, que en httpx significa esperar para
  siempre; sin esto, un Ollama trabado dejaba la UI "cargando" sin ningún
  error. `vectorstore.py` tiene el mismo patrón para embeddings
  (`EMBED_TIMEOUT_SEGUNDOS`, más corto porque embeddings es mucho más rápido
  que generación). `app.py` tiene `_mensaje_error_ollama()` para traducir
  `httpx.ConnectError`/`httpx.TimeoutException` a un mensaje legible en vez
  del traceback crudo — todo punto que llama a `llm.py` o dispara embeddings
  está envuelto en `try/except Exception` usando ese helper.
- `src/extraccion.py` — extracción estructurada de requisitos (JSON:
  `{"requisito", "categoria"}`). Nunca debe inventar requisitos que no estén
  en el documento.
- `src/propuesta.py` — pipeline de generación: por cada requisito, RAG contra
  `coleccion_servicios`, después un único prompt final que redacta la
  propuesta completa en la plantilla fija.
- `src/documentos_pmi.py` — genera, uno por vez (nunca los 5 juntos), los
  documentos PMI de arranque de proyecto: Acta de Inicio, Documento de
  Formulación, Gestión del Cambio, Lecciones Aprendidas y Documento de
  Cierre. Mismos títulos y secciones que `src/lib/documentos.ts` del proyecto
  CPM — si se agrega/renombra una sección ahí, replicar el cambio en
  `PLANTILLAS` acá para que ambos sigan alineados. Cada sección sin
  información suficiente en el documento de cliente queda como
  `"[Completar]"` en vez de inventarse (mismo principio que "sin cobertura
  clara" de `propuesta.py`) — Lecciones Aprendidas y Documento de Cierre en
  particular van a tener casi todo así, porque describen una ejecución que
  todavía no pasó; ambos documentos sirven como esqueleto editable, no como
  redacción final.
- `src/exportar_word.py` — markdown simple (`#`/`##`/`###`, `-`, `**negrita**`)
  a `.docx` editable.
- `src/resumen.py` — funcionalidad original (resumir/comparar un documento de
  cliente), ahora leyendo desde `coleccion_clientes`.

## Reglas no negociables del pipeline de propuestas

1. **Nunca inventar cobertura.** Si ningún fragmento de `coleccion_servicios`
   cubre razonablemente un requisito, la propuesta tiene que decirlo en
   "Requisitos sin cobertura clara" — nunca forzar una recomendación. Esto
   está en el system prompt de `propuesta.py` y no se toca sin que el usuario
   lo pida explícitamente.
2. **Nunca inventar specs.** La justificación de cada servicio recomendado
   sale del contexto recuperado, no de conocimiento general del modelo. Por
   eso el catálogo de servicios tiene que tener specs numéricas explícitas —
   ver checklist de aceptación más abajo.
3. **Control humano en el medio.** El flujo de la pestaña "Generar propuesta"
   siempre para en la lista de requisitos extraídos (editable) antes de
   generar la propuesta final — no es un botón único de punta a punta.
4. **Nunca generar precios.** El catálogo de servicios puede tener un campo
   de costo interno, pero el pricing final de una propuesta comercial queda
   siempre para revisión humana.

## El catálogo de servicios es el cuello de botella de calidad

`servicios/*.md` (excepto `_template.md`) están cargados con specs de
**ejemplo** marcadas `X` / "COMPLETAR CON DATOS REALES" — no son datos reales
de la empresa. Un modelo de este tamaño no va a inventar SLAs correctamente,
así que completar estos archivos con información real es tarea del usuario,
no de Claude Code. Al agregar un servicio nuevo, copiar `servicios/_template.md`
y mantener el mismo formato de secciones (Descripción, Especificaciones
técnicas, SLA, Cuándo ofrecerlo, Cuándo NO ofrecerlo) para que el chunking por
sección de `servicios_loader.py` siga funcionando igual para todos.

## Modelo de LLM

Con 8-16GB RAM sin GPU, `llama3.2:3b` alcanza para resumir pero se queda
corto en extracción estructurada + matching (la parte más exigente). Default
actual: `qwen2.5:7b-instruct` (configurable vía `ANALIZADOR_LLM_MODEL`).
Alternativa evaluada: `mistral:7b-instruct`. Esperar 1-3 min por propuesta en
CPU es aceptable — no es un flujo en tiempo real.

Importante distinguir dos tipos de operación bien distintos en velocidad:
las que solo calculan **embeddings** (Cargar documento, Cargar/recargar
catálogo) deberían ser cuestión de segundos — van en lote a `nomic-embed-text`,
un modelo chico. Las que hacen **generación con el LLM de 7B** (Extraer
borrador de servicio, Extraer requisitos, Generar propuesta, Generar
documento PMI) son inherentemente lentas en CPU (minutos, no segundos) — eso
no es un bug a arreglar con código, es el costo de correr un modelo capaz
100% local sin GPU. Si algún día hay quejas de velocidad ahí, las palancas
reales son: modelo más chico (`llama3.2:3b`, con peor calidad), o GPU.

## Comandos

```bash
pip install -r requirements.txt
streamlit run app.py
pytest              # solo las partes puras (sin Ollama/Chroma en vivo)
```

## Checklist de aceptación (ver también README.md)

- [ ] Un documento de cliente y el catálogo de servicios quedan en
      colecciones separadas de Chroma.
- [ ] La extracción de requisitos devuelve JSON válido y parseable
      (con reintentos si el modelo rompe el formato).
- [ ] Cada requisito de una propuesta generada tiene un servicio asociado
      O aparece en "Requisitos sin cobertura clara" — nunca ninguna de las
      dos cosas a la vez, nunca ninguna.
- [ ] La propuesta no inventa specs que no estén en `/servicios/*.md`.
- [ ] Un requisito que ningún servicio propio cubre se señala como tal, no
      se fuerza una recomendación.
- [ ] Exportar a `.docx` abre correctamente en Word.

## Fuera de alcance (por ahora)

- Integración con CRM/comercial.
- Multiusuario / despliegue en servidor compartido — sigue siendo una
  herramienta de un solo PM en su propia PC, por confidencialidad.
- Pricing automático de la propuesta final.

## Estado

Implementación inicial completa: separación de colecciones, ingesta de
documentos de cliente, catálogo de servicios estructurado (con 5 archivos
de ejemplo a completar con datos reales: Housing, Nube Empresarial, Backup,
Conectividad, Nube Híbrida), extracción de requisitos en JSON con reintentos,
generación de propuesta vía RAG contra el catálogo, exportación a Word, y UI
de Streamlit con 6 pestañas (Cargar documento / Catálogo de servicios /
Resumir / Comparar / Generar propuesta / Documentos PMI) más la carga rápida
del catálogo en la barra lateral. La pestaña "Documentos PMI" genera, de a
uno, los 5 documentos base de arranque (Acta de Inicio, Formulación, Gestión
del Cambio, Lecciones Aprendidas, Cierre) a partir del documento de cliente —
mismo set y secciones que el módulo Documentos de CPM. La pestaña "Catálogo
de servicios" permite subir un PDF/Word suelto de un servicio propio y arma
un borrador de ficha vía IA (`src/servicios_extraccion.py`), editable antes
de guardarlo como `.md` — la barra lateral sigue siendo la vía rápida para
recargar lo que ya está en `/servicios/*.md` sin pasar por la IA. Instalación
en Windows resuelta
con `setup.ps1` (instala Ollama + modelos + venv) que además crea un ícono de
escritorio; uso diario "como app" vía `iniciar_app.vbs` (invisible, abre
Chrome/Edge en modo app sin barra de direcciones — `_iniciar_interno.bat` es
su motor interno, no se corre directo) e `iniciar.bat` como variante con
consola visible para diagnosticar errores.

Deploy en la nube (Railway u otro) fue evaluado y descartado a pedido del
usuario: rompe la premisa "100% local" del proyecto (los documentos de
cliente dejarían de quedarse en su máquina) — no reabrir esa opción sin que
el usuario la pida explícitamente de nuevo. Pendiente para el usuario:
completar `servicios/*.md` con datos reales de ITC/Antel antes de usar la
herramienta en propuestas reales. Próximos pasos a definir con el usuario.
