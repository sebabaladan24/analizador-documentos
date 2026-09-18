"""Generación de los 5 documentos PMI de arranque de proyecto (Acta de
Inicio, Documento de Formulación, Gestión del Cambio, Lecciones
Aprendidas, Documento de Cierre) a partir del texto del documento de
cliente. Mismos títulos y secciones que el módulo "Documentos" del
proyecto CPM (`src/lib/documentos.ts` en ese repo), para que el PM que
ya usa esa plantilla la reconozca acá.

Cada documento se genera de forma independiente (nunca los 5 juntos):
el modelo completa lo que puede inferir del documento de cliente y deja
"[Completar]" en los campos que dependen de decisiones internas
(sponsor, presupuesto, aprobaciones) o de información que todavía no
existe al momento de generarlo (desempeño real, lecciones de una
ejecución que no pasó).
"""

from . import llm

PLANTILLAS: dict[str, dict] = {
    "acta_inicio": {
        "titulo": "Acta de Inicio",
        "secciones": [
            "Nombre del proyecto",
            "Patrocinador (sponsor)",
            "Director del proyecto y nivel de autoridad",
            "Justificación del proyecto",
            "Objetivos y criterios de éxito",
            "Descripción de alto nivel y alcance",
            "Requisitos de alto nivel",
            "Riesgos de alto nivel",
            "Hitos principales",
            "Presupuesto estimado",
            "Interesados clave",
            "Aprobación",
        ],
    },
    "formulacion": {
        "titulo": "Documento de Formulación",
        "secciones": [
            "Antecedentes y diagnóstico de la situación actual",
            "Problema u oportunidad que origina el proyecto",
            "Objetivo general",
            "Objetivos específicos",
            "Alcance del proyecto",
            "Alternativas evaluadas",
            "Factibilidad técnica",
            "Factibilidad económica y financiera",
            "Beneficiarios e interesados",
            "Cronograma estimado",
            "Presupuesto estimado",
            "Riesgos identificados",
            "Conclusión y recomendación",
        ],
    },
    "gestion_cambio": {
        "titulo": "Gestión del Cambio",
        "secciones": [
            "Objetivo del proceso de gestión de cambios",
            "Procedimiento: cómo se solicita, evalúa y aprueba un cambio",
            "Responsable o comité de aprobación",
            "Registro de solicitudes de cambio",
        ],
    },
    "lecciones_aprendidas": {
        "titulo": "Lecciones Aprendidas",
        "secciones": [
            "Objetivo del documento",
            "¿Qué funcionó bien?",
            "¿Qué no funcionó? Dificultades encontradas",
            "Causas raíz",
            "Lecciones por área",
            "Recomendaciones para futuros proyectos",
        ],
    },
    "cierre": {
        "titulo": "Documento de Cierre",
        "secciones": [
            "Resumen del proyecto",
            "Objetivos alcanzados vs. planificados",
            "Entregables finales aceptados",
            "Desempeño de alcance (planificado vs. real)",
            "Desempeño de cronograma (planificado vs. real)",
            "Desempeño de presupuesto (planificado vs. real)",
            "Aceptación formal del cliente/sponsor",
            "Cierre de contratos y proveedores",
            "Liberación de recursos del equipo",
            "Lecciones aprendidas",
            "Aprobación de cierre",
        ],
    },
}

SYSTEM_PROMPT = """Sos un asistente que redacta borradores de documentos PMI de gestión de \
proyectos a partir de un documento técnico enviado por un cliente.

Reglas estrictas:
- Completá cada sección SOLO con lo que se pueda inferir razonablemente del documento del \
cliente.
- Si una sección depende de información que el documento NO tiene (decisiones internas como \
sponsor, director de proyecto, presupuesto exacto, aprobaciones; o hechos que todavía no \
ocurrieron, como desempeño real o lecciones de una ejecución que no pasó), escribí exactamente \
"[Completar]" en esa sección. NUNCA inventes nombres, fechas, montos o datos que no estén en el \
documento.
- Seguí EXACTAMENTE los encabezados de sección indicados, en el mismo orden, sin agregar ni \
quitar ninguno.
- Redactá en español, en prosa clara y concisa."""


def generar_documento_pmi(tipo: str, texto_documento_cliente: str) -> str:
    if tipo not in PLANTILLAS:
        raise ValueError(f"Tipo de documento PMI desconocido: {tipo}")

    plantilla = PLANTILLAS[tipo]
    estructura = "\n\n".join(f"## {seccion}\n[Completar]" for seccion in plantilla["secciones"])

    user_prompt = (
        f"Documento del cliente:\n\n{texto_documento_cliente}\n\n"
        f"Redactá el documento '{plantilla['titulo']}' completando esta estructura exacta "
        "(reemplazando cada '[Completar]' por el contenido correspondiente, o dejándolo tal "
        f"cual si no hay información suficiente en el documento del cliente):\n\n"
        f"# {plantilla['titulo']}\n\n{estructura}"
    )

    return llm.chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
