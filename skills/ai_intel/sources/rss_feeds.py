"""Fuente: RSS feeds de blogs de compañías de AI y newsletters.

Feeds incluidos (todos verificados con URL funcional):
  Compañías:
  - OpenAI            (oficial)
  - Google DeepMind   (oficial)
  - Google AI Blog    (oficial, via blog.google)
  - HuggingFace Blog  (oficial)

  Newsletters / Blogs editorializados (alta señal):
  - TLDR AI           (newsletter diario curado, muy completo)
  - Simon Willison    (blog diario, herramientas AI prácticas para developers)
  - Interconnects     (Nathan Lambert — análisis mensual de tendencias LLM)
  - Ahead of AI       (Sebastian Raschka — deep dives en arquitecturas LLM)

Notas:
  - Anthropic: sin RSS oficial → excluido
  - Meta AI: sin RSS funcional → excluido
  - xAI: sin RSS → excluido
  - The Batch (DL.AI): RSS no funcional (404) → excluido
  - ArXiv cs.AI: REMOVIDO — demasiado volumen (500 papers/día), mucho ruido académico
  - Hacker News AI: REMOVIDO — demasiado ruido, falsos positivos frecuentes
"""

import logging
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from models.schemas import NewsEntry

logger = logging.getLogger(__name__)

# Cada feed tiene url y limit_per_fetch (items max por llamada).
# Simon Willison publica ~5 posts/día (links cortos + ensayos) → límite 3
# para no inundar el digest con citas y links triviales.
# Interconnects y Ahead of AI son mensuales → sin límite práctico (limit=10).
RSS_FEEDS: dict[str, dict] = {
    "OpenAI": {
        "url":   "https://openai.com/news/rss.xml",
        "limit": 4,
    },
    "Google DeepMind": {
        "url":   "https://deepmind.google/blog/rss.xml",
        "limit": 4,
    },
    "Google AI": {
        "url":   "https://blog.google/technology/ai/rss/",
        "limit": 3,
    },
    "HuggingFace Blog": {
        "url":   "https://huggingface.co/blog/feed.xml",
        "limit": 4,
    },
    "TLDR AI": {
        "url":   "https://tldr.tech/api/rss/ai",
        "limit": 3,
    },
    "Simon Willison": {
        "url":   "https://simonwillison.net/atom/everything/",
        "limit": 3,
    },
    "Interconnects": {
        "url":   "https://www.interconnects.ai/feed",
        "limit": 10,
    },
    "Ahead of AI": {
        "url":   "https://magazine.sebastianraschka.com/feed",
        "limit": 10,
    },
}


def _parse_date(entry) -> datetime | None:
    """Intenta parsear la fecha de una entrada RSS."""
    for field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    for field in ("published", "updated"):
        raw = getattr(entry, field, "")
        if raw:
            try:
                return parsedate_to_datetime(raw).astimezone(timezone.utc)
            except Exception:
                pass
    return None


def _clean_html(text: str, max_len: int = 250) -> str:
    """Remueve tags HTML y trunca."""
    clean = re.sub(r"<[^>]+>", "", str(text)).strip()
    clean = re.sub(r"\s+", " ", clean)
    return clean[:max_len] + ("…" if len(clean) > max_len else "")


async def _fetch_feed(name: str, url: str) -> list[feedparser.FeedParserDict]:
    """Descarga y parsea un feed RSS."""
    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": "Iris-AI-Intel/1.0 (personal AI assistant)"},
        ) as client:
            response = await client.get(url)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        return feed.entries
    except Exception as e:
        logger.warning("RSS feed '%s' falló: %s", name, e)
        return []


async def fetch_news(days: int = 7) -> tuple[list[NewsEntry], list[str]]:
    """Lee todos los feeds y devuelve noticias de los últimos `days` días.

    Cada feed tiene su propio límite de items definido en RSS_FEEDS.

    Returns:
        (lista de noticias ordenadas por fecha DESC, lista de feeds con error)
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    all_news: list[NewsEntry] = []
    errors: list[str] = []

    for source_name, config in RSS_FEEDS.items():
        url = config["url"]
        limit = config.get("limit", 4)

        entries = await _fetch_feed(source_name, url)
        if not entries:
            errors.append(f"{source_name}: sin respuesta")
            continue

        count = 0
        for entry in entries:
            published = _parse_date(entry)
            if published and published < cutoff:
                continue

            title = getattr(entry, "title", "Sin título").strip()
            link = getattr(entry, "link", "")

            # Extraer summary limpio
            summary = ""
            for field in ("summary", "description"):
                raw = getattr(entry, field, "")
                if isinstance(raw, list) and raw:
                    raw = raw[0].get("value", "")
                if raw:
                    summary = _clean_html(raw)
                    break

            date_str = published.strftime("%Y-%m-%d") if published else "fecha desconocida"

            all_news.append(NewsEntry(
                title=title,
                source=source_name,
                url=link,
                published=date_str,
                summary=summary,
            ))
            count += 1
            if count >= limit:
                break

        logger.info("RSS '%s': %d entradas recientes", source_name, count)

    # Ordenar del más reciente al más viejo
    all_news.sort(key=lambda x: x.published, reverse=True)
    return all_news, errors
