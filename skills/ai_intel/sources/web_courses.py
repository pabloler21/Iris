"""Fuente: GitHub org search — repos de organizaciones educativas de AI.

Estrategia alternativa a web search (que falla desde Docker por rate limiting de DDG).

Cubre:
  - deeplearning-ai (DeepLearning.AI) — cada curso nuevo tiene un repo con el código
  - microsoft (cursos de Azure AI / Phi / SLMs en su org de GitHub)

Cuando DeepLearning.AI lanza un nuevo curso, casi siempre publica el repo
de código en github.com/deeplearning-ai con un nombre descriptivo.
El nombre del repo se convierte en el título del curso (snake_case → Title Case).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

import httpx

from models.schemas import CourseEntry

logger = logging.getLogger(__name__)

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

# Organizaciones de GitHub que publican repos de cursos de AI
COURSE_ORGS = {
    "deeplearning-ai": "DeepLearning.AI",
    "microsoft":       "Microsoft",
}

# Palabras que confirman que el repo es un curso (en nombre o descripción)
COURSE_REPO_KEYWORDS = {
    "course", "tutorial", "lab", "workshop", "lesson", "learn",
    "beginner", "hands-on", "guide", "bootcamp",
}

# Repos de microsoft que son cursos (keywords para filtrar su org grande)
MICROSOFT_COURSE_KEYWORDS = {
    "course", "tutorial", "learn", "generative-ai", "phi",
    "llm", "workshop", "beginner",
}


def _repo_name_to_title(name: str) -> str:
    """Convierte nombre de repo a título legible.

    Ejemplos:
      'building-systems-with-chatgpt-api' → 'Building Systems With Chatgpt Api'
      'langchain-for-llm-application-development' → 'Langchain For Llm Application Development'
    """
    return name.replace("-", " ").replace("_", " ").title()


def _is_course_repo(item: dict, org: str) -> bool:
    """True si el repo parece un curso/tutorial de AI."""
    name = (item.get("name") or "").lower()
    desc = (item.get("description") or "").lower()
    combined = name + " " + desc

    if org == "deeplearning-ai":
        # Todos los repos de deeplearning-ai son cursos o materiales de cursos
        return True

    if org == "microsoft":
        # Microsoft tiene miles de repos — filtrar solo cursos
        return any(kw in combined for kw in MICROSOFT_COURSE_KEYWORDS)

    return any(kw in combined for kw in COURSE_REPO_KEYWORDS)


async def _fetch_org_courses(
    client: httpx.AsyncClient,
    org: str,
    provider: str,
    cutoff: str,
    limit: int = 5,
) -> list[CourseEntry]:
    """Busca repos nuevos de una org en GitHub."""
    try:
        response = await client.get(
            GITHUB_SEARCH_URL,
            params={
                "q": f"org:{org} created:>{cutoff}",
                "sort": "updated",
                "order": "desc",
                "per_page": 20,
            },
        )
        response.raise_for_status()
        items = response.json().get("items", [])
    except Exception as e:
        logger.warning("GitHub org '%s' falló: %s", org, e)
        return []

    courses: list[CourseEntry] = []
    for item in items:
        if not _is_course_repo(item, org):
            continue

        name = item.get("name", "")
        title = _repo_name_to_title(name)
        # Prefijo del provider solo si no es ya evidente en el título
        display_title = f"{title}"

        courses.append(CourseEntry(
            title=display_title,
            provider=f"{provider} (GitHub)",
            url=item.get("html_url", ""),
            published=item.get("created_at", "")[:10],
            summary=(item.get("description") or "")[:200],
            is_free=True,  # repos de GitHub son gratuitos por definición
        ))

        if len(courses) >= limit:
            break

    logger.info("GitHub org '%s': %d repos de cursos en el período", org, len(courses))
    return courses


async def fetch_web_courses() -> tuple[list[CourseEntry], str | None]:
    """Busca repos de cursos nuevos en organizaciones educativas de AI en GitHub.

    Cubre DeepLearning.AI y Microsoft (AI courses), que no tienen RSS.
    Usa la GitHub Search API (sin API key, límite 60 req/hora).
    """
    # días fijo: cursos no se lanzan tan seguido → ventana de 14 días
    days = 14
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    all_courses: list[CourseEntry] = []

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            headers={"Accept": "application/vnd.github.v3+json"},
        ) as client:
            for org, provider in COURSE_ORGS.items():
                courses = await _fetch_org_courses(client, org, provider, cutoff)
                all_courses.extend(courses)
    except Exception as e:
        logger.error("fetch_web_courses (GitHub) error: %s", e)
        return [], f"GitHub courses: {e}"

    all_courses.sort(key=lambda x: x.published, reverse=True)
    return all_courses, None
