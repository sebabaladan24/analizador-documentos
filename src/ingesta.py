"""Ingesta de documentos de cliente: extracción de texto, chunking e
indexado en `coleccion_clientes`. Esta es la funcionalidad "actual" de
resumir/comparar documentos sueltos, sobre la que se construye el resto.
"""

import uuid
from pathlib import Path

import docx
from pypdf import PdfReader

from . import config, vectorstore


def extraer_texto(ruta: Path) -> str:
    sufijo = ruta.suffix.lower()
    if sufijo == ".pdf":
        lector = PdfReader(str(ruta))
        return "\n".join(pagina.extract_text() or "" for pagina in lector.pages)
    if sufijo == ".docx":
        documento = docx.Document(str(ruta))
        return "\n".join(parrafo.text for parrafo in documento.paragraphs)
    return ruta.read_text(encoding="utf-8", errors="ignore")


def chunkear_texto(
    texto: str,
    tam_palabras: int = config.CHUNK_SIZE_WORDS,
    solape_palabras: int = config.CHUNK_OVERLAP_WORDS,
) -> list[str]:
    palabras = texto.split()
    if not palabras:
        return []
    chunks = []
    inicio = 0
    paso = max(tam_palabras - solape_palabras, 1)
    while inicio < len(palabras):
        fin = inicio + tam_palabras
        chunks.append(" ".join(palabras[inicio:fin]))
        if fin >= len(palabras):
            break
        inicio += paso
    return chunks


def ingerir_documento_cliente(ruta: Path, nombre_archivo: str) -> str:
    texto = extraer_texto(ruta)
    chunks = chunkear_texto(texto)
    if not chunks:
        raise ValueError("El documento no contiene texto extraíble.")

    doc_id = f"{Path(nombre_archivo).stem}-{uuid.uuid4().hex[:8]}"
    ids = [f"{doc_id}__{i}" for i in range(len(chunks))]
    metadatas = [
        {"doc_id": doc_id, "nombre_archivo": nombre_archivo, "chunk": i}
        for i in range(len(chunks))
    ]
    vectorstore.add_chunks(config.COLECCION_CLIENTES, ids, chunks, metadatas)
    return doc_id


def obtener_texto_completo(doc_id: str) -> str:
    col = vectorstore.get_collection(config.COLECCION_CLIENTES)
    datos = col.get(where={"doc_id": doc_id}, include=["documents", "metadatas"])
    pares = sorted(zip(datos["metadatas"], datos["documents"]), key=lambda par: par[0]["chunk"])
    return "\n".join(documento for _, documento in pares)


def listar_documentos_cliente() -> dict[str, str]:
    """Devuelve {doc_id: nombre_archivo} de los documentos de cliente ya ingestados."""
    return vectorstore.listar_valores_metadata(config.COLECCION_CLIENTES, "doc_id", "nombre_archivo")
