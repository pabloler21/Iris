"""
ai_intel — Skill de inteligencia sobre novedades en AI.

Endpoints:
  GET /health
  GET /models?days=7    — modelos nuevos (OpenRouter + HuggingFace)
  GET /repos?days=7     — repos trending en AI (GitHub)
  GET /news?days=7      — noticias de blogs de compañías de AI
  GET /courses?days=7   — cursos y certificaciones: RSS feeds de plataformas educativas
  GET /summary?days=7   — todo junto (el que usa Iris por defecto)

Nota sobre cursos:
  Esta skill monitorea RSS de NVIDIA DLI, Coursera, fast.ai, Google Dev, AWS ML.
  DeepLearning.AI NO tiene RSS → usar web_search para esa plataforma.
"""

import asyncio
import logging
from typing import Any

from fastapi import FastAPI, Query

from models.schemas import IntelResponse
from sources.openrouter import fetch_new_models as or_models
from sources.huggingface import fetch_new_models as hf_models
from sources.github import fetch_trending_repos
from sources.rss_feeds import fetch_news
from sources.courses import fetch_new_courses

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
    """Cursos y certificaciones: RSS de NVIDIA DLI, Coursera, fast.ai, Google Dev, AWS ML."""
    courses, feed_errors = await fetch_new_courses(days)
    return IntelResponse(type="courses", days=days, courses=courses, errors=feed_errors)


# --- Endpoint principal (el que usa Iris) -------------------------------------

@app.get("/summary", response_model=IntelResponse)
async def get_summary(days: int = Query(default=7, ge=1, le=30)) -> IntelResponse:
    """Todo junto: modelos + repos + noticias + cursos de los últimos N días."""
    (
        (or_list, or_err),
        (hf_list, hf_err),
        (repos, repo_err),
        (news, feed_errs),
        (courses, course_errs),
    ) = await asyncio.gather(
        or_models(days),
        hf_models(days),
        fetch_trending_repos(days),
        fetch_news(days),
        fetch_new_courses(days),
    )
    errors = [e for e in [or_err, hf_err, repo_err] if e] + feed_errs + course_errs
    models = or_list + hf_list

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
