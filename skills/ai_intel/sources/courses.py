"""Fuente: RSS de plataformas y blogs educativos de AI.

Feeds incluidos (todos verificados con URL funcional):
  - NVIDIA Developer Blog  — anuncios del Deep Learning Institute (DLI)
  - Coursera Blog          — lanzamientos de cursos de OpenAI, Google, Meta, etc.
  - fast.ai               — cursos gratuitos, comunidad de ML práctica
  - Google Dev Blog        — codelabs, workshops, certificaciones de Google Cloud/AI
  - AWS ML Blog            — cursos y labs de AWS en AI/ML

Notas:
  - DeepLearning.AI: sin RSS funcional (404 en todos los paths probados) → excluido
  - Anthropic/OpenAI: sin RSS de cursos específicos → cubiertos por rss_feeds.py

Estrategia: se descargan los feeds completos y se filtra por keywords educativos
con word boundaries para evitar falsos positivos (ej: "course" en "Coursera").
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from models.schemas import CourseEntry

logger = logging.getLogger(__name__)

# Feeds verificados — plataformas educativas y blogs de compañías que
# anuncian cursos y certificaciones de AI con frecuencia
COURSE_FEEDS = {
    "NVIDIA DLI": "https://developer.nvidia.com/blog/feed/",
    "Coursera":   "https://blog.coursera.org/feed/",
    "fast.ai":    "https://www.fast.ai/index.xml",
    "Google Dev": "https://developers.googleblog.com/feeds/posts/default",
    "AWS ML":     "https://aws.amazon.com/blogs/machine-learning/feed/",
}

# Keywords que confirman que el post anuncia un curso, certificación o recurso educativo.
# IMPORTANTE: se usa matching con word boundaries (\b) para evitar que "course"
# matchee contra "Coursera" o "training" contra "post-training quantization".
_COURSE_KEYWORDS = (
    "course",
    "certification",
    "certificate",
    "certif",
    "workshop",
    "bootcamp",
    "nanodegree",
    "specialization",
    "curriculum",
    "mooc",
    "credential",
    "learning path",
    "enroll",
    "cohort",
    "tutorial series",
    "codelabs",
    "hands-on lab",
    "online class",
    "online course",
    "training program",
    "training course",
    "new class",
    "free access",
)

# Regex compilado con word boundaries — más preciso que substring match simple
_COURSE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in _COURSE_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# Keywords de gratuidad — para mostrar 🆓 en el output
_FREE_PATTERN = re.compile(
    r"\b(free|gratuito|gratis|no cost|open access|at no cost)\b",
    re.IGNORECASE,
)


def _parse_date(entry) -> datetime | None:
    """Parsea la fecha de publicación de una entrada RSS."""
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


def _clean_html(text: str, max_len: int = 200) -> str:
    """Remueve tags HTML y trunca."""
    clean = re.sub(r"<[^>]+>", "", str(text)).strip()
    clean = re.sub(r"\s+", " ", clean)
    return clean[:max_len] + ("…" if len(clean) > max_len else "")


def _is_course_related(title: str, summary: str) -> bool:
    """True si título o summary contienen un keyword educativo (con word boundary).

    Usa regex con \\b en lugar de substring match para evitar falsos positivos como:
      - "course" en "Coursera"
      - "training" en "post-training quantization"
      - "lab" en "LLM laboratory"
    """
    return bool(_COURSE_PATTERN.search(title + " " + summary))


def _is_free(title: str, summary: str) -> bool:
    """True si el recurso parece gratuito (con word boundary)."""
    return bool(_FREE_PATTERN.search(title + " " + summary))


async def _fetch_feed(name: str, url: str) -> list:
    """Descarga y parsea un feed RSS. Retorna lista vacía si falla."""
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
        logger.warning("Courses feed '%s' falló: %s", name, e)
        return []


async def fetch_new_courses(
    days: int = 7,
    limit_per_feed: int = 3,
) -> tuple[list[CourseEntry], list[str]]:
    """Lee feeds educativos y devuelve cursos/certs de los últimos `days` días.

    Args:
        days: ventana de tiempo a cubrir (1–30)
        limit_per_feed: máximo de resultados por feed (evita dominar con un solo blog)

    Returns:
        (lista de CourseEntry ordenados por fecha DESC, lista de feeds con error)
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    all_courses: list[CourseEntry] = []
    errors: list[str] = []

    for source_name, url in COURSE_FEEDS.items():
        entries = await _fetch_feed(source_name, url)
        if not entries:
            errors.append(f"{source_name}: sin respuesta")
            continue

        count = 0
        for entry in entries:
            published = _parse_date(entry)
            # Si la fecha existe y es más vieja que el cutoff, salteamos
            if published and published < cutoff:
                continue

            title = getattr(entry, "title", "Sin título").strip()
            link = getattr(entry, "link", "")

            # Extraer summary limpio del primer campo disponible
            summary_raw = ""
            for field in ("summary", "description"):
                raw = getattr(entry, field, "")
                if isinstance(raw, list) and raw:
                    raw = raw[0].get("value", "")
                if raw:
                    summary_raw = _clean_html(raw)
                    break

            # Filtro principal con word boundaries — descarta posts que no sean cursos/certs
            if not _is_course_related(title, summary_raw):
                continue

            date_str = published.strftime("%Y-%m-%d") if published else "fecha desconocida"

            all_courses.append(CourseEntry(
                title=title,
                provider=source_name,
                url=link,
                published=date_str,
                summary=summary_raw,
                is_free=_is_free(title, summary_raw),
            ))
            count += 1
            if count >= limit_per_feed:
                break

        logger.info("Courses '%s': %d entradas educativas en %d días", source_name, count, days)

    # Ordenar del más reciente al más viejo
    all_courses.sort(key=lambda x: x.published, reverse=True)
    return all_courses, errors
