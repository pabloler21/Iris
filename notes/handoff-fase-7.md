# Handoff — Fase 7: Weekly AI Digest (Push Mode)

**Fecha:** 2026-05-27  
**Estado:** ✅ Completo y deployado en homelab  
**Rama:** main (mergeado)  

---

## Qué se construyó

Push mode para ai_intel: el **digest semanal automático**.

Iris envía cada lunes a las 9am (ART) un resumen formateado de las novedades de AI
al DM de Pablo (Discord), sin que él tenga que preguntar.

**Arquitectura:**
```
Hermes Cron (lunes 12:00 UTC = 09:00 ART)
    ↓ --no-agent --script ai_digest.sh
~/.hermes/scripts/ai_digest.sh
    ↓ curl http://localhost:8002/digest?days=7
iris-ai-intel (Docker, puerto 8002)
    ↓ fetch sources + format_discord_digest()
stdout → Hermes → Discord DM pl101
```

**Costo del cron:** $0 (no usa LLM — `--no-agent`)

---

## Archivos creados/modificados

```
skills/ai_intel/digest.py              # NUEVO: formatter Discord-optimizado
skills/ai_intel/main.py                # /digest endpoint (v1.2.0 → 1.3.0)
skills/ai_intel/models/schemas.py      # DigestResponse model
skills/ai_intel/scripts/ai_digest.sh   # Script Hermes (deploy → ~/.hermes/scripts/)
skills/ai_intel/sources/github.py      # Fix: awesome-architecture false positive
```

---

## Hermes cron job (homelab)

```
ID:       efb842b408ac
Name:     weekly-ai-digest
Schedule: 0 12 * * 1  (lunes 12:00 UTC = 09:00 ART)
Deliver:  discord:1508529853127856238  (DM pl101)
Mode:     no-agent (script stdout → Discord)
Script:   ai_digest.sh
Next run: 2026-06-01T12:00:00 UTC
```

**Comandos útiles:**
```bash
# Ver estado del cron job
~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main cron list

# Ejecutar manualmente (test)
~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main cron run weekly-ai-digest

# Ver output del último run
ls ~/.hermes/cron/output/efb842b408ac/
cat ~/.hermes/cron/output/efb842b408ac/*.md | tail -30

# Test directo del script
bash ~/.hermes/scripts/ai_digest.sh

# Test del endpoint
curl -s http://localhost:8002/digest?days=7 | python3 -m json.tool | head -20
```

---

## Formato del digest (verificado)

```
📬 **Digest semanal · AI Intel** — 20–27 may 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 **Modelos nuevos** (2)
  · Qwen3.7 Max [OR] · 21-may · $1.25/$3.75/M · 1000K ctx
  · Grok Build 0.1 [OR] · 20-may · $1.00/$2.00/M · 256K ctx

⭐ **Repos trending** (8)
  · **UditAkhourii/adhd** ★269 [TypeScript] — ADHD skill...
    → github.com/UditAkhourii/adhd
  *(y 4 más)*

📰 **Noticias** (25)
  · [27-may] Building self-improving tax agents... — *OpenAI*
    → https://openai.com/...
  *(y 20 más — pedile al bot 'dame las noticias de AI')*

⚠️ *Fuentes con errores: HuggingFace*  ← solo si hay errores
```

**Tamaño:** 1739 chars (semana de prueba) — bien dentro del límite 1900 de Discord.

---

## Fix: awesome-architecture false positive (github.py)

Repos tipo `awesome-architecture`, `awesome-python`, `awesome-selfhosted` se colaban
en los resultados porque tienen topic `llm` o `generative-ai` auto-tageado.

**Solución:** regex `_AWESOME_NOISE` que filtra `awesome-*` excepto los explícitamente
de AI (`awesome-ai`, `awesome-llm`, `awesome-chatgpt`, etc.).

```python
_AWESOME_NOISE = re.compile(
    r"^[^/]*/awesome-(?!ai|llm|generative|chatgpt|gpt|langchain|rag|ml|machine-learning)",
    re.IGNORECASE,
)
```

---

## Decisiones de diseño

### --no-agent en vez de agent mode
El cron usa `--no-agent` — Hermes ejecuta el script y entrega stdout directo a Discord
sin pasar por el LLM. Razones:
- $0 costo (no llama a OpenRouter)
- Determinístico (mismo formato siempre)
- Rápido (< 5s)
- No falla por timeouts del LLM

### Formatter separado para digest vs. chat
`digest.py` tiene su propio formatter, distinto al `_format_response()` en el plugin:
- Digest: compacto, sin agrupar por fuente en noticias, límites más estrictos (max 4/4/5/3)
- Chat: completo, agrupado por fuente, con instrucciones para el LLM

### Límite Discord 1900 chars
Discord limita mensajes a 2000 chars. Usamos 1900 como límite conservador.
Si el digest supera 1900, `format_discord_digest()` lo divide en múltiples mensajes.
En la práctica entra en uno solo.

---

## Deploy script al homelab (si se modifica)

```bash
# Desde WSL2 (después de git push)
ssh clawnest-homelab "cd ~/clawnest && git pull && docker compose build ai_intel --no-cache && docker compose up -d ai_intel"

# Actualizar script (si cambia)
scp skills/ai_intel/scripts/ai_digest.sh clawnest-homelab:~/.hermes/scripts/ai_digest.sh
```

---

## Verificación final (2026-05-27)

| Test | Resultado |
|---|---|
| `/health` en ai_intel v1.3.0 | ✅ `{"status":"ok"}` |
| `/digest?days=7` endpoint | ✅ 1739 chars, 1 mensaje |
| `bash ai_digest.sh` manual | ✅ output correcto |
| `hermes cron run weekly-ai-digest` | ✅ `delivered to discord:1508529853127856238 via live adapter` |
| `hermes cron list` | ✅ active, next: 2026-06-01T12:00:00 UTC |

---

## Pendiente para próxima sesión

| Item | Prioridad | Notas |
|---|---|---|
| Verificar digest en Discord el 1 Jun (9am ART) | Alta | Primer run real del cron semanal |
| Renombrar `~/projects/clawnest` → `~/projects/iris` | Baja | Hacer con Claude Code cerrado |
| Digest "smart" con highlights LLM | Baja | `/digest-smart`: LLM solo para resumen ejecutivo, < $0.01/run |
| Polish + Portfolio (README, diagrama arquitectura) | Media | Útil para búsqueda laboral |
| Definir Fase 8 | Alta | Opciones: job tracker, smart digest, arxiv summarizer |
