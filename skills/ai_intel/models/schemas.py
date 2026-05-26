"""Pydantic schemas para la skill ai_intel."""

from pydantic import BaseModel, Field
from typing import Literal


class ModelEntry(BaseModel):
    name: str
    provider: str
    context_k: int = Field(description="Context window en miles de tokens")
    price_input: float = Field(description="$/M tokens input")
    price_output: float = Field(description="$/M tokens output")
    created_date: str


class RepoEntry(BaseModel):
    name: str
    description: str
    stars: int
    url: str
    language: str
    created_date: str


class NewsEntry(BaseModel):
    title: str
    source: str
    url: str
    published: str
    summary: str = ""


class CourseEntry(BaseModel):
    title: str
    provider: str          # "DeepLearning.AI", "NVIDIA DLI", "Coursera", etc.
    url: str
    published: str         # YYYY-MM-DD
    summary: str = ""
    is_free: bool = False  # True si se detectó keyword de gratuidad en título/summary


class IntelResponse(BaseModel):
    type: Literal["models", "repos", "news", "courses", "all"]
    days: int
    models: list[ModelEntry] = []
    repos: list[RepoEntry] = []
    news: list[NewsEntry] = []
    courses: list[CourseEntry] = []
    errors: list[str] = Field(default_factory=list, description="Fuentes que fallaron")
