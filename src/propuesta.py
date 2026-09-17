"""Generación de la propuesta técnica: para cada requisito extraído,
recupera fragmentos relevantes de `coleccion_servicios` (RAG) y arma un
prompt final que redacta la propuesta completa siguiendo una plantilla
fija. El modelo tiene prohibido inventar specs que no vengan en el
contexto recuperado, y debe declarar explícitamente los requisitos sin
cobertura en vez de forzar una recomendación.
"""

from . import config, llm, vectorstore

SYSTEM_PROMPT_PROPUESTA = """Sos un ingeniero preventa que redacta propuestas técnicas para \
clientes, usando EXCLUSIVAMENTE el catálogo de servicios propio que se te provee como contexto.

Reglas estrictas:
- Nunca inventes especificaciones, SLAs o capacidades que no estén en el contexto de servicios \
provisto.
- Si ningún fragmento de servicio cubre razonablemente un requisito, decilo explícitamente en la \
sección "Requisitos sin cobertura clara". NUNCA fuerces una recomendación en ese caso.
- Seguí EXACTAMENTE la estructura de encabezados markdown indicada, sin agregar ni quitar \
secciones.
- Sé concreto: citá specs numéricas del contexto cuando existan."""

PLANTILLA_INSTRUCCIONES = """# Propuesta Técnica — {nombre_proyecto}

## Resumen de requisitos identificados
{lista_requisitos}

## Servicios propuestos
[Para cada requisito CON cobertura, un bloque:
### Requisito: <texto del requisito>
**Servicio recomendado**: <nombre del servicio>
**Justificación**: <por qué cubre el requisito, citando specs del contexto>
**Consideraciones**: <límites, condiciones>
]

## Requisitos sin cobertura clara
[Los requisitos SIN un servicio propio que los cubra claramente. Si todos tienen cobertura, \
escribir "Ninguno."]

## Notas para revisión humana
[Ambigüedades detectadas en el documento del cliente, o "Ninguna." si no hay]"""


def _contexto_para_requisito(requisito: str, n_results: int = 4) -> str:
    resultados = vectorstore.query(config.COLECCION_SERVICIOS, requisito, n_results=n_results)
    documentos = (resultados.get("documents") or [[]])[0]
    metadatas = (resultados.get("metadatas") or [[]])[0]
    if not documentos:
        return "(sin fragmentos relevantes encontrados en el catálogo de servicios)"

    fragmentos = []
    for documento, metadata in zip(documentos, metadatas):
        nombre = (metadata or {}).get("nombre_servicio", "servicio desconocido")
        fragmentos.append(f"[Servicio: {nombre}]\n{documento}")
    return "\n\n".join(fragmentos)


def generar_propuesta(nombre_proyecto: str, requisitos: list[dict]) -> str:
    if not requisitos:
        raise ValueError("No hay requisitos para generar la propuesta.")

    lista_requisitos_md = "\n".join(
        f"- {r['requisito']} ({r['categoria']})" for r in requisitos
    )

    bloques_contexto = []
    for r in requisitos:
        contexto = _contexto_para_requisito(r["requisito"])
        bloques_contexto.append(
            f"### Requisito: {r['requisito']} (categoría: {r['categoria']})\n"
            f"Fragmentos de servicios propios recuperados:\n{contexto}"
        )
    contexto_completo = "\n\n".join(bloques_contexto)

    plantilla = PLANTILLA_INSTRUCCIONES.format(
        nombre_proyecto=nombre_proyecto, lista_requisitos=lista_requisitos_md
    )

    user_prompt = (
        "Requisitos del cliente y contexto de servicios propios recuperado para cada uno:\n\n"
        f"{contexto_completo}\n\n"
        "Redactá la propuesta técnica completa siguiendo EXACTAMENTE esta estructura "
        f"(reemplazando los placeholders entre corchetes):\n\n{plantilla}"
    )

    return llm.chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT_PROPUESTA},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
