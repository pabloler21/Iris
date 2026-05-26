"""Fuente: RSS feeds de blogs de compañías de AI y newsletters.

Feeds incluidos:
  - OpenAI          (oficial)
  - Google DeepMind (oficial)
  - Google AI Blog  (oficial)
  - Anthropic       (community feed — no hay RSS oficial)
  - Meta AI         (community feed)
  - TLDR AI         (newsletter digest, muy completo)
  - ArXiv cs.AI     (papers recientes)
"""

import logging
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from models.schemas import NewsEntry

logger = logging.getLogger(__name__)

RSS_FEEDS = {
    "OpenAI":         "https://openai.com/news/rss.xml",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    "Google AI":      "https://ai.googleblog.com/feeds/posts/default",
    "Anthropic":      "https://www.anthropic.com/rss.xml",
    "Meta AI":        "https://ai.meta.com/blog/feed/",
    "TLDR AI":        "https://actions.tldrnewsletter.com/web-feed?feed=tldrAI",
    "ArXiv cs.AI":    "https://rss.arxiv.org/rss/cs.AI",
}


def _parse_date(entry) -> datetime | None:
    """Intenta parsear la fecha de una entrada RSS de distintos campos."""
    # feedparser llena published_parsed o updated_parsed como time.struct_time
    for field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    # fallback: string published
    published = getattr(entry, "published", "") or getattr(entry, "updated", "")
    if published:
        try:
            return parsedate_to_datetime(published).astimezone(timezone.utc)
        except Exception:
            pass
    return None


async def _fetch_feed(name: str, url: str) -> list[feedparser.FeedParserDict]:
    """Descarga y parsea un feed RSS."""
    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": "Iris-AI-Intel/1.0 (personal assistant)"},
        ) as client:
            response = await client.get(url)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        return feed.entries
    except Exception as e:
        logger.warning("RSS feed '%s' falló: %s", name, e)
        return []


async def fetch_news(days: int = 7, limit_per_feed: int = 5) -> tuple[list[NewsEntry], list[str]]:
    """Lee todos los feeds y devuelve noticias de los últimos `days` días.

    Returns:
        (lista de noticias ordenadas por fecha, lista de errores por feed)
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    all_news: list[NewsEntry] = []
    errors: list[str] = []

    for source_name, url in RSS_FEEDS.items():
        entries = await _fetch_feed(source_name, url)
        if not entries:
            errors.append(f"{source_name}: sin respuesta o sin entradas")
            continue

        count = 0
        for entry in entries:
            published = _parse_date(entry)
            if published and published < cutoff:
                continue

            title = getattr(entry, "title", "Sin título")
            link = getattr(entry, "link", "")
            # Intentar extraer un resumen corto
            summary = ""
            for field in ("summary", "description", "content"):
                raw = getattr(entry, field, "")
                if isinstance(raw, list) and raw:
                    raw = raw[0].get("value", "")
                if raw:
                    # Remover HTML básico y truncar
                    import re
                    summary = re.sub(r"<[^>]+>", "", str(raw)).strip()[:300]
                    break

            all_news.append(NewsEntry(
                title=title,
                source=source_name,
                url=link,
                published=published.strftime("%Y-%m-%d") if published else "fecha desconocida",
                summary=summary,
            ))
            count += 1
            if count >= limit_per_feed:
                break

        logger.info("RSS '%s': %d noticias recientes", source_name, count)

    # Ordenar del más reciente al más viejo
    all_news.sort(key=lambda x: x.published, reverse=True)
    return all_news, errors
