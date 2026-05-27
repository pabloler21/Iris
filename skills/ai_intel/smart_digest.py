"""Digest inteligente: Kimi K2.6 como editor del newsletter semanal.

Toma el feed completo de la semana, llama a Kimi K2.6 via OpenRouter,
y devuelve un texto Discord-ready curado y personalizado para Pablo.

Costo estimado: < $0.005 por run (2-3K tokens en total).
Timeout: 40s. Si falla, el caller debe hacer fallback a digest.py.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Gemini Flash: sin reasoning tokens, muy rápido (~2-5s), ideal para formateo/curaduría.
# Kimi K2.6 es un reasoning model — gasta >2000 tokens pensando en tareas simples.
# Para esta tarea (seleccionar + formatear), un instruction-following model es mejor.
CURATION_MODEL = "google/gemini-2.0-flash-001"
LLM_TIMEOUT = 30.0   # segundos — Gemini Flash responde en 2-5s normalmente


# Perfil de Pablo — qué le importa, cómo priorizar
_PABLO_PROFILE = """
Pablo es AI Engineer Jr en Buenos Aires. Stack: Python, FastAPI, Pydantic, LangChain,
Docker, LLMs vía API (OpenRouter), RAG con Qdrant, agentes con Hermes/Pydantic AI.
Está buscando trabajo activamente como AI Engineer.

Qué le importa en orden de relevancia:
1. Herramientas y frameworks para developers de AI (nuevos SDKs, agent frameworks, MCP, etc.)
2. Modelos nuevos con buen precio/performance (especialmente los usables vía API)
3. Patrones arquitecturales de LLM apps (RAG, agentic loops, fine-tuning accesible)
4. Noticias de industria que afecten el mercado laboral de AI
5. Cursos prácticos de bajo costo

Baja prioridad: investigación teórica pura, hardware, política/regulación,
papers sin implementación, noticias de consumidores finales.
""".strip()



# Límites de items que mandamos a Kimi — menos input = menos reasoning tokens gastados
_MAX_NEWS_FOR_PROMPT = 10
_MAX_REPOS_FOR_PROMPT = 6


def _compact_feed(data: dict, days: int) -> str:
    """Serializa los datos del feed en formato compacto para el prompt.

    Limitamos los items enviados a Kimi para no disparar demasiados reasoning tokens:
    Kimi K2.6 puede gastar >4000 chars pensando si el input es muy largo.
    """
    lines: list[str] = []

    # Modelos (todos — suelen ser pocos)
    models = data.get("models", [])
    if models:
        lines.append(f"=== MODELOS NUEVOS ({len(models)}) ===")
        for m in models:
            src = "HF" if m.get("provider") == "huggingface" else "OpenRouter"
            p_in = m.get("price_input", 0)
            p_out = m.get("price_output", 0)
            price = f"${p_in:.2f}/${p_out:.2f}/M" if p_in > 0 else "gratis"
            ctx = f" · {m['context_k']}K ctx" if m.get("context_k", 0) > 0 else ""
            lines.append(f"- {m['name']} [{src}] · {m['created_date']} · {price}{ctx}")
    else:
        lines.append("=== MODELOS NUEVOS (0) ===\n(ninguno esta semana)")

    # Repos (top N por stars)
    repos = data.get("repos", [])[:_MAX_REPOS_FOR_PROMPT]
    total_repos = len(data.get("repos", []))
    if repos:
        lines.append(f"\n=== REPOS GITHUB (mostrando {len(repos)} de {total_repos}) ===")
        for r in repos:
            lang = f" [{r['language']}]" if r.get("language") and r["language"] != "N/A" else ""
            desc = (r.get("description") or "")[:90]
            lines.append(f"- {r['name']} ★{r['stars']:,}{lang} — {desc}")
    else:
        lines.append("\n=== REPOS GITHUB (0) ===\n(ninguno esta semana)")

    # Noticias (top N más recientes)
    news = data.get("news", [])[:_MAX_NEWS_FOR_PROMPT]
    total_news = len(data.get("news", []))
    if news:
        lines.append(f"\n=== NOTICIAS (mostrando {len(news)} de {total_news}) ===")
        for n in news:
            url = n.get("url", "")
            lines.append(f"- [{n['published']}] {n['title']} — {n['source']} → {url}")
    else:
        lines.append("\n=== NOTICIAS (0) ===\n(ninguna esta semana)")

    # Cursos (todos — suelen ser pocos o ninguno)
    courses = data.get("courses", [])
    if courses:
        lines.append(f"\n=== CURSOS ({len(courses)}) ===")
        for c in courses:
            free = " [GRATIS]" if c.get("is_free") else ""
            url = c.get("url", "")
            lines.append(f"- [{c['published']}] {c['title']}{free} — {c['provider']} → {url}")
    else:
        lines.append("\n=== CURSOS (0) ===\n(ninguno esta semana)")

    return "\n".join(lines)


def _build_prompt(data: dict, days: int) -> tuple[str, str]:
    """Devuelve (system_prompt, user_message) para la llamada a Kimi."""

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    if start.month == end.month:
        date_range = f"{start.day}–{end.day} {end.strftime('%b %Y').lower()}"
    else:
        date_range = f"{start.strftime('%-d %b')} – {end.strftime('%-d %b %Y').lower()}"

    system = f"""Sos el editor de "AI Weekly", el newsletter personal de Pablo.

