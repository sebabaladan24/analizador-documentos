import tempfile
from pathlib import Path

import streamlit as st

from src import config, exportar_word, extraccion, ingesta, propuesta, resumen, servicios_loader

st.set_page_config(page_title="Generador de Propuestas Técnicas", layout="wide")

# --- Barra lateral: catálogo de servicios (fuente separada de los docs de cliente) ---
st.sidebar.header("Base de conocimiento de servicios")
st.sidebar.caption(f"Archivos leídos desde `{config.SERVICIOS_DIR.name}/`")

if st.sidebar.button("Cargar / recargar catálogo de servicios"):
    with st.sidebar:
        with st.spinner("Indexando catálogo de servicios..."):
            servicios, total_chunks = servicios_loader.cargar_catalogo_servicios()
    if servicios:
        st.sidebar.success(f"{len(servicios)} servicios cargados ({total_chunks} fragmentos).")
    else:
        st.sidebar.warning(
            "No se encontró ningún archivo en `servicios/*.md` (aparte de la plantilla `_template.md`)."
        )
    st.session_state["servicios_cargados"] = servicios

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

tab_cargar, tab_resumir, tab_comparar, tab_propuesta = st.tabs(
    ["Cargar documento", "Resumir", "Comparar", "Generar propuesta"]
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
        except ValueError as error:
            st.error(str(error))
        finally:
            ruta_tmp.unlink(missing_ok=True)

with tab_resumir:
    st.subheader("Resumir documento de cliente")
    docs = _docs_cliente_disponibles()
    if not docs:
        st.info("No hay documentos de cliente cargados todavía.")
    else:
        doc_id = st.selectbox("Documento", options=list(docs.keys()), format_func=lambda k: docs[k])
        if st.button("Resumir"):
            with st.spinner("Generando resumen..."):
                st.markdown(resumen.resumir_documento(doc_id))

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
                with st.spinner("Comparando..."):
                    st.markdown(resumen.comparar_documentos(doc_a, doc_b, docs[doc_a], docs[doc_b]))

with tab_propuesta:
    st.subheader("Generar propuesta técnica")
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
                except ValueError as error:
                    st.error(f"No se pudieron extraer los requisitos: {error}")

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
                        with st.spinner("Generando propuesta (puede tardar unos minutos)..."):
                            st.session_state["propuesta_generada"] = propuesta.generar_propuesta(
                                nombre_proyecto or doc_id, requisitos_validos
                            )

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
