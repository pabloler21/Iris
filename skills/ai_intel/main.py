"""
ai_intel — Skill de inteligencia sobre novedades en AI.

Endpoints:
  GET /health
  GET /models?days=7    — modelos nuevos (OpenRouter + HuggingFace)
  GET /repos?days=7     — repos trending en AI (GitHub)
  GET /news?days=7      — noticias de blogs de compañías de AI
  GET /courses?days=7   — cursos y certificaciones: RSS + búsqueda web (DDG)
  GET /summary?days=7   — todo junto (el que usa Iris por defecto)
"""

import asyncio
import logging
from typing import Any

from fastapi import FastAPI, Query

from models.schemas import IntelResponse, CourseEntry
from sources.openrouter import fetch_new_models as or_models
from sources.huggingface import fetch_new_models as hf_models
from sources.github import fetch_trending_repos
from sources.rss_feeds import fetch_news
from sources.courses import fetch_new_courses
from sources.web_courses import fetch_web_courses

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ai_intel",
    description="Skill RAG: novedades de AI — modelos, repos, noticias, cursos.",
    version="1.2.0",
)


# --- Health -------------------------------------------------------------------

@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "ai_intel"}


# --- Helpers ------------------------------------------------------------------

def _merge_courses(
    rss: list[CourseEntry],
    web: list[CourseEntry],
) -> list[CourseEntry]:
    """Combina cursos RSS + web, deduplica por URL, ordena por fecha DESC."""
    seen: set[str] = set()
    merged: list[CourseEntry] = []

    for c in rss + web:
        key = c.url or c.title  # fallback a título si no hay URL
        if key in seen:
            continue
        seen.add(key)
        merged.append(c)

    merged.sort(key=lambda x: x.published, reverse=True)
    return merged


# --- Endpoints individuales ---------------------------------------------------

@app.get("/models", response_model=IntelResponse)
async def get_models(days: int = Query(default=7, ge=1, le=30)) -> IntelResponse:
    """Modelos nuevos en OpenRouter y HuggingFace."""
    (or_list, or_err), (hf_list, hf_err) = await asyncio.gather(
        or_models(days),
        hf_models(days),
    )
    errors = [e for e in [or_err, hf_err] if e]
    combined = or_list + hf_list  # OpenRouter primero (tiene pricing)
    return IntelResponse(type="models", days=days, models=combined, errors=errors)


@app.get("/repos", response_model=IntelResponse)
async def get_repos(days: int = Query(default=7, ge=1, le=30)) -> IntelResponse:
    """Repos trending en AI/LLM en GitHub."""
    repos, error = await fetch_trending_repos(days)
    errors = [error] if error else []
    return IntelResponse(type="repos", days=days, repos=repos, errors=errors)


@app.get("/news", response_model=IntelResponse)
async def get_news(days: int = Query(default=7, ge=1, le=30)) -> IntelResponse:
    """Noticias de blogs de compañías de AI (OpenAI, DeepMind, Anthropic, etc.)."""
    news, feed_errors = await fetch_news(days)
    return IntelResponse(type="news", days=days, news=news, errors=feed_errors)


@app.get("/courses", response_model=IntelResponse)
async def get_courses(days: int = Query(default=7, ge=1, le=30)) -> IntelResponse:
    """Cursos y certificaciones: RSS feeds + búsqueda web (DuckDuckGo).

    Combina resultados de ambas fuentes y deduplica por URL.
    La búsqueda web cubre plataformas sin RSS (DeepLearning.AI, edX, Udemy, etc.).
    """
    (rss_courses, rss_errs), (web_courses, web_err) = await asyncio.gather(
        fetch_new_courses(days),
        fetch_web_courses(),
    )
    all_courses = _merge_courses(rss_courses, web_courses)
    errors = rss_errs + ([web_err] if web_err else [])

    logger.info(
        "Courses [%d días]: %d RSS + %d web = %d total",
        days, len(rss_courses), len(web_courses), len(all_courses),
    )
    return IntelResponse(type="courses", days=days, courses=all_courses, errors=errors)


# --- Endpoint principal (el que usa Iris) -------------------------------------

@app.get("/summary", response_model=IntelResponse)
async def get_summary(days: int = Query(default=7, ge=1, le=30)) -> IntelResponse:
    """Todo junto: modelos + repos + noticias + cursos de los últimos N días."""
    (
        (or_list, or_err),
        (hf_list, hf_err),
        (repos, repo_err),
        (news, feed_errs),
        (rss_courses, rss_errs),
        (web_courses_list, web_err),
    ) = await asyncio.gather(
        or_models(days),
        hf_models(days),
        fetch_trending_repos(days),
        fetch_news(days),
        fetch_new_courses(days),
        fetch_web_courses(),
    )

    errors = [e for e in [or_err, hf_err, repo_err, web_err] if e] + feed_errs + rss_errs
    models = or_list + hf_list
    courses = _merge_courses(rss_courses, web_courses_list)

    logger.info(
        "Summary [%d días]: %d modelos, %d repos, %d noticias, %d cursos, %d errores",
        days, len(models), len(repos), len(news), len(courses), len(errors),
    )
    return IntelResponse(
        type="all",
        days=days,
        models=models,
        repos=repos,
        news=news,
        courses=courses,
        errors=errors,
    )
