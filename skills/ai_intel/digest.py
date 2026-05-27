"""Formateador de digest semanal para Discord.

Genera un resumen compacto (< 1900 chars) listo para enviar como mensaje de Discord.
Diseñado para el cron push semanal de Hermes — sin LLM en el loop.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


# Límite conservador — Discord permite 2000, dejamos margen para headers de Hermes
DISCORD_LIMIT = 1900


def _short_date(date_str: str) -> str:
    """Convierte 'YYYY-MM-DD' a '26-may'. Devuelve el original si falla."""
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return dt.strftime("%-d-%b").lower()
    except Exception:
        return date_str


def _fmt_models_compact(models: list[dict], max_items: int = 4) -> str:
    """Sección de modelos — formato compacto para digest."""
    if not models:
        return ""

    total = len(models)
    items = models[:max_items]
    lines = [f"🤖 **Modelos nuevos** ({total})"]

    for m in items:
        source = "HF" if m.get("provider") == "huggingface" else "OR"
        price_in = m.get("price_input", 0)
        price_out = m.get("price_output", 0)
        if price_in > 0:
            price = f"${price_in:.2f}/${price_out:.2f}/M"
        else:
            price = "free"
        ctx = f" · {m['context_k']}K ctx" if m.get("context_k", 0) > 0 else ""
        lines.append(f"  · {m['name']} [{source}] · {_short_date(m['created_date'])} · {price}{ctx}")

    if total > max_items:
        lines.append(f"  *(y {total - max_items} más)*")

    return "\n".join(lines)


def _fmt_repos_compact(repos: list[dict], max_items: int = 4) -> str:
    """Sección de repos — formato compacto para digest."""
    if not repos:
        return ""

    total = len(repos)
    items = repos[:max_items]
    lines = [f"⭐ **Repos trending** ({total})"]

    for r in items:
        lang = f" [{r['language']}]" if r.get("language") and r["language"] != "N/A" else ""
        # Descripción corta: max 70 chars
        desc = (r.get("description") or "Sin descripción")[:70]
        short_url = r["url"].replace("https://github.com/", "")
        lines.append(f"  · **{r['name']}** ★{r['stars']:,}{lang} — {desc}")
        lines.append(f"    → github.com/{short_url}")

    if total > max_items:
        lines.append(f"  *(y {total - max_items} más)*")

    return "\n".join(lines)


def _fmt_news_compact(news: list[dict], max_items: int = 5) -> str:
    """Sección de noticias — sin agrupar por fuente (más compacto que el formato chat)."""
    if not news:
        return ""

    total = len(news)
    items = news[:max_items]
    lines = [f"📰 **Noticias** ({total})"]

    for n in items:
        date = _short_date(n.get("published", ""))
        title = n["title"][:80]
        url = n.get("url", "")
        source = n.get("source", "")
        source_str = f" — *{source}*" if source else ""
        url_str = f"\n    → {url}" if url else ""
        lines.append(f"  · [{date}] {title}{source_str}{url_str}")

    if total > max_items:
        lines.append(f"  *(y {total - max_items} más — pedile al bot 'dame las noticias de AI')*")

    return "\n".join(lines)


def _fmt_courses_compact(courses: list[dict], max_items: int = 3) -> str:
    """Sección de cursos — formato compacto para digest."""
    if not courses:
        return ""

    total = len(courses)
    items = courses[:max_items]
    lines = [f"📚 **Cursos nuevos** ({total})"]

    for c in items:
        date = _short_date(c.get("published", ""))
        title = c["title"][:80]
        free_tag = " 🆓" if c.get("is_free") else ""
        provider = c.get("provider", "")
        provider_str = f" — *{provider}*" if provider else ""
        url = c.get("url", "")
        url_str = f"\n    → {url}" if url else ""
        lines.append(f"  · [{date}] {title}{free_tag}{provider_str}{url_str}")

    if total > max_items:
        lines.append(f"  *(y {total - max_items} más)*")

    return "\n".join(lines)


def format_discord_digest(data: dict, days: int = 7) -> list[str]:
    """Convierte IntelResponse (dict) en una lista de mensajes para Discord.

    Cada mensaje está garantizado de ser < DISCORD_LIMIT chars.
    En la práctica debería caber en un solo mensaje con los límites de items por sección.

    Args:
        data: dict con campos models, repos, news, courses, errors
        days: período cubierto (para el header)

    Returns:
        Lista de strings, cada uno < DISCORD_LIMIT chars.
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    # Rango de fechas en el header: "20-26 may" o "20 may - 3 jun"
    if start.month == end.month:
        date_range = f"{start.day}–{end.day} {end.strftime('%b %Y').lower()}"
    else:
        date_range = f"{start.strftime('%-d %b')} – {end.strftime('%-d %b %Y').lower()}"

    header = f"📬 **Digest semanal · AI Intel** — {date_range}\n{'━' * 30}\n\n"

    # Construir secciones
    raw_sections = [
        _fmt_models_compact(data.get("models", [])),
        _fmt_repos_compact(data.get("repos", [])),
        _fmt_news_compact(data.get("news", [])),
        _fmt_courses_compact(data.get("courses", [])),
    ]
    sections = [s for s in raw_sections if s]

    if not sections:
        return [f"📬 Sin novedades en los últimos {days} días."]

    # Errores de fuentes (si hay, al final en modo silencioso)
    errors = data.get("errors", [])
    footer = ""
    if errors:
        fuentes = ", ".join(e.split(":")[0] for e in errors)
        footer = f"\n\n⚠️ *Fuentes con errores: {fuentes}*"

    # Intentar meter todo en un mensaje
    full_text = header + "\n\n".join(sections) + footer
    if len(full_text) <= DISCORD_LIMIT:
        return [full_text]

    # Si no entra: dividir en mensajes por sección
    # El header + primera sección siempre van juntos
    messages: list[str] = []
    current = header + sections[0]

    for section in sections[1:]:
        candidate = current + "\n\n" + section
        if len(candidate) <= DISCORD_LIMIT:
            current = candidate
        else:
            messages.append(current)
            current = section

    current += footer
    messages.append(current)

    return messages
