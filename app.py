import tempfile
from pathlib import Path

import httpx
import streamlit as st

from src import (
    config,
    documentos_pmi,
    exportar_word,
    extraccion,
    ingesta,
    plantilla_word,
    propuesta,
    resumen,
    servicios_extraccion,
    servicios_loader,
)

st.set_page_config(page_title="Generador de Propuestas Técnicas", layout="wide")


def _mensaje_error_ollama(error: Exception) -> str:
    """Traduce errores típicos de Ollama/red a un mensaje claro en vez del
    traceback crudo — sin esto, cualquier corte de conexión o timeout se
    veía como una pantalla roja con código Python."""
    if isinstance(error, httpx.ConnectError):
        return (
            "No se pudo conectar con Ollama. Verificá que esté corriendo (ícono en la "
            "bandeja del sistema, o probá `ollama list` en una terminal)."
        )
    if isinstance(error, httpx.TimeoutException):
        minutos = config.LLM_TIMEOUT_SEGUNDOS // 60
        return (
            f"La operación tardó más de {minutos} minutos y se cortó. Puede pasar con "
            "documentos muy largos o si la PC tiene poca memoria libre para el modelo. "
            "Probá con un documento más corto, cerrá otros programas, o intentá de nuevo."
        )
    if isinstance(error, ValueError):
        return str(error)
    return f"Ocurrió un error inesperado: {error}"

# --- Barra lateral: catálogo de servicios (fuente separada de los docs de cliente) ---
st.sidebar.header("Base de conocimiento de servicios")
st.sidebar.caption(
    f"Archivos leídos desde `{config.SERVICIOS_DIR.name}/`. Para agregar servicios desde un "
    "PDF/Word, usá la pestaña 'Catálogo de servicios' — esto de acá solo reindexa lo que ya "
    "está guardado en esa carpeta."
)

if st.sidebar.button("Cargar / recargar catálogo de servicios"):
    try:
        with st.sidebar:
            with st.spinner("Indexando catálogo de servicios..."):
                servicios, total_chunks = servicios_loader.cargar_catalogo_servicios()
        if servicios:
            st.sidebar.success(f"{len(servicios)} servicios cargados ({total_chunks} fragmentos).")
        else:
            st.sidebar.warning(
                "No se encontró ningún archivo en `servicios/*.md` (aparte de `_template.md`)."
            )
        st.session_state["servicios_cargados"] = servicios
    except Exception as error:
        st.sidebar.error(_mensaje_error_ollama(error))

servicios_cargados = st.session_state.get("servicios_cargados")
if servicios_cargados is None:
    servicios_cargados = list(servicios_loader.listar_servicios_cargados().keys())

if servicios_cargados:
    st.sidebar.write("Servicios en la colección:")
    for nombre_servicio in servicios_cargados:
        st.sidebar.write(f"- {nombre_servicio}")
else:
    st.sidebar.info("Todavía no cargaste el catálogo de servicios.")

st.title("Generador de Propuestas Técnicas")
st.caption("100% local — Ollama + Chroma. Ningún documento sale de esta máquina.")

tab_cargar, tab_catalogo, tab_resumir, tab_comparar, tab_propuesta, tab_documentos_pmi = st.tabs(
    [
        "Cargar documento",
        "Catálogo de servicios",
        "Resumir",
        "Comparar",
        "Generar propuesta",
        "Documentos PMI",
    ]
)


def _docs_cliente_disponibles() -> dict[str, str]:
    return ingesta.listar_documentos_cliente()


with tab_cargar:
    st.subheader("Cargar documento de cliente")
    archivo_subido = st.file_uploader(
        "Documento del cliente (PDF, DOCX, TXT o MD)", type=["pdf", "docx", "txt", "md"]
    )
    if archivo_subido and st.button("Ingestar documento"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(archivo_subido.name).suffix) as tmp:
            tmp.write(archivo_subido.getbuffer())
            ruta_tmp = Path(tmp.name)
        try:
            with st.spinner("Extrayendo texto e indexando..."):
                doc_id = ingesta.ingerir_documento_cliente(ruta_tmp, archivo_subido.name)
            st.success(f"Documento ingestado como `{doc_id}`.")
        except Exception as error:
            st.error(_mensaje_error_ollama(error))
        finally:
            ruta_tmp.unlink(missing_ok=True)

