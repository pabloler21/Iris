"""Fuente: GitHub Search API — repos trending en AI/LLM (sin API key)."""

import logging
from datetime import datetime, timezone, timedelta

import httpx

from models.schemas import RepoEntry

logger = logging.getLogger(__name__)

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

# Topics de AI/LLM para buscar repos relevantes
AI_TOPICS = ["llm", "large-language-model", "ai", "generative-ai", "machine-learning"]


async def fetch_trending_repos(days: int = 7, limit: int = 10) -> tuple[list[RepoEntry], str | None]:
    """Devuelve repos de AI/LLM creados o con stars recientes en los últimos `days` días.

    Usa la GitHub Search API pública (60 req/hora sin key, suficiente para uso personal).
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    # Buscar repos creados recientemente con topics de AI, ordenados por estrellas
    query = f"topic:llm+topic:ai created:>{cutoff}"

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            headers={"Accept": "application/vnd.github.v3+json"},
        ) as client:
            response = await client.get(
                GITHUB_SEARCH_URL,
                params={
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": limit,
                },
            )
        response.raise_for_status()
    except Exception as e:
        logger.error("GitHub API error: %s", e)
        return [], f"GitHub: {e}"

    repos: list[RepoEntry] = []
    for item in response.json().get("items", []):
        repos.append(RepoEntry(
            name=item.get("full_name", ""),
            description=(item.get("description") or "")[:200],
            stars=item.get("stargazers_count", 0),
            url=item.get("html_url", ""),
            language=item.get("language") or "N/A",
            created_date=item.get("created_at", "")[:10],
        ))

    logger.info("GitHub: %d repos nuevos en los últimos %d días", len(repos), days)
    return repos, None
