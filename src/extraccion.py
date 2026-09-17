"""Extracción estructurada de requisitos técnicos desde el documento de
un cliente. Es el paso más exigente del pipeline (JSON estricto +
razonamiento), separado a propósito del modo de redacción en prosa.
"""

from . import llm

SYSTEM_PROMPT_EXTRACCION = """Sos un analista técnico. Tu única tarea es leer el documento de un \
cliente y extraer los requisitos técnicos mencionados, como una lista JSON.

Reglas estrictas:
- Devolvé EXCLUSIVAMENTE un array JSON válido, sin texto antes ni después, sin bloques de código \
markdown.
- Cada elemento del array es un objeto: {"requisito": "<texto breve y concreto>", \
"categoria": "<categoría>"}.
- Las categorías deben ser una de: computo, almacenamiento, red, compliance, disponibilidad, \
soporte, otro.
- No inventes requisitos que no estén planteados en el documento.
- Si el documento no tiene requisitos técnicos claros, devolvé un array vacío []."""

CATEGORIAS_VALIDAS = {
    "computo",
    "almacenamiento",
    "red",
    "compliance",
    "disponibilidad",
    "soporte",
    "otro",
}


def validar_requisitos(resultado) -> list[dict]:
    if not isinstance(resultado, list):
        raise ValueError("Se esperaba una lista JSON de requisitos.")

    requisitos = []
    for item in resultado:
        if not isinstance(item, dict) or "requisito" not in item:
            continue
        categoria = str(item.get("categoria", "otro")).strip().lower()
        if categoria not in CATEGORIAS_VALIDAS:
            categoria = "otro"
        requisitos.append({"requisito": str(item["requisito"]).strip(), "categoria": categoria})
    return requisitos


def extraer_requisitos(texto_documento: str) -> list[dict]:
    resultado = llm.generar_json(
        SYSTEM_PROMPT_EXTRACCION,
        f"Documento del cliente:\n\n{texto_documento}\n\n"
        "Extraé los requisitos técnicos en el formato indicado.",
    )
    return validar_requisitos(resultado)