with tab_catalogo:
    st.subheader("Agregar un servicio al catálogo desde un documento")
    st.caption(
        "Subí un folleto, ficha técnica o Word/PDF que ya tengas de un servicio propio. La IA "
        "arma un borrador estructurado — revisalo y corregilo antes de guardarlo: puede no "
        "captar bien las specs que el documento no dice de forma explícita, y nunca hay que "
        "confiar en eso sin revisarlo primero."
    )

    archivo_servicio = st.file_uploader(
        "Documento del servicio (PDF, DOCX, TXT o MD)",
        type=["pdf", "docx", "txt", "md"],
        key="uploader_servicio",
    )
    if archivo_servicio and st.button("Extraer borrador"):
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(archivo_servicio.name).suffix
        ) as tmp:
            tmp.write(archivo_servicio.getbuffer())
            ruta_tmp = Path(tmp.name)
        try:
            with st.spinner("Extrayendo información del documento (puede tardar varios minutos)..."):
                texto_servicio = ingesta.extraer_texto(ruta_tmp)
                st.session_state["borrador_servicio"] = servicios_extraccion.extraer_borrador_servicio(
                    texto_servicio
                )
        except Exception as error:
            st.error(f"No se pudo extraer el borrador: {_mensaje_error_ollama(error)}")
        finally:
            ruta_tmp.unlink(missing_ok=True)

    if "borrador_servicio" in st.session_state:
        borrador = st.session_state["borrador_servicio"]
        st.warning(
            "Revisá cada campo antes de guardar. Los que dicen '[Verificar...]' no estaban "
            "claros en el documento fuente — completalos a mano si corresponde, o dejalos así "
            "si de verdad no aplican."
        )

        col1, col2 = st.columns(2)
        with col1:
            borrador["nombre"] = st.text_input(
                "Nombre del servicio", value=borrador.get("nombre", ""), key="campo_nombre"
            )
        with col2:
            borrador["categoria"] = st.text_input(
                "Categoría", value=borrador.get("categoria", ""), key="campo_categoria"
            )

        for clave, titulo in servicios_extraccion.CAMPOS_ORDEN:
            borrador[clave] = st.text_area(
                titulo, value=borrador.get(clave, ""), height=120, key=f"campo_{clave}"
            )

        if st.button("Guardar en el catálogo"):
            if not borrador["nombre"].strip():
                st.error("Ponele un nombre al servicio antes de guardar.")
            else:
                nombre_archivo = f"{servicios_extraccion.slug_desde_nombre(borrador['nombre'])}.md"
                ruta_destino = config.SERVICIOS_DIR / nombre_archivo
                ruta_destino.write_text(
                    servicios_extraccion.borrador_a_markdown(borrador), encoding="utf-8"
                )
                try:
                    with st.spinner("Guardando y recargando el catálogo..."):
                        servicios, total_chunks = servicios_loader.cargar_catalogo_servicios()
                    st.session_state["servicios_cargados"] = servicios
                    del st.session_state["borrador_servicio"]
                    st.success(
                        f"Guardado como `servicios/{nombre_archivo}` y recargado en el catálogo "
                        f"({len(servicios)} servicios, {total_chunks} fragmentos)."
                    )
                except Exception as error:
                    st.error(
                        f"Se guardó `servicios/{nombre_archivo}`, pero no se pudo recargar el "
                        f"catálogo: {_mensaje_error_ollama(error)} Podés reintentar con el botón "
                        "'Cargar / recargar catálogo de servicios' de la barra lateral."
                    )

with tab_resumir:
    st.subheader("Resumir documento de cliente")
    docs = _docs_cliente_disponibles()
    if not docs:
        st.info("No hay documentos de cliente cargados todavía.")
    else:
        doc_id = st.selectbox("Documento", options=list(docs.keys()), format_func=lambda k: docs[k])
        if st.button("Resumir"):
            try:
                with st.spinner("Generando resumen..."):
                    st.markdown(resumen.resumir_documento(doc_id))
            except Exception as error:
                st.error(_mensaje_error_ollama(error))

with tab_comparar:
    st.subheader("Comparar dos documentos de cliente")
    docs = _docs_cliente_disponibles()
    if len(docs) < 2:
        st.info("Necesitás al menos 2 documentos cargados para comparar.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            doc_a = st.selectbox(
                "Documento A", options=list(docs.keys()), format_func=lambda k: docs[k], key="doc_a"
            )
        with col2:
            doc_b = st.selectbox(
                "Documento B", options=list(docs.keys()), format_func=lambda k: docs[k], key="doc_b"
            )
        if st.button("Comparar"):
            if doc_a == doc_b:
                st.warning("Elegí dos documentos distintos.")
            else:
                try:
                    with st.spinner("Comparando..."):
                        st.markdown(
                            resumen.comparar_documentos(doc_a, doc_b, docs[doc_a], docs[doc_b])
                        )
                except Exception as error:
                    st.error(_mensaje_error_ollama(error))

