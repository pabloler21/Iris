"""Fuente: DuckDuckGo Lite — cursos y certificaciones de AI recientes.

Usa el endpoint `https://lite.duckduckgo.com/lite/` con httpx directamente,
sin depender de la librería duckduckgo-search que requiere curl-cffi con
perfiles de browser válidos (no disponibles en Docker slim).

DDG Lite es un endpoint de texto plano sin JS, no rate-limita de la misma
forma que los otros backends.

Cubre plataformas sin RSS: DeepLearning.AI, edX, Udemy, etc.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from html.parser import HTMLParser

import httpx

from models.schemas import CourseEntry

logger = logging.getLogger(__name__)

DDG_LITE_URL = "https://lite.duckduckgo.com/lite/"

# Queries: pocas, específicas, con año para filtrar semánticamente
WEB_COURSE_QUERIES = [
    "deeplearning.ai new AI course 2026",
    "new AI certification course launch 2026",
]

MAX_RESULTS_PER_QUERY = 5

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
}


def _extract_provider(url: str) -> str:
    for domain, name in _DOMAIN_PROVIDER.items():
        if domain in url:
            return name
    try:
        host = url.split("/")[2]
        parts = host.split(".")
        return parts[-2].capitalize() if len(parts) >= 2 else host
    except Exception:
        return "Web"


class _DDGLiteParser(HTMLParser):
    """Parser minimal para extraer resultados de DDG Lite."""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict] = []
        self._in_result_link = False
        self._current_href = ""
        self._current_title = ""
        self._in_snippet = False
        self._current_snippet = ""
        self._td_class = ""

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attr_dict = dict(attrs)
        if tag == "a" and "uddg" in attr_dict.get("href", ""):
            self._in_result_link = True
            self._current_href = attr_dict.get("href", "")
            self._current_title = ""
        elif tag == "td":
            self._td_class = attr_dict.get("class", "")
            if "result-snippet" in self._td_class:
                self._in_snippet = True
                self._current_snippet = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_result_link:
            self._in_result_link = False
        elif tag == "td" and self._in_snippet:
            self._in_snippet = False
            if self._current_href and self._current_title:
                self.results.append({
                    "href": self._current_href,
                    "title": self._current_title.strip(),
                    "body": self._current_snippet.strip(),
                })

    def handle_data(self, data: str) -> None:
        if self._in_result_link:
            self._current_title += data
        elif self._in_snippet:
            self._current_snippet += data


async def _search_ddg_lite(query: str) -> list[dict]:
    """Llama a DDG Lite con httpx y parsea los resultados HTML."""
    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) "
                    "Gecko/20100101 Firefox/125.0"
                ),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as client:
            response = await client.post(
                DDG_LITE_URL,
                data={"q": query, "kl": "en-us"},
            )
        response.raise_for_status()

        parser = _DDGLiteParser()
        parser.feed(response.text)
        return parser.results[:MAX_RESULTS_PER_QUERY]

    except Exception as e:
        logger.warning("DDG Lite query '%s' falló: %s", query, e)
        return []


async def fetch_web_courses() -> tuple[list[CourseEntry], str | None]:
    """Busca cursos nuevos de AI en DuckDuckGo Lite.

    Cubre plataformas sin RSS: DeepLearning.AI, Udemy, edX, etc.
    Retorna (lista de CourseEntry, error_string | None).
    """
    seen_urls: set[str] = set()
    courses: list[CourseEntry] = []

    for query in WEB_COURSE_QUERIES:
        results = await _search_ddg_lite(query)
        for r in results:
            url = r.get("href", "")
            title = r.get("title", "").strip()
            body = r.get("body", "")

            if url in seen_urls:
                continue
            seen_urls.add(url)

            if not _COURSE_PATTERN.search(title):
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

    logger.info("Web courses (DDG Lite): %d resultados", len(courses))
    return courses, None
