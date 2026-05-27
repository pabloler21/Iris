"""
ai_intel — Skill de inteligencia sobre novedades en AI.

Endpoints:
  GET /health
  GET /models?days=7    — modelos nuevos (OpenRouter + HuggingFace)
  GET /repos?days=7     — repos trending en AI (GitHub)
  GET /news?days=7      — noticias de blogs de compañías de AI
  GET /courses?days=7   — cursos y certificaciones: RSS feeds de plataformas educativas
  GET /summary?days=7   — todo junto (el que usa Iris por defecto)
  GET /digest?days=7    — digest pre-formateado para Discord (usado por el cron semanal)

Nota sobre cursos:
  Esta skill monitorea RSS de NVIDIA DLI, Coursera, fast.ai, Google Dev, AWS ML.
  DeepLearning.AI NO tiene RSS → usar web_search para esa plataforma.
"""

import asyncio
import logging
from typing import Any

from fastapi import FastAPI, Query

from models.schemas import IntelResponse, DigestResponse
from digest import format_discord_digest
from smart_digest import call_kimi_curator
from sources.openrouter import fetch_new_models as or_models
from sources.huggingface import fetch_new_models as hf_models
from sources.github import fetch_trending_repos
from sources.rss_feeds import fetch_news
from sources.courses import fetch_new_courses

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ai_intel",
    description="Skill RAG: novedades de AI — modelos, repos, noticias, cursos.",
    version="2.0.0",
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


# --- Digest para cron semanal -------------------------------------------------

@app.get("/digest", response_model=DigestResponse)
async def get_digest(days: int = Query(default=7, ge=1, le=14)) -> DigestResponse:
    """Digest pre-formateado para Discord — usado por el cron semanal de Hermes.

    Llama a todas las fuentes en paralelo y devuelve mensajes listos para enviar,
    cada uno garantizado < 1900 chars. Diseñado para el modo --no-agent de Hermes.
    """
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

    data = {
        "models": [m.model_dump() for m in models],
        "repos": [r.model_dump() for r in repos],
        "news": [n.model_dump() for n in news],
        "courses": [c.model_dump() for c in courses],
        "errors": errors,
    }

    messages = format_discord_digest(data, days=days)

    logger.info(
        "Digest [%d días]: %d modelos, %d repos, %d noticias, %d cursos → %d mensaje(s)",
        days, len(models), len(repos), len(news), len(courses), len(messages),
    )

    return DigestResponse(
        messages=messages,
        stats={
            "models": len(models),
            "repos": len(repos),
            "news": len(news),
            "courses": len(courses),
        },
    )


@app.get("/digest-smart", response_model=DigestResponse)
async def get_digest_smart(days: int = Query(default=7, ge=1, le=14)) -> DigestResponse:
    """Digest curado por Kimi K2.6 — newsletter personalizado para Pablo.

    Kimi lee todo el feed de la semana y selecciona los items más relevantes
    para un AI Engineer Jr, agregando una línea de 'por qué importa' por item.

    Fallback automático a /digest si Kimi no responde (timeout o error).
    """
    # Fetch en paralelo (igual que /digest)
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

    data = {
        "models": [m.model_dump() for m in models],
        "repos": [r.model_dump() for r in repos],
        "news": [n.model_dump() for n in news],
        "courses": [c.model_dump() for c in courses],
        "errors": errors,
    }

    logger.info(
        "Digest-smart [%d días]: %d modelos, %d repos, %d noticias, %d cursos",
        days, len(models), len(repos), len(news), len(courses),
    )

    # Llamar a Kimi para curaduría
    curated_text = await call_kimi_curator(data, days=days)

    if curated_text:
        # Kimi respondió — usar su texto directamente
        logger.info("Digest-smart: curaduría Kimi exitosa (%d chars)", len(curated_text))
        messages = [curated_text]
    else:
        # Fallback: usar el formatter determinístico
        logger.warning("Digest-smart: Kimi falló, usando fallback digest.py")
        messages = format_discord_digest(data, days=days)

    return DigestResponse(
        messages=messages,
        stats={
            "models": len(models),
            "repos": len(repos),
            "news": len(news),
            "courses": len(courses),
            "curated_by_llm": curated_text is not None,
        },
    )
