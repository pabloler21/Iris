"""Fuente: RSS feeds de blogs de compañías de AI y newsletters.

Feeds incluidos (todos verificados con URL funcional):
  - OpenAI          (oficial)
  - Google DeepMind (oficial)
  - Google AI Blog  (oficial, via blog.google)
  - Mistral AI      (oficial)
  - TLDR AI         (newsletter, muy completo)
  - ArXiv cs.AI     (papers recientes)
  - Hacker News AI  (posts sobre AI en HN)

Notas:
  - Anthropic: sin RSS oficial ni community feed estable → excluido
  - Meta AI: sin RSS funcional → excluido
  - xAI: sin RSS → excluido
"""

import logging
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from models.schemas import NewsEntry

logger = logging.getLogger(__name__)

RSS_FEEDS = {
    "OpenAI":          "https://openai.com/news/rss.xml",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    "Google AI":       "https://blog.google/technology/ai/rss/",
    "Mistral AI":      "https://mistral.ai/fr/rss/news.xml",
    "TLDR AI":         "https://tldr.tech/api/rss/ai",
    "ArXiv cs.AI":     "https://rss.arxiv.org/rss/cs.AI",
    "Hacker News AI":  "https://hnrss.org/newest?q=LLM+OR+%22language+model%22+OR+%22AI+model%22&count=20",
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


async def fetch_news(days: int = 7, limit_per_feed: int = 4) -> tuple[list[NewsEntry], list[str]]:
    """Lee todos los feeds y devuelve noticias de los últimos `days` días.

    Returns:
        (lista de noticias ordenadas por fecha DESC, lista de feeds con error)
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    all_news: list[NewsEntry] = []
    errors: list[str] = []

    for source_name, url in RSS_FEEDS.items():
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
            if count >= limit_per_feed:
                break

        logger.info("RSS '%s': %d entradas recientes", source_name, count)

    # Ordenar del más reciente al más viejo
    all_news.sort(key=lambda x: x.published, reverse=True)
    return all_news, errors
