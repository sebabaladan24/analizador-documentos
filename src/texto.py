"""Utilidad de texto compartida entre la ingesta de documentos de cliente
(`ingesta.py`) y el catálogo de servicios (`servicios_loader.py`): partir
un texto largo en fragmentos de tamaño acotado.

Existe como módulo aparte porque las dos cosas la necesitan: sin este
troceo, una sección larga de un servicio (o un documento de cliente)
termina mandándole al modelo de embeddings más texto del que su ventana
de contexto soporta, y Ollama devuelve
`the input length exceeds the context length` en vez de indexarlo.
"""


def chunkear_texto(texto: str, tam_palabras: int, solape_palabras: int) -> list[str]:
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