with tab_propuesta:
    st.subheader("Generar propuesta técnica")
    st.caption(
        "Flujo de 2 pasos. **1. Extraer requisitos**: la IA lee el documento del cliente y "
        "arma una lista de los requisitos técnicos que menciona (ej. \"necesita 40 servidores\", "
        "\"los datos no pueden salir del país\"), cada uno con una categoría — la vas a poder "
        "revisar y corregir antes de seguir. **2. Generar propuesta**: recién ahí busca en tu "
        "catálogo de servicios qué cubre cada requisito y redacta el borrador final."
    )
    docs = _docs_cliente_disponibles()
    if not docs:
        st.info(
            "No hay documentos de cliente cargados todavía. Cargá uno en la pestaña "
            "'Cargar documento'."
        )
    elif not servicios_cargados:
        st.warning(
            "Todavía no cargaste el catálogo de servicios (barra lateral). Sin eso, no hay "
            "nada contra qué cruzar los requisitos del cliente."
        )
    else:
        doc_id = st.selectbox(
            "Documento de cliente", options=list(docs.keys()), format_func=lambda k: docs[k],
            key="doc_propuesta",
        )
        nombre_proyecto = st.text_input("Nombre del cliente/proyecto", value=docs.get(doc_id, ""))

        if st.button("1. Extraer requisitos"):
            with st.spinner("Extrayendo requisitos..."):
                texto = ingesta.obtener_texto_completo(doc_id)
                try:
                    st.session_state["requisitos_extraidos"] = extraccion.extraer_requisitos(texto)
                except Exception as error:
                    st.error(f"No se pudieron extraer los requisitos: {_mensaje_error_ollama(error)}")

        if "requisitos_extraidos" in st.session_state:
            if not st.session_state["requisitos_extraidos"]:
                st.info("No se detectó ningún requisito técnico en el documento.")
            else:
                st.write("Revisá y editá los requisitos detectados antes de generar la propuesta:")
                requisitos_editados = st.data_editor(
                    st.session_state["requisitos_extraidos"],
                    num_rows="dynamic",
                    key="editor_requisitos",
                    column_config={
                        "requisito": st.column_config.TextColumn("Requisito", width="large"),
                        "categoria": st.column_config.SelectboxColumn(
                            "Categoría",
                            options=sorted(extraccion.CATEGORIAS_VALIDAS),
                        ),
                    },
                )

                if st.button("2. Generar propuesta"):
                    requisitos_validos = [
                        r for r in requisitos_editados if r.get("requisito", "").strip()
                    ]
                    if not requisitos_validos:
                        st.warning("No quedó ningún requisito para generar la propuesta.")
                    else:
                        try:
                            with st.spinner("Generando propuesta (puede tardar unos minutos)..."):
                                st.session_state["propuesta_generada"] = propuesta.generar_propuesta(
                                    nombre_proyecto or doc_id, requisitos_validos
                                )
                        except Exception as error:
                            st.error(_mensaje_error_ollama(error))

        if "propuesta_generada" in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state["propuesta_generada"])

            buffer_docx = exportar_word.markdown_a_docx(st.session_state["propuesta_generada"])
            st.download_button(
                "3. Exportar a Word",
                data=buffer_docx,
                file_name=f"propuesta-{nombre_proyecto or doc_id}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

with tab_documentos_pmi:
    st.subheader("Documentos PMI de arranque del proyecto")
    st.caption(
        "Acta de Inicio, Documento de Formulación, Gestión del Cambio, Lecciones Aprendidas y "
        "Documento de Cierre — mismo set que el módulo Documentos de gestión de proyectos. Se "
        "generan de a uno a partir del documento del cliente, nunca los 5 juntos."
    )

    docs = _docs_cliente_disponibles()
    if not docs:
        st.info("No hay documentos de cliente cargados todavía.")
    else:
        doc_id_pmi = st.selectbox(
            "Documento de cliente",
            options=list(docs.keys()),
            format_func=lambda k: docs[k],
            key="doc_documentos_pmi",
        )
        nombre_proyecto_pmi = st.text_input(
            "Nombre del cliente/proyecto (va en la portada del Word)",
            value=docs.get(doc_id_pmi, ""),
            key="nombre_proyecto_pmi",
        )

        if "documentos_pmi_generados" not in st.session_state:
            st.session_state["documentos_pmi_generados"] = {}
        generados = st.session_state["documentos_pmi_generados"]

        columnas = st.columns(len(documentos_pmi.PLANTILLAS))
        for columna, (tipo, plantilla) in zip(columnas, documentos_pmi.PLANTILLAS.items()):
            with columna:
                with st.container(border=True):
                    st.markdown(f"**{plantilla['titulo']}**")
                    st.caption("Generado ✅" if tipo in generados else "Sin generar")
                    if st.button("Generar", key=f"generar_{tipo}", use_container_width=True):
                        try:
                            with st.spinner(f"Generando {plantilla['titulo']}..."):
                                texto_cliente = ingesta.obtener_texto_completo(doc_id_pmi)
                                generados[tipo] = documentos_pmi.generar_documento_pmi(
                                    tipo, texto_cliente
                                )
                        except Exception as error:
                            st.error(_mensaje_error_ollama(error))

        for tipo, contenido in generados.items():
            titulo = documentos_pmi.PLANTILLAS[tipo]["titulo"]
            with st.expander(titulo, expanded=True):
                texto_editado = st.text_area(
                    "Contenido (editable)", value=contenido, height=350, key=f"editor_{tipo}"
                )
                generados[tipo] = texto_editado

                buffer_docx = plantilla_word.documento_pmi_a_docx(
                    titulo, nombre_proyecto_pmi or docs.get(doc_id_pmi, ""), texto_editado
                )
                st.download_button(
                    f"Exportar '{titulo}' a Word",
                    data=buffer_docx,
                    file_name=f"{tipo}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"exportar_{tipo}",
                )
