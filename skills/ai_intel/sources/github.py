"""Fuente: GitHub Search API — repos trending en AI/LLM (sin API key).

Estrategia: búsqueda en 3 topics de AI distintos (llm, generative-ai,
large-language-model) para mayor cobertura. Los resultados se combinan
y deduplicación por repo name. Requiere stars:>2 para filtrar repos vacíos.
"""

import logging
from datetime import datetime, timezone, timedelta

import httpx

from models.schemas import RepoEntry

logger = logging.getLogger(__name__)

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

# Topics específicos de AI — separados para evitar AND implícito del query
AI_TOPICS = [
    "llm",
    "generative-ai",
    "large-language-model",
]


async def _search_topic(
    client: httpx.AsyncClient,
    topic: str,
    cutoff: str,
    per_page: int = 10,
) -> list[dict]:
    """Busca repos por un topic específico creados a partir de `cutoff`."""
    try:
        response = await client.get(
            GITHUB_SEARCH_URL,
            params={
                "q": f"topic:{topic} created:>{cutoff} stars:>2",
                "sort": "stars",
                "order": "desc",
                "per_page": per_page,
            },
        )
        response.raise_for_status()
        return response.json().get("items", [])
    except Exception as e:
        logger.warning("GitHub topic '%s' falló: %s", topic, e)
        return []


async def fetch_trending_repos(days: int = 7, limit: int = 10) -> tuple[list[RepoEntry], str | None]:
    """Devuelve repos de AI/LLM creados en los últimos `days` días con tracción.

    Combina resultados de 3 topics distintos y deduplica por nombre completo.
    Requiere al menos 3 estrellas para filtrar repos vacíos/spam.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            headers={"Accept": "application/vnd.github.v3+json"},
        ) as client:
            # Buscar en los 3 topics en paralelo usando asyncio.gather implícito
            # (httpx async client, llamadas secuenciales pero rápidas)
            all_items: list[dict] = []
            for topic in AI_TOPICS:
                items = await _search_topic(client, topic, cutoff)
                all_items.extend(items)
    except Exception as e:
        logger.error("GitHub API error: %s", e)
        return [], f"GitHub: {e}"

    # Deduplicar por full_name y ordenar por estrellas
    seen: set[str] = set()
    repos: list[RepoEntry] = []

    for item in sorted(all_items, key=lambda x: x.get("stargazers_count", 0), reverse=True):
        full_name = item.get("full_name", "")
        if full_name in seen:
            continue
        seen.add(full_name)

        repos.append(RepoEntry(
            name=full_name,
            description=(item.get("description") or "Sin descripción")[:200],
            stars=item.get("stargazers_count", 0),
            url=item.get("html_url", ""),
            language=item.get("language") or "N/A",
            created_date=item.get("created_at", "")[:10],
        ))

        if len(repos) >= limit:
            break

    logger.info("GitHub: %d repos en los últimos %d días (3 topics, deduplicado)", len(repos), days)
    return repos, None
