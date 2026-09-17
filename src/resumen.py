"""Funcionalidad "original" de la herramienta: resumir y comparar
documentos de cliente sueltos. Se mantiene tal cual, solo que ahora lee
los documentos desde `coleccion_clientes` en vez de una colección única.
"""

from . import ingesta, llm


def resumir_documento(doc_id: str) -> str:
    texto = ingesta.obtener_texto_completo(doc_id)
    return llm.chat(
        [
            {
                "role": "system",
                "content": (
                    "Sos un asistente que resume documentos técnicos de forma clara y "
                    "concisa, en español, para un project manager."
                ),
            },
            {"role": "user", "content": f"Resumí el siguiente documento:\n\n{texto}"},
        ],
        temperature=0.3,
    )


def comparar_documentos(doc_id_a: str, doc_id_b: str, nombre_a: str, nombre_b: str) -> str:
    texto_a = ingesta.obtener_texto_completo(doc_id_a)
    texto_b = ingesta.obtener_texto_completo(doc_id_b)
    return llm.chat(
        [
            {
                "role": "system",
                "content": (
                    "Sos un asistente que compara dos documentos técnicos y señala "
                    "similitudes, diferencias y contradicciones, en español."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Documento '{nombre_a}':\n{texto_a}\n\n---\n\n"
                    f"Documento '{nombre_b}':\n{texto_b}\n\nCompará ambos documentos."
                ),
            },
        ],
        temperature=0.3,
    )
