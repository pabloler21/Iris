"""Pydantic schemas para la skill search_my_docs."""

from pydantic import BaseModel, Field
from typing import Optional


class SearchRequest(BaseModel):
    query: str = Field(..., description="Consulta en lenguaje natural")
    limit: int = Field(default=5, ge=1, le=20, description="Cantidad máxima de resultados")
    collection: str = Field(default="docs", description="Colección de Qdrant a consultar")


class SearchResult(BaseModel):
    text: str = Field(..., description="Fragmento de texto relevante")
    score: float = Field(..., description="Score de similitud (0-1)")
    source: str = Field(..., description="Nombre o path del documento origen")
    chunk_index: int = Field(..., description="Índice del chunk dentro del documento")


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total_found: int


class IngestRequest(BaseModel):
    text: str = Field(..., description="Texto completo a indexar")
    source: str = Field(..., description="Nombre o identificador del documento (ej: 'paper-rag-2024.pdf')")
    collection: str = Field(default="docs", description="Colección de Qdrant donde indexar")
    chunk_size: int = Field(default=500, ge=100, le=2000, description="Tokens aproximados por chunk")
    chunk_overlap: int = Field(default=50, ge=0, le=200, description="Tokens de overlap entre chunks")


class IngestResponse(BaseModel):
    source: str
    chunks_indexed: int
    collection: str
    message: str
