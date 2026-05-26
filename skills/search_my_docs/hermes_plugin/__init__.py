"""Plugin Hermes: search-my-docs

Registra dos tools:
  - search_my_docs: busca en la knowledge base personal (Qdrant via FastAPI)
  - ingest_doc: indexa un texto nuevo en la knowledge base

El servicio FastAPI corre en Docker en el puerto 8001.
"""

from __future__ import annotations

import json
import logging

import httpx

logger = logging.getLogger(__name__)

SKILL_BASE_URL = "http://localhost:8001"

# --- Schemas JSON (lo que ve el LLM) -----------------------------------------

SEARCH_MY_DOCS_SCHEMA = {
    "name": "search_my_docs",
    "description": (
        "Busca en la knowledge base personal de Pablo: documentos, papers, artículos y notas "
        "guardados previamente. Úsalo cuando el usuario pregunte sobre algo que guardó, "
        "o cuando la respuesta pueda estar en sus documentos personales en vez de en la web."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Consulta en lenguaje natural sobre el contenido buscado",
            },
            "limit": {
                "type": "integer",
                "description": "Cantidad de fragmentos a devolver (default: 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}

INGEST_DOC_SCHEMA = {
    "name": "ingest_doc",
    "description": (
        "Indexa un texto en la knowledge base personal de Pablo para poder buscarlo después. "
        "Úsalo cuando el usuario quiera guardar un documento, artículo o nota para referencia futura."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Texto completo a indexar",
            },
            "source": {
                "type": "string",
                "description": "Nombre o identificador del documento (ej: 'paper-rag-2024', 'notas-fastapi')",
            },
        },
        "required": ["text", "source"],
    },
}


# --- Handlers -----------------------------------------------------------------


def _handle_search_my_docs(args: dict, **kwargs) -> str:
    """Llama al endpoint /search del servicio FastAPI."""
    query = args.get("query", "")
    limit = args.get("limit", 5)

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                f"{SKILL_BASE_URL}/search",
                json={"query": query, "limit": limit},
            )
        response.raise_for_status()
        data = response.json()
    except httpx.ConnectError:
        return "❌ search_my_docs no disponible — el servicio Docker no está corriendo."
    except Exception as e:
        logger.error("search_my_docs error: %s", e)
        return f"❌ Error al buscar: {e}"

    results = data.get("results", [])
    if not results:
        return f"No encontré nada en la knowledge base para: '{query}'"

    # Formatear resultados para el LLM
    lines = [f"Encontré {len(results)} fragmentos relevantes para '{query}':\n"]
    for i, r in enumerate(results, 1):
        lines.append(
            f"[{i}] Fuente: {r['source']} (score: {r['score']:.2f})\n{r['text']}\n"
        )
    return "\n".join(lines)


def _handle_ingest_doc(args: dict, **kwargs) -> str:
    """Llama al endpoint /ingest del servicio FastAPI."""
    text = args.get("text", "")
    source = args.get("source", "unnamed")

    if not text.strip():
        return "❌ El texto está vacío."

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{SKILL_BASE_URL}/ingest",
                json={"text": text, "source": source},
            )
        response.raise_for_status()
        data = response.json()
    except httpx.ConnectError:
        return "❌ search_my_docs no disponible — el servicio Docker no está corriendo."
    except Exception as e:
        logger.error("ingest_doc error: %s", e)
        return f"❌ Error al indexar: {e}"

    return f"✅ '{source}' indexado: {data['chunks_indexed']} chunks guardados en la knowledge base."


# --- Register -----------------------------------------------------------------


def register(ctx) -> None:
    """Llamado por el plugin loader de Hermes al arrancar."""
    ctx.register_tool(
        name="search_my_docs",
        toolset="search-my-docs",
        schema=SEARCH_MY_DOCS_SCHEMA,
        handler=_handle_search_my_docs,
        emoji="🔎",
    )
    ctx.register_tool(
        name="ingest_doc",
        toolset="search-my-docs",
        schema=INGEST_DOC_SCHEMA,
        handler=_handle_ingest_doc,
        emoji="📥",
    )
    logger.info("Plugin search-my-docs: tools search_my_docs + ingest_doc registradas")
