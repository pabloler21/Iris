"""
search_my_docs — Skill RAG para Iris.

Endpoints:
  GET  /health          — healthcheck
  POST /search          — busca chunks relevantes en Qdrant
  POST /ingest          — indexa un texto en Qdrant (chunking + embedding)
  GET  /collections     — lista colecciones disponibles en Qdrant
"""

import logging
import os
import uuid
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from models.schemas import (
    IngestRequest,
    IngestResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)

# --- Config -------------------------------------------------------------------

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")
EMBEDDING_DIM = 1536  # dimensión fija de text-embedding-3-small

logger = logging.getLogger(__name__)

# --- App ----------------------------------------------------------------------

app = FastAPI(
    title="search_my_docs",
    description="Skill RAG: indexa documentos en Qdrant y los busca por similitud semántica.",
    version="1.0.0",
)

# Cliente Qdrant — reutilizado en todos los requests
qdrant = QdrantClient(url=QDRANT_URL)


# --- Helpers ------------------------------------------------------------------


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Divide texto en chunks por palabras, con overlap.

    chunk_size y overlap están en palabras (aproximación a tokens).
    """
    words = text.split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


async def _get_embedding(text: str) -> list[float]:
    """Genera embedding via OpenRouter (compatible con OpenAI API)."""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY no configurada")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": EMBEDDING_MODEL,
                "input": text,
            },
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"OpenRouter embeddings error {response.status_code}: {response.text[:200]}",
        )

    data = response.json()
    return data["data"][0]["embedding"]


def _ensure_collection(collection: str) -> None:
    """Crea la colección en Qdrant si no existe."""
    existing = {c.name for c in qdrant.get_collections().collections}
    if collection not in existing:
        qdrant.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        logger.info("Colección '%s' creada en Qdrant", collection)


# --- Endpoints ----------------------------------------------------------------


@app.get("/health")
def health() -> dict[str, Any]:
    """Healthcheck: verifica conexión con Qdrant."""
    try:
        qdrant.get_collections()
        qdrant_ok = True
    except Exception as e:
        qdrant_ok = False
        logger.warning("Qdrant no disponible: %s", e)

    return {
        "status": "ok" if qdrant_ok else "degraded",
        "qdrant": "connected" if qdrant_ok else "unreachable",
        "embedding_model": EMBEDDING_MODEL,
    }


@app.get("/collections")
def list_collections() -> dict[str, Any]:
    """Lista las colecciones disponibles en Qdrant con su cantidad de puntos."""
    collections = qdrant.get_collections().collections
    result = []
    for col in collections:
        info = qdrant.get_collection(col.name)
        result.append({
            "name": col.name,
            "points": info.points_count,
        })
    return {"collections": result}


@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    """Busca chunks relevantes para una query en lenguaje natural."""
    # Generar embedding de la query
    query_vector = await _get_embedding(req.query)

    # Verificar que la colección existe
    existing = {c.name for c in qdrant.get_collections().collections}
    if req.collection not in existing:
        return SearchResponse(query=req.query, results=[], total_found=0)

    # Buscar en Qdrant
    hits = qdrant.search(
        collection_name=req.collection,
        query_vector=query_vector,
        limit=req.limit,
        with_payload=True,
    )

    results = [
        SearchResult(
            text=hit.payload.get("text", ""),
            score=hit.score,
            source=hit.payload.get("source", "unknown"),
            chunk_index=hit.payload.get("chunk_index", 0),
        )
        for hit in hits
    ]

    return SearchResponse(
        query=req.query,
        results=results,
        total_found=len(results),
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest) -> IngestResponse:
    """Indexa un texto en Qdrant: chunking → embedding → upsert."""
    _ensure_collection(req.collection)

    # Dividir en chunks
    chunks = _chunk_text(req.text, req.chunk_size, req.chunk_overlap)
    logger.info("Ingesta '%s': %d chunks (size=%d, overlap=%d)",
                req.source, len(chunks), req.chunk_size, req.chunk_overlap)

    # Generar embeddings y construir puntos para Qdrant
    points: list[PointStruct] = []
    for i, chunk in enumerate(chunks):
        vector = await _get_embedding(chunk)
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": chunk,
                    "source": req.source,
                    "chunk_index": i,
                },
            )
        )

    # Upsert en Qdrant (batch de hasta 100 puntos)
    batch_size = 100
    for i in range(0, len(points), batch_size):
        qdrant.upsert(
            collection_name=req.collection,
            points=points[i : i + batch_size],
        )

    logger.info("Ingesta completada: %d chunks indexados en '%s'", len(chunks), req.collection)
    return IngestResponse(
        source=req.source,
        chunks_indexed=len(chunks),
        collection=req.collection,
        message=f"{len(chunks)} chunks indexados correctamente.",
    )
