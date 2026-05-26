"""Fuente: DuckDuckGo web search — cursos y certificaciones de AI recientes.

Cubre plataformas sin RSS (DeepLearning.AI, edX, Udemy, etc.) mediante
búsquedas web dirigidas. Los resultados se combinan con los de RSS en main.py
y se deduplicán por URL antes de devolver al cliente.

Estrategia de búsqueda:
  - 4 queries dirigidas a plataformas/compañías clave
  - timelimit='m' → solo resultados del último mes (filtro de DDG, no 100% exacto)
  - Keyword filter en título para confirmar que es realmente un curso/cert
  - asyncio.to_thread() porque duckduckgo-search es síncrono
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone

from duckduckgo_search import DDGS

from models.schemas import CourseEntry

logger = logging.getLogger(__name__)

# Queries diseñadas para encontrar anuncios de cursos recientes.
# Cada query apunta a una fuente/segmento diferente para maximizar cobertura.
WEB_COURSE_QUERIES = [
    "deeplearning.ai new course 2026",
    "new AI certification launch 2026",
    "new machine learning course announcement 2026",
    "NVIDIA DLI new certification 2026",
]

MAX_RESULTS_PER_QUERY = 4

# Mismo patrón de keywords con word boundaries que courses.py
_COURSE_PATTERN = re.compile(
    r"\b(course|certification|certificate|certif|workshop|bootcamp|"
    r"nanodegree|specialization|mooc|credential|learning path|enroll|"
    r"codelabs|online class|training program|training course|new class)\b",
    re.IGNORECASE,
)

_FREE_PATTERN = re.compile(
    r"\b(free|gratuito|gratis|no cost|open access|at no cost)\b",
    re.IGNORECASE,
)

# Mapa de dominio → nombre del provider para el output
_DOMAIN_PROVIDER = {
    "deeplearning.ai":  "DeepLearning.AI",
    "coursera.org":     "Coursera",
    "fast.ai":          "fast.ai",
    "nvidia.com":       "NVIDIA DLI",
    "udemy.com":        "Udemy",
    "edx.org":          "edX",
    "kaggle.com":       "Kaggle",
    "huggingface.co":   "HuggingFace",
    "aws.amazon.com":   "AWS",
    "microsoft.com":    "Microsoft",
    "google.com":       "Google",
}


def _extract_provider(url: str) -> str:
    """Extrae el nombre del provider a partir del dominio de la URL."""
    for domain, name in _DOMAIN_PROVIDER.items():
        if domain in url:
            return name
    # Fallback: segundo nivel del dominio (ej: "openai.com" → "openai")
    try:
        host = url.split("/")[2]  # "https://X.Y.Z/path" → "X.Y.Z"
        parts = host.split(".")
        return parts[-2].capitalize() if len(parts) >= 2 else host
    except Exception:
        return "Web"


def _is_course_title(title: str) -> bool:
    """True si el título del resultado menciona explícitamente un curso/cert."""
    return bool(_COURSE_PATTERN.search(title))


def _sync_search() -> list[CourseEntry]:
    """Ejecuta las búsquedas DDG de forma síncrona.

    Llamada via asyncio.to_thread() — no bloquea el event loop.
    """
    seen_urls: set[str] = set()
    courses: list[CourseEntry] = []

    try:
        with DDGS() as ddgs:
            for query in WEB_COURSE_QUERIES:
                try:
                    results = ddgs.text(
                        query,
                        max_results=MAX_RESULTS_PER_QUERY,
                        timelimit="m",  # último mes
                    )
                    for r in results:
                        url = r.get("href", "")
                        title = r.get("title", "").strip()
                        body = r.get("body", "")

                        # Deduplicar por URL
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        # Filtrar: solo si el título tiene keyword educativo
                        if not _is_course_title(title):
                            continue

                        provider = _extract_provider(url)
                        is_free = bool(_FREE_PATTERN.search(title + " " + body[:200]))

                        courses.append(CourseEntry(
                            title=title,
                            provider=f"{provider} (web)",
                            url=url,
                            published=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                            summary=body[:200] if body else "",
                            is_free=is_free,
                        ))

                except Exception as e:
                    logger.warning("DDG query '%s' falló: %s", query, e)
                    continue

    except Exception as e:
        logger.error("DDG web courses init error: %s", e)

    logger.info("Web courses (DDG): %d resultados", len(courses))
    return courses


async def fetch_web_courses() -> tuple[list[CourseEntry], str | None]:
    """Busca cursos nuevos de AI en la web via DuckDuckGo.

    Cubre plataformas sin RSS: DeepLearning.AI, Udemy, edX, etc.
    Devuelve (lista de CourseEntry, error_string | None).
    """
    try:
        courses = await asyncio.to_thread(_sync_search)
        return courses, None
    except Exception as e:
        logger.error("fetch_web_courses falló: %s", e)
        return [], f"Web search: {e}"
