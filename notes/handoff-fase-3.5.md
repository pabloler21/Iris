# Handoff: Fase 3.5 — Migración Hermes + Discord + Iris

## Status
✅ Completada — 2026-05-25

---

## Qué se hizo esta sesión

### Stack cambiado

| Componente | Antes | Después |
|---|---|---|
| Framework | OpenClaw 2026.5.22 (Node.js 22) | Hermes Agent 0.14.0 (Python 3.11) |
| Canal | Telegram (no llegó a usarse) | Discord (bot: Iris#4138) |
| Modelo | moonshotai/kimi-k2.6 | google/gemini-2.0-flash-001 |
| Precio LLM | $0.73/$3.49 por M tokens | $0.10/$0.40 por M tokens |

### Estado del homelab al final de la sesión

```
systemctl --user status hermes-gateway → active (running), enabled
Bot Discord: Iris#4138 — conectado y respondiendo
Modelo: google/gemini-2.0-flash-001 vía OpenRouter
max_tokens: 4096
web_search + web_extract: activos (DuckDuckGo, sin API key)
Qdrant: corriendo en Docker (sin cambios)
OpenClaw: DESACTIVADO (disabled) pero no desinstalado
```

### Archivos modificados en el homelab (NO en el repo)

```
~/.hermes/.env                              → API keys (OpenRouter + Discord)
~/.hermes/config.yaml                       → modelo, toolsets, web.backend=ddgs
~/.hermes/SOUL.md                           → personalidad simplificada de Iris
~/.hermes/hermes-agent/toolsets.py          → toolset hermes-discord-minimal
~/.hermes/hermes-agent/agent/conversation_loop.py   → PATCH: non-streaming forzado
~/.hermes/hermes-agent/run_agent.py         → PATCH: http2=False sin keepalives
~/.hermes/hermes-agent/venv/ (uvloop uninstalled)
```

### Bugs resueltos durante la sesión

1. **Connection error en API calls** — OpenRouter cierra conexiones SSE con payloads grandes.
   Fix: forzar non-streaming en `conversation_loop.py` (patch local).

2. **reasoning_content en historial** — Kimi K2.x genera thinking content que rompe el 2do turno.
   Fix: cambio de modelo a Gemini 2.0 Flash (sin thinking mode).

3. **21k tokens de system prompt** — Hermes inyecta listado de 90 skills automáticamente.
   Fix: excluir `skill_view` y `skills_list` del toolset → baja a ~5k tokens.

4. **web_search no funcionaba** — Provider ddgs instalado pero no configurado.
   Fix: `pip install ddgs` + `web.search_backend: ddgs` en config.yaml.

5. **web_extract faltante** — Iris no podía leer páginas web, solo snippets.
   Fix: agregar `web_extract` al toolset minimal.

---

## Pendientes para próxima sesión

### Pendientes técnicos de esta fase
- [ ] **#11 Renombrar repo** de `clawnest` → `iris` (GitHub + directorio local)
  - En GitHub: Settings → Repository name → iris
  - Local: `mv ~/projects/clawnest ~/projects/iris && cd ~/projects/iris && git remote set-url origin https://github.com/pabloler21/iris`
  - Actualizar CLAUDE.md/AGENTS.md con el nombre nuevo
  - Actualizar README con nombre Iris + estado Fase 3.5

### Fase 4 (nueva) — Pulido y configuración pendiente
- [ ] **`/sethome` en Discord** — escribir `/sethome` en el DM del bot para registrar el home channel
- [ ] **Corregir ddgs startpage** — configurar ddgs para evitar startpage.com (siempre timeout)
- [ ] **Configurar /sethome** automáticamente o documentar que hay que hacerlo

### Fase 5 — RAG con Qdrant (ya planeada)
- [ ] Skill `search_my_docs` — ingesta de PDFs/docs a Qdrant, query semántico
- [ ] Cron de RSS/newsletters → indexar en Qdrant → query "qué se publicó esta semana"
- [ ] Skills del hub: `arxiv` (papers), `blogwatcher` (RSS feeds), `github-issues`

---

## Notes for next agent

### Para conectarse al homelab
```bash
ssh clawnest-homelab   # host configurado en ~/.ssh/config → 100.109.56.91
# Requiere Tailscale activo en el homelab
```

### Comandos útiles en el homelab
```bash
systemctl --user status hermes-gateway          # ver estado
systemctl --user restart hermes-gateway         # reiniciar
journalctl --user -u hermes-gateway -f          # logs en tiempo real
tail -f ~/.hermes/logs/agent.log               # logs del agente
tail -f ~/.hermes/logs/errors.log              # solo errores
hermes gateway status                           # status amigable
```

### Patches críticos (no perder)
Los patches están en:
- `~/.hermes/hermes-agent/agent/conversation_loop.py` — non-streaming forzado
- `~/.hermes/hermes-agent/run_agent.py` — http2=False

Si Hermes se actualiza y los patches se pierden, el bot vuelve a dar Connection errors.
Para re-aplicarlos, ver ADR 006 para el detalle de qué cambiar.

### Config clave
```yaml
# ~/.hermes/config.yaml (fragmento)
model:
  default: google/gemini-2.0-flash-001
  max_tokens: 4096
  base_url: https://openrouter.ai/api/v1

platform_toolsets:
  discord:
  - hermes-discord-minimal    # toolset custom, ver toolsets.py

web:
  backend: ddgs
  search_backend: ddgs
```

### Toolset actual
```python
# ~/.hermes/hermes-agent/toolsets.py — hermes-discord-minimal
tools = [
    "memory", "session_search", "clarify",
    "web_search", "web_extract",
    "todo", "send_message", "cronjob", "discord"
]
```

### Advertencias
- API key de OpenRouter en `~/.hermes/.env` como OPENAI_API_KEY (no OPENROUTER_API_KEY)
- OpenClaw sigue instalado en `~/.openclaw/` y `~/.nvm/` — no borrar todavía
- Qdrant corriendo en Docker (puerto 6333) — sin cambios, listo para Fase 5
