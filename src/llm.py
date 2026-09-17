"""Wrapper fino sobre Ollama. Separa dos modos:

- `chat()`: texto libre en prosa (resúmenes, comparaciones, redacción de
  la propuesta final).
- `generar_json()`: fuerza salida JSON (vía `format="json"` de Ollama) y
  reintenta pasándole el error de parseo al modelo si la respuesta
  anterior no era JSON válido. Se usa solo para la extracción de
  requisitos, que es la parte que no puede darse el lujo de romper el
  formato esperado.
"""

import json

import ollama

from . import config


def chat(mensajes: list[dict], temperature: float = 0.2, json_mode: bool = False) -> str:
    kwargs = {
        "model": config.LLM_MODEL,
        "messages": mensajes,
        "options": {"temperature": temperature},
    }
    if json_mode:
        kwargs["format"] = "json"
    respuesta = ollama.chat(**kwargs)
    return respuesta["message"]["content"]


def generar_json(system_prompt: str, user_prompt: str, max_reintentos: int | None = None):
    max_reintentos = max_reintentos or config.JSON_EXTRACCION_MAX_REINTENTOS
    mensajes = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    ultimo_error = None
    for _ in range(max_reintentos):
        contenido = chat(mensajes, temperature=0.1, json_mode=True)
        try:
            return json.loads(contenido)
        except json.JSONDecodeError as error:
            ultimo_error = error
            mensajes.append({"role": "assistant", "content": contenido})
            mensajes.append(
                {
                    "role": "user",
                    "content": (
                        f"Tu respuesta anterior no era JSON válido (error: {error}). "
                        "Respondé ÚNICAMENTE con JSON válido, sin texto adicional, "
                        "sin explicaciones y sin bloques de código markdown."
                    ),
                }
            )
    raise ValueError(f"No se pudo obtener JSON válido tras {max_reintentos} intentos: {ultimo_error}")
