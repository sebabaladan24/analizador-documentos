"""Carga el catálogo propio de servicios (`/servicios/*.md`) a
`coleccion_servicios`. Cada archivo tiene frontmatter (nombre, categoria)
y un cuerpo dividido en secciones `##`; cada sección se indexa con
metadata propia, para que el RAG pueda recuperar justo la sección
relevante (specs, SLA, cuándo NO ofrecerlo, etc.) en vez de todo el
archivo entero.

Una sección puede ser larga (una ficha con muchas specs, o un borrador
armado por `servicios_extraccion.py` a partir de un PDF largo), así que
cada sección se trocea con el mismo `chunkear_texto` que usa la ingesta
de documentos de cliente antes de mandarla a embeddings — sin esto,
Ollama devuelve "the input length exceeds the context length" en vez de
indexarla.
"""

import re
from pathlib import Path

import frontmatter

from . import config, vectorstore
from .texto import chunkear_texto


def dividir_por_secciones(cuerpo: str) -> list[tuple[str, str]]:
    partes = re.split(r"(?m)^##\s+", cuerpo)
    secciones = []
    for parte in partes:
        parte = parte.strip()
        if not parte:
            continue
        lineas = parte.split("\n", 1)
        titulo = lineas[0].strip()
        contenido = lineas[1].strip() if len(lineas) > 1 else ""
        secciones.append((titulo, contenido))
    return secciones


def _listar_archivos_servicio() -> list[Path]:
    if not config.SERVICIOS_DIR.exists():
        return []
    return sorted(
        archivo
        for archivo in config.SERVICIOS_DIR.glob("*.md")
        if not archivo.name.startswith("_")
    )


def cargar_catalogo_servicios(reemplazar: bool = True) -> tuple[list[str], int]:
    """Indexa todos los `/servicios/*.md` en `coleccion_servicios`.

    Devuelve (nombres_de_servicios_cargados, cantidad_total_de_chunks).
    """
    archivos = _listar_archivos_servicio()

    if reemplazar:
        vectorstore.borrar_coleccion_completa(config.COLECCION_SERVICIOS)

    total_chunks = 0
    servicios_cargados = []

    for archivo in archivos:
        post = frontmatter.load(archivo)
        nombre = post.get("nombre", archivo.stem)
        categoria = post.get("categoria", "sin categoría")
        secciones = dividir_por_secciones(post.content)

        ids, documentos, metadatas = [], [], []
        for i, (titulo, contenido) in enumerate(secciones):
            if not contenido:
                continue
            texto_seccion = f"## {titulo}\n{contenido}".strip()
            fragmentos = chunkear_texto(
                texto_seccion, config.CHUNK_SIZE_WORDS, config.CHUNK_OVERLAP_WORDS
            )
            for j, fragmento in enumerate(fragmentos):
                ids.append(f"{archivo.stem}__{i}__{j}")
                documentos.append(fragmento)
                metadatas.append(
                    {
                        "nombre_servicio": nombre,
                        "categoria": categoria,
                        "seccion": titulo,
                        "archivo": archivo.name,
                    }
                )

        if ids:
            vectorstore.add_chunks(config.COLECCION_SERVICIOS, ids, documentos, metadatas)
            total_chunks += len(ids)
            servicios_cargados.append(nombre)

    return servicios_cargados, total_chunks


def listar_servicios_cargados() -> dict[str, str]:
    return vectorstore.listar_valores_metadata(
        config.COLECCION_SERVICIOS, "nombre_servicio", "categoria"
    )
