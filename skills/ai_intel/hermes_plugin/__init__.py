"""Plugin Hermes: ai-intel

Registra la tool `ai_intel` que consulta novedades del mundo de AI:
  - Modelos nuevos en OpenRouter y HuggingFace (orgs conocidas)
  - Repos nuevos en GitHub con topic llm/generative-ai (deduplicado)
  - Noticias de OpenAI, DeepMind, Mistral, TLDR AI, ArXiv, HN
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

SKILL_BASE_URL = "http://localhost:8002"

AI_INTEL_SCHEMA = {
    "name": "ai_intel",
    "description": (
        "Obtiene novedades del mundo de AI vía RSS y APIs: modelos nuevos en OpenRouter y "
        "HuggingFace, repositorios nuevos en GitHub con temática AI/LLM, noticias de "
        "OpenAI, DeepMind, TLDR AI, ArXiv y más, y cursos/certificaciones de "
        "NVIDIA DLI, Coursera, fast.ai, Google Dev y AWS ML. "
        "Usalo cuando Pablo pregunte qué hay de nuevo en AI, qué modelos salieron, "
        "qué está trending en GitHub, o qué anunciaron las compañías de AI. "
        "LÍMITE IMPORTANTE: DeepLearning.AI NO tiene RSS → si Pablo pregunta "
        "específicamente por cursos de DeepLearning.AI, usá web_search en vez de este tool. "
        "IMPORTANTE: al presentar la respuesta, conservá siempre las fechas y URLs."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": ["all", "models", "repos", "news", "courses"],
                "description": (
                    "Qué consultar: "
                    "'all' = todo (default), "
                    "'models' = solo modelos nuevos, "
                    "'repos' = solo repos GitHub, "
                    "'news' = solo noticias de compañías, "
                    "'courses' = solo cursos y certificaciones"
                ),
                "default": "all",
            },
            "days": {
                "type": "integer",
                "description": "Días atrás a cubrir (default: 7, máx: 30)",
                "default": 7,
            },
        },
        "required": [],
    },
}


def _fmt_models(models: list[dict]) -> list[str]:
    """Formatea la sección de modelos."""
    if not models:
        return []

    or_models = [m for m in models if m.get("provider") != "huggingface"]
    hf_models = [m for m in models if m.get("provider") == "huggingface"]

    lines = [f"🤖 **Modelos nuevos** ({len(models)} total)"]

    if or_models:
        lines.append("*OpenRouter* (con pricing):")
        for m in or_models:
            price = (
                f"${m['price_input']:.4f}/${m['price_output']:.4f}/M tokens"
                if m["price_input"] > 0 else "precio no disponible"
            )
            ctx = f" · {m['context_k']}K ctx" if m["context_k"] > 0 else ""
            lines.append(f"  • **{m['name']}** | {m['created_date']} | {price}{ctx}")

    if hf_models:
        lines.append(f"*HuggingFace* (orgs reconocidas, {len(hf_models)} modelos):")
        for m in hf_models[:5]:
            lines.append(f"  • **{m['name']}** | {m['created_date']}")
        if len(hf_models) > 5:
            lines.append(f"  (y {len(hf_models) - 5} más...)")

    return lines


def _fmt_repos(repos: list[dict]) -> list[str]:
    """Formatea la sección de repos."""
    if not repos:
        return []

    lines = [f"⭐ **Repos GitHub nuevos** ({len(repos)} encontrados)"]
    for r in repos:
        lang = f" [{r['language']}]" if r.get("language") and r["language"] != "N/A" else ""
        desc = r.get("description", "")[:120]
        lines.append(
            f"  • **{r['name']}** | creado: {r['created_date']} | {r['stars']:,} ⭐{lang}\n"
            f"    {desc}\n"
            f"    {r['url']}"
        )
    return lines


def _fmt_courses(courses: list[dict], query_is_courses: bool = False) -> list[str]:
    """Formatea la sección de cursos y certificaciones.

    Formato: • [DD-mmm] Título (🆓 si es gratis) — Provider 🔗 URL
    Misma estrategia que _fmt_news: fecha inline para que el LLM no la pierda.

    Cuando `query_is_courses=True` (el usuario preguntó específicamente por cursos)
    devuelve una línea informativa en lugar de lista vacía, para que el LLM no
    tenga que inventar qué fuentes se chequearon.
    """
    if not courses:
        if query_is_courses:
            return [
                "📚 **Cursos y certificaciones** — 0 resultados en este período.",
                "  Fuentes chequeadas: NVIDIA DLI, Coursera, fast.ai, Google Dev, AWS ML Blog,",
                "  DeepLearning.AI (GitHub), Microsoft AI (GitHub).",
                "  Esta semana no se publicaron cursos nuevos en estas fuentes.",
            ]
        return []

    lines = [f"📚 **Cursos y certificaciones** ({len(courses)} nuevos)"]

    for item in courses:
        pub = item.get("published", "")
        try:
            from datetime import datetime
            dt = datetime.strptime(pub, "%Y-%m-%d")
            short_date = dt.strftime("%d-%b").lower()
        except Exception:
            short_date = pub

        free_tag = " 🆓" if item.get("is_free") else ""
        url = item.get("url", "")
        url_str = f" 🔗 {url}" if url else ""
        provider = item.get("provider", "")

        lines.append(
            f"  • [{short_date}] {item['title']}{free_tag} — *{provider}*{url_str}"
        )

    return lines


def _fmt_news(news: list[dict]) -> list[str]:
    """Formatea noticias con fecha inline en el título y URL en la misma línea.

    Formato: • [DD-mmm] Título — Fuente 🔗 URL
    La fecha va fusa con el título para que el LLM no la pueda omitir al resumir.
    """
    if not news:
        return []

    lines = [f"📰 **Noticias** ({len(news)} artículos) — presentá fecha y URL de cada una"]

    # Agrupar por fuente
    by_source: dict[str, list] = {}
    for item in news:
        by_source.setdefault(item["source"], []).append(item)

    for source, items in by_source.items():
        lines.append(f"\n*{source}:*")
        for item in items[:4]:
            # Fecha en formato corto y pegada al título
            pub = item["published"]  # YYYY-MM-DD
            try:
                from datetime import datetime
                dt = datetime.strptime(pub, "%Y-%m-%d")
                short_date = dt.strftime("%d-%b").lower()  # ej: "26-may"
            except Exception:
                short_date = pub

            url = item.get("url", "")
            url_str = f" 🔗 {url}" if url else ""
            lines.append(
                f"  • [{short_date}] {item['title']}{url_str}"
            )

    return lines


def _format_response(data: dict, query_type: str) -> str:
    """Convierte la respuesta del servicio en texto estructurado para el LLM."""
    days = data.get("days", 7)
    errors = data.get("errors", [])

    sections: list[list[str]] = []

    if query_type in ("all", "models"):
        s = _fmt_models(data.get("models", []))
        if s:
            sections.append(s)

    if query_type in ("all", "repos"):
        s = _fmt_repos(data.get("repos", []))
        if s:
            sections.append(s)

    if query_type in ("all", "news"):
        s = _fmt_news(data.get("news", []))
        if s:
            sections.append(s)

    if query_type in ("all", "courses"):
        # query_is_courses=True cuando el usuario preguntó específicamente por cursos
        # → mostrar mensaje informativo aunque esté vacío (en vez de silencio)
        s = _fmt_courses(data.get("courses", []), query_is_courses=(query_type == "courses"))
        if s:
            sections.append(s)

    if not sections:
        return f"No encontré novedades en los últimos {days} días."

    header = f"📡 **AI Intel — últimos {days} días**\n"
    body = "\n\n".join("\n".join(s) for s in sections)

    # Errores al final, solo si hay (no alarmar si son feeds menores)
    footer = ""
    if errors:
        footer = f"\n\n⚠️ Sin datos de: {', '.join(e.split(':')[0] for e in errors)}"

    return header + body + footer


def _handle_ai_intel(args: dict, **kwargs) -> str:
    """Llama al servicio ai_intel y formatea la respuesta para Iris."""
    query_type = args.get("type", "all")
    days = args.get("days", 7)

    endpoint_map = {
        "all":     "/summary",
        "models":  "/models",
        "repos":   "/repos",
        "news":    "/news",
        "courses": "/courses",
    }
    endpoint = endpoint_map.get(query_type, "/summary")

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(
                f"{SKILL_BASE_URL}{endpoint}",
                params={"days": days},
            )
        response.raise_for_status()
        data = response.json()
    except httpx.ConnectError:
        return "❌ ai_intel no disponible — el servicio Docker no está corriendo."
    except Exception as e:
        logger.error("ai_intel error: %s", e)
        return f"❌ Error al obtener novedades de AI: {e}"

    return _format_response(data, query_type)


def register(ctx) -> None:
    """Llamado por el plugin loader de Hermes al arrancar."""
    ctx.register_tool(
        name="ai_intel",
        toolset="ai-intel",
        schema=AI_INTEL_SCHEMA,
        handler=_handle_ai_intel,
        emoji="📡",
    )
    logger.info("Plugin ai-intel: tool ai_intel registrada")
