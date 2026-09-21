"""Extracción asistida por IA de un servicio nuevo del catálogo a partir
de un documento suelto (PDF/Word/texto) que el usuario ya tenga armado —
folleto, ficha técnica, presentación comercial.

Es un paso de BORRADOR: a diferencia del resto del pipeline (que solo lee
del catálogo ya estructurado en `/servicios/*.md`), acá el modelo sí tiene
que interpretar texto libre y completar los campos fijos — con el mismo
riesgo de inventar specs que tiene cualquier extracción. Por eso el
resultado nunca se guarda directo: se muestra editable en la UI
(`app.py`, pestaña "Catálogo de servicios") para que un humano lo revise
y corrija antes de indexarlo.
"""

import re

from . import llm

SYSTEM_PROMPT = """Sos un asistente que estructura información de un servicio comercial a partir \
de un documento suelto (folleto, ficha técnica, presentación) para armar una entrada de catálogo.

Reglas estrictas:
- Devolvé EXCLUSIVAMENTE un objeto JSON válido, sin texto antes ni después, sin bloques de \
código markdown.
- El objeto tiene EXACTAMENTE estas claves, todas como texto: "nombre", "categoria", \
"descripcion", "especificaciones_tecnicas", "sla", "cuando_ofrecerlo", "cuando_no_ofrecerlo".
- Completá cada campo SOLO con lo que el documento diga explícitamente. Si el documento no \
menciona claramente algo (por ejemplo, no da un SLA o un límite técnico numérico), escribí \
exactamente "[Verificar - no especificado en el documento fuente]" en ese campo. NUNCA inventes \
números, porcentajes o condiciones que no estén en el texto.
- "especificaciones_tecnicas" y "sla" van como lista de texto, un ítem por línea empezando con \
"- ".
- Redactá en español."""

CAMPOS_ORDEN = [
    ("descripcion", "Descripción"),
    ("especificaciones_tecnicas", "Especificaciones técnicas"),
    ("sla", "SLA"),
    ("cuando_ofrecerlo", "Cuándo ofrecerlo"),
    ("cuando_no_ofrecerlo", "Cuándo NO ofrecerlo"),
]

PLACEHOLDER_SIN_DATO = "[Verificar - no especificado en el documento fuente]"


def extraer_borrador_servicio(texto_documento: str) -> dict:
    resultado = llm.generar_json(
        SYSTEM_PROMPT,
        f"Documento fuente:\n\n{texto_documento}\n\n"
        "Extraé la ficha del servicio en el formato indicado.",
    )
    if not isinstance(resultado, dict):
        raise ValueError("Se esperaba un objeto JSON con los campos del servicio.")

    claves_esperadas = {"nombre", "categoria", *(clave for clave, _ in CAMPOS_ORDEN)}
    return {clave: str(resultado.get(clave, "")).strip() for clave in claves_esperadas}


def slug_desde_nombre(nombre: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", nombre.lower()).strip("-")
    return slug or "servicio"


def borrador_a_markdown(datos: dict) -> str:
    nombre = datos.get("nombre", "").strip() or "Servicio sin nombre"
    categoria = datos.get("categoria", "").strip() or "sin categoría"

    secciones = []
    for clave, titulo in CAMPOS_ORDEN:
        contenido = datos.get(clave, "").strip() or PLACEHOLDER_SIN_DATO
        secciones.append(f"## {titulo}\n{contenido}")

    cuerpo = "\n\n".join(secciones)
    return f"---\nnombre: {nombre}\ncategoria: {categoria}\n---\n\n{cuerpo}\n"
