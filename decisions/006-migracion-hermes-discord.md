# ADR 006: Migración OpenClaw → Hermes Agent + Discord + Gemini Flash

## Supersede

Reemplaza parcialmente ADR 005 (OpenClaw + Kimi K2.6). OpenClaw desactivado.

## Context

Durante la Fase 3.5 (2026-05-25) se evaluó Hermes Agent de Nous Research como reemplazo
de OpenClaw, motivado por:
- Hermes tiene mayor madurez, más features (sub-agentes, cron natural, web, etc.)
- Stack Python vs Node.js de OpenClaw → mejor alineado con las skills del proyecto
- Hermes tiene comando de migración nativo (`hermes claw migrate`)
- Soporte nativo de Discord (además de Telegram, Slack, WhatsApp, etc.)
- Nos Research es un laboratorio de IA reconocido → mejor para portfolio

## Decisiones tomadas

### 1. Hermes Agent reemplaza OpenClaw

**Instalado:** `~/.hermes/hermes-agent/` (Python 3.11 + uv, venv propio)
**Gateway:** systemd user service `hermes-gateway.service` (reemplaza `openclaw-gateway.service`)
**Migración:** `hermes claw migrate --preset full --overwrite --yes`

OpenClaw fue detenido (`systemctl --user stop/disable openclaw-gateway`) pero no desinstalado.
El config original sigue en `~/.openclaw/` como backup.

### 2. Discord reemplaza Telegram

Canal de mensajería cambiado a Discord (DM con bot **Iris#4138**).
Telegram descartado para simplificar — Hermes soporta ambos si en el futuro se reactiva.

**Bot configurado:**
- Token: guardado en `~/.hermes/.env` (DISCORD_BOT_TOKEN)
- Allowed user: `1036628709735673916` (DISCORD_ALLOWED_USERS)

### 3. Modelo: Google Gemini 2.0 Flash vía OpenRouter

**Modelo:** `google/gemini-2.0-flash-001`
**Pricing:** $0.10/M input, $0.40/M output (vs $0.57/$2.30 de kimi-k2, 5-8x más barato)
**Contexto:** 1M tokens (vs 131k del resto)

**Por qué Kimi K2.x fue descartado:**
- kimi-k2.6 tiene thinking mode hardcodeado → genera `reasoning_content`
- Hermes incluye `reasoning_content` en el historial del siguiente turno
- OpenRouter rechaza ese campo → Connection error en el 2do turno
- kimi-k2 (sin .6) tiene el mismo problema de forma intermitente
- Gemini 2.0 Flash no tiene thinking mode → historial limpio

### 4. Qdrant se mantiene para RAG (Fase 5)

Qdrant no es redundante con la memoria nativa de Hermes:
- **Hermes FTS5 + Honcho**: memoria de conversación (working memory)
- **Qdrant + skill custom**: knowledge base externa para RAG (PDFs, docs, RSS)

Se desarrollará una skill `search_my_docs` en Fase 5.

### 5. Nombre del proyecto: Iris

Renombramiento pendiente de clawnest → iris (repo, directorio, docs). Ver task #11.

## Patches aplicados al código de Hermes

Hermes 0.14.0 tiene bugs en Linux Mint que requirieron parches locales:

### Patch 1: Non-streaming forzado (`agent/conversation_loop.py`)
**Problema:** OpenRouter cierra conexiones SSE silenciosamente cuando el payload de tools
es grande (33+ tools, ~52KB). El config `streaming: false` no era respetado correctamente.
**Fix:** Línea ~1164 — se cambió `elif not agent._has_stream_consumers()` por `else:`
para forzar `_use_streaming = False` incondicionalmente.
**Backup:** `agent/conversation_loop.py.bak`

### Patch 2: TCP keepalives custom (`run_agent.py`)
**Problema:** `_build_keepalive_http_client` creaba un httpx.Client con TCP keepalives
(`TCP_KEEPIDLE=30, KEEPINTVL=10, KEEPCNT=3`) que causaban Connection errors en Linux Mint.
**Fix:** Se reemplazó por un httpx.Client con `http2=False` sin socket options custom.
**Backup:** `run_agent.py.bak`

⚠️ Si Hermes se auto-actualiza, estos patches se pueden pisar. Re-aplicar si el bot
empieza a dar Connection errors.

## Toolset configurado para Discord

Toolset minimalista `hermes-discord-minimal` definido en `toolsets.py`:
```python
tools = [
    "memory", "session_search", "clarify",
    "web_search", "web_extract",   # ddgs como provider (gratis, sin API key)
    "todo", "send_message", "cronjob", "discord"
]
```

**Excluidos intencionalmente:** `skill_view`, `skills_list` — su presencia inyecta
el listado de 90 skills (~18k tokens) en el system prompt, disparando la latencia
de 5s a 30s por respuesta.

## Configuración en homelab

```
~/.hermes/.env         → API keys (OPENAI_API_KEY=OpenRouter key, DISCORD_BOT_TOKEN)
~/.hermes/config.yaml  → modelo, max_tokens, toolsets, web.backend=ddgs
~/.hermes/SOUL.md      → personalidad de Iris (simplificada, comportamiento adaptativo)
~/.hermes/hermes-agent/ → código fuente con patches aplicados
```

## Consecuencias

- ✅ Asistente respondiendo en Discord con web search + extract
- ✅ Sin límite de tiempo fijo — avisa cuando va a tardar
- ✅ Contexto de ~5k tokens por request (vs 21k-28k antes del fix del toolset)
- ✅ Latencia ~5-15s por respuesta simple, ~20-40s con tool use
- ⚠️ ddgs falla intermitentemente en startpage.com (primer intento) — retry automático
- ⚠️ Patches locales al código de Hermes — pueden pisarse en updates
- ⚠️ Repo aún se llama clawnest → renombrar a iris (pendiente)

## Date
2026-05-25

## Author
Pablo + Claude Code (Opus 4.7)
