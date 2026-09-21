"""Acceso a Chroma. Las dos colecciones (clientes / servicios) se manejan
siempre por acá para no mezclar nunca los datos de un cliente con el
catálogo propio.

Los embeddings se calculan a mano con Ollama y se pasan directamente a
Chroma (en vez de usar el mecanismo de `embedding_function` de la
librería), para no depender de qué firma de esa interfaz soporta la
versión de chromadb instalada.

Usa un `ollama.Client` propio con timeout — igual que `llm.py` — en vez
de `ollama.embeddings()` suelto, que por default espera para siempre si
Ollama se traba.
"""

from pathlib import Path

import chromadb
import ollama

from . import config

_client = None
_cliente_ollama = ollama.Client(timeout=config.EMBED_TIMEOUT_SEGUNDOS)


def get_client():
    global _client
    if _client is None:
        config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return _client


def get_collection(nombre: str):
    return get_client().get_or_create_collection(name=nombre)


def embed(textos: list[str]) -> list[list[float]]:
    """Calcula todos los embeddings en un solo pedido a Ollama (soporta
    lote vía /api/embed) en vez de uno por fragmento — con documentos de
    varias páginas, mandar 50-100 pedidos HTTP secuenciales es la
    diferencia entre segundos y minutos.
    """
    if not textos:
        return []
    respuesta = _cliente_ollama.embed(model=config.EMBED_MODEL, input=textos)
    return list(respuesta.embeddings)


def add_chunks(coleccion: str, ids: list[str], documentos: list[str], metadatas: list[dict]):
    if not ids:
        return
    col = get_collection(coleccion)
    embeddings = embed(documentos)
    col.add(ids=ids, documents=documentos, metadatas=metadatas, embeddings=embeddings)


def query(coleccion: str, texto: str, n_results: int = 5, where: dict | None = None):
    col = get_collection(coleccion)
    consulta_embedding = embed([texto])[0]
    kwargs = {"query_embeddings": [consulta_embedding], "n_results": n_results}
    if where:
        kwargs["where"] = where
    return col.query(**kwargs)


def borrar_coleccion_completa(coleccion: str):
    col = get_collection(coleccion)
    existentes = col.get(include=[])
    if existentes["ids"]:
        col.delete(ids=existentes["ids"])


def listar_valores_metadata(coleccion: str, campo_id: str, campo_label: str) -> dict[str, str]:
    """Devuelve {valor_de_campo_id: valor_de_campo_label} únicos de la colección."""
    col = get_collection(coleccion)
    datos = col.get(include=["metadatas"])
    resultado: dict[str, str] = {}
    for meta in datos.get("metadatas", []):
        if meta and campo_id in meta:
            resultado[meta[campo_id]] = meta.get(campo_label, meta[campo_id])
    return resultado
