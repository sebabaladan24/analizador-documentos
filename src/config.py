import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("ANALIZADOR_DATA_DIR", BASE_DIR / "data"))
CHROMA_DIR = DATA_DIR / "chroma"
SERVICIOS_DIR = Path(os.environ.get("ANALIZADOR_SERVICIOS_DIR", BASE_DIR / "servicios"))

# ollama.Client toma el host de la variable de entorno OLLAMA_HOST si está seteada.
LLM_MODEL = os.environ.get("ANALIZADOR_LLM_MODEL", "qwen2.5:7b-instruct")
EMBED_MODEL = os.environ.get("ANALIZADOR_EMBED_MODEL", "nomic-embed-text")

# La librería de Ollama no pone timeout por defecto (timeout=None => espera
# para siempre). Generoso a propósito: en CPU sin GPU, generar un documento
# largo puede tardar varios minutos y no queremos cortar algo que va a
# terminar bien. Es una red de seguridad para cuando Ollama está realmente
# trabado, no un límite agresivo.
LLM_TIMEOUT_SEGUNDOS = int(os.environ.get("ANALIZADOR_LLM_TIMEOUT_SEGUNDOS", "900"))
EMBED_TIMEOUT_SEGUNDOS = int(os.environ.get("ANALIZADOR_EMBED_TIMEOUT_SEGUNDOS", "180"))

COLECCION_CLIENTES = "coleccion_clientes"
COLECCION_SERVICIOS = "coleccion_servicios"

CHUNK_SIZE_WORDS = 350
CHUNK_OVERLAP_WORDS = 50

JSON_EXTRACCION_MAX_REINTENTOS = 3