PERFIL DEL LECTOR:
{_PABLO_PROFILE}

TU TRABAJO:
Del feed completo que te mando, seleccioná y redactá el digest semanal para Discord.

REGLAS DE FORMATO:
- Empezá con: 📬 **AI Weekly · {date_range}**\\n{'━' * 30}
- Máximo 4 secciones: 🤖 Modelos · ⭐ Repos · 📰 Noticias · 📚 Cursos
- Por sección: máximo 3 modelos, 3 repos, 5 noticias, 2 cursos
- Para cada item: nombre/título + URL + UNA línea de "por qué importa para Pablo" (empieza con →)
- Si una sección no tiene nada relevante, omitila completamente
- Texto total: MENOS de 1900 caracteres (límite Discord)
- Markdown Discord-friendly: **negrita**, *cursiva*, emojis moderados
- Idioma: español rioplatense (vos/te/tus)

PRIORIDAD AL ELEGIR:
Herramientas prácticas > papers teóricos > noticias de industria > cursos
No incluyas papers sin código/demo, noticias de política, o hardware puro."""

    user = f"Feed de la semana {date_range}:\n\n{_compact_feed(data, days)}"

    return system, user


async def call_kimi_curator(data: dict, days: int = 7) -> str | None:
    """Llama a Kimi K2.6 para curar el digest. Devuelve el texto formateado.

    Returns:
        El texto Discord-ready si la llamada fue exitosa, None si falló.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY no configurada — no se puede llamar a Kimi")
        return None

    system_prompt, user_message = _build_prompt(data, days)

    payload = {
        "model": CURATION_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        # Gemini Flash no tiene reasoning overhead — 900 tokens es más que suficiente
        # para el digest completo (~1900 chars ≈ 600-700 tokens).
        "max_tokens": 900,
        "temperature": 0.3,   # Baja temperatura = formato más consistente
    }

    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/pabloler21/Iris",
                    "X-Title": "Iris AI Weekly Digest",
                },
                json=payload,
            )
        response.raise_for_status()
        result = response.json()

        message = result["choices"][0]["message"]
        # Kimi K2.6 separa reasoning del content. Con max_tokens suficiente,
        # content tiene la respuesta final. Fallback a reasoning solo como debug.
        text = message.get("content") or ""
        if not text.strip():
            # Si content llegó vacío o null (no debería pasar con max_tokens=1600)
            logger.error("Kimi devolvió content vacío. reasoning len=%d", len(message.get("reasoning") or ""))
            return None
        text = text.strip()

        # Loguear uso de tokens para monitorear costo
        usage = result.get("usage", {})
        logger.info(
            "Kimi curation: %d input tokens + %d output tokens",
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
        )

        return text

    except httpx.TimeoutException:
        logger.error("Kimi curation timeout (>%.0fs)", LLM_TIMEOUT)
        return None
    except httpx.HTTPStatusError as e:
        logger.error("Kimi curation HTTP error %s: %s", e.response.status_code, e.response.text[:200])
        return None
    except Exception as e:
        logger.error("Kimi curation error: %s", e)
        return None
