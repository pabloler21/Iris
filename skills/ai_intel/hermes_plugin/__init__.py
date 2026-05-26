"""Plugin Hermes: ai-intel

Registra la tool `ai_intel` que consulta novedades del mundo de AI:
  - Modelos nuevos en OpenRouter y HuggingFace
  - Repos trending en GitHub con temática AI/LLM
  - Noticias/anuncios de OpenAI, DeepMind, Anthropic, Meta, TLDR AI, etc.
"""

from __future__ import annotations

import json
import logging

import httpx

logger = logging.getLogger(__name__)

SKILL_BASE_URL = "http://localhost:8002"

AI_INTEL_SCHEMA = {
    "name": "ai_intel",
    "description": (
        "Obtiene novedades del mundo de AI: modelos nuevos en OpenRouter y HuggingFace, "
        "repositorios trending en GitHub con temática AI/LLM, y noticias/anuncios de "
        "OpenAI, DeepMind, Anthropic, Meta AI, TLDR AI y otros. "
        "Usalo cuando Pablo pregunte qué hay de nuevo en AI, qué modelos salieron, "
        "qué está trending en GitHub, o qué anunciaron las compañías de AI."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": ["all", "models", "repos", "news"],
                "description": (
                    "Qué tipo de información buscar: "
                    "'all' (todo, default), "
                    "'models' (solo modelos nuevos), "
                    "'repos' (solo repos GitHub), "
                    "'news' (solo noticias de compañías)"
                ),
                "default": "all",
            },
            "days": {
                "type": "integer",
                "description": "Cuántos días atrás buscar (default: 7, máx: 30)",
                "default": 7,
            },
        },
        "required": [],
    },
}


def _format_response(data: dict, query_type: str) -> str:
    """Formatea la respuesta del servicio en texto legible para el LLM."""
    days = data.get("days", 7)
    errors = data.get("errors", [])
    lines: list[str] = [f"📡 AI Intel — últimos {days} días\n"]

    # --- Modelos ---
    models = data.get("models", [])
    if models and query_type in ("all", "models"):
        lines.append(f"🤖 **Modelos nuevos** ({len(models)} encontrados):")
        # Separar OpenRouter de HuggingFace
        or_models = [m for m in models if m.get("provider") != "huggingface"]
        hf_models = [m for m in models if m.get("provider") == "huggingface"]

        if or_models:
            lines.append("  *OpenRouter:*")
            for m in or_models[:8]:
                price_str = (
                    f"${m['price_input']:.4f}/${m['price_output']:.4f} per M tokens"
                    if m["price_input"] > 0
                    else "precio no disponible"
                )
                ctx_str = f"{m['context_k']}K ctx" if m["context_k"] > 0 else ""
                lines.append(
                    f"  • {m['name']} ({m['created_date']}) — {price_str}"
                    + (f", {ctx_str}" if ctx_str else "")
                )

        if hf_models:
            lines.append(f"  *HuggingFace* ({len(hf_models)} nuevos):")
            for m in hf_models[:5]:
                lines.append(f"  • {m['name']} ({m['created_date']})")

        lines.append("")

    # --- Repos ---
    repos = data.get("repos", [])
    if repos and query_type in ("all", "repos"):
        lines.append(f"⭐ **Repos GitHub trending** ({len(repos)} encontrados):")
        for r in repos[:8]:
            lang = f" [{r['language']}]" if r.get("language") and r["language"] != "N/A" else ""
            lines.append(
                f"  • **{r['name']}** — {r.get('description', '')[:100]}\n"
                f"    {r['stars']:,} ⭐{lang} | {r['url']}"
            )
        lines.append("")

    # --- Noticias ---
    news = data.get("news", [])
    if news and query_type in ("all", "news"):
        lines.append(f"📰 **Noticias** ({len(news)} artículos):")
        # Agrupar por fuente para mejor lectura
        by_source: dict[str, list] = {}
        for n in news:
            by_source.setdefault(n["source"], []).append(n)

        for source, items in by_source.items():
            lines.append(f"  *{source}:*")
            for item in items[:3]:
                lines.append(f"  • [{item['published']}] {item['title']}")
                if item.get("summary"):
                    lines.append(f"    {item['summary'][:150]}...")
                lines.append(f"    {item['url']}")
        lines.append("")

    # --- Errores (discretos, al final) ---
    if errors:
        lines.append(f"⚠️ Fuentes con error: {', '.join(errors)}")

    if len(lines) == 1:
        return f"No encontré novedades en los últimos {days} días."

    return "\n".join(lines)


def _handle_ai_intel(args: dict, **kwargs) -> str:
    """Llama al servicio ai_intel y formatea la respuesta para Iris."""
    query_type = args.get("type", "all")
    days = args.get("days", 7)

    # Elegir endpoint según tipo
    endpoint_map = {
        "all": "/summary",
        "models": "/models",
        "repos": "/repos",
        "news": "/news",
    }
    endpoint = endpoint_map.get(query_type, "/summary")

    try:
        with httpx.Client(timeout=45.0) as client:  # feeds RSS pueden tardar
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
