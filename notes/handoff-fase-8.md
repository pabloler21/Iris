# Handoff — Fase 8: Smart Digest + Better Sources

**Fecha:** 2026-05-27  
**Estado:** ✅ Completo y deployado en homelab  
**Rama:** main (mergeado)  

---

## Qué se construyó

El digest semanal ahora es un **newsletter personalizado curado por Gemini Flash**.
Iris selecciona los items más relevantes para Pablo y agrega contexto por qué importa cada uno.

**Antes (Fase 7):** lista RSS formateada — todos los items en orden de feed  
**Ahora (Fase 8):** Gemini Flash elige el top, agrega "por qué importa" por item

---

## Cambios de fuentes RSS

Sacar (mucho ruido):
- ~~ArXiv cs.AI~~ — 500 papers/día, muy académico
- ~~Hacker News AI~~ — falsos positivos frecuentes

Agregar (alta señal):
- **Simon Willison** (`simonwillison.net/atom/everything/`) — diario, herramientas prácticas para AI developers
- **Interconnects** (`interconnects.ai/feed`) — Nathan Lambert, análisis mensual de tendencias LLM
- **Ahead of AI** (`magazine.sebastianraschka.com/feed`) — Sebastian Raschka, deep dives en arquitecturas

The Batch (DL.AI): RSS 404 → excluido.

---

## Arquitectura del smart digest

```
GET /digest-smart?days=7
    ↓ fetch all sources in parallel (igual que /digest)
    ↓ build compact feed text para el prompt
    ↓ POST → OpenRouter → google/gemini-2.0-flash-001
    ↓ Gemini selecciona + añade "por qué importa" por item
    ↓ DigestResponse(messages=[curated text], curated_by_llm=True)
    ↓ (fallback a digest.py si Gemini falla)
```

**Costo estimado:** < $0.002/run (800 tokens input + 700 tokens output con Gemini Flash)  
**Tiempo de respuesta:** ~5-8s (Gemini Flash, sin reasoning tokens)

---

## Por qué Gemini Flash y no Kimi K2.6

Kimi K2.6 es un reasoning model — gasta >2000 tokens "pensando" antes de responder.
Para una tarea de formateo/selección, esto es overhead puro: `content=null` con tokens agotados.

Gemini 2.0 Flash: sin reasoning overhead, ~2-5s, excelente en instrucciones de formato.

**Principio de diseño:** right model for the right task.
- Kimi K2.6 → agent Iris (conversación compleja, multi-step)
- Gemini Flash → digest curation (selección + formato, tarea simple)

---

## Archivos modificados/creados

```
skills/ai_intel/smart_digest.py          # NUEVO: LLM curation layer
skills/ai_intel/sources/rss_feeds.py     # RSS_FEEDS refactored (3 feeds nuevos, 2 eliminados)
skills/ai_intel/main.py                  # /digest-smart endpoint (v2.0.0)
skills/ai_intel/scripts/ai_digest.sh     # Cambia a /digest-smart
```

---

## Commits de esta sesión

```
feat(ai_intel): smart digest — Kimi curation layer + better RSS sources (v2.0.0)
fix(smart_digest): increase max_tokens to 1600 for Kimi reasoning model
fix(smart_digest): reduce prompt size + raise max_tokens to 2500
fix(smart_digest): use Gemini Flash for curation, not Kimi K2.6
fix(smart_digest): prevent URL hallucination + stricter prompt
fix(smart_digest): explicit URL labels in feed + clearer format instruction
```

---

## Output verificado del digest (2026-05-27)

```
📬 **AI Weekly · 20–27 may 2026**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Modelos
· **Qwen: Qwen3.7 Max [OpenRouter]** — Modelo de Qwen con contexto de 1000K.
  → *por qué importa:* Contexto enorme para RAG o agentes complejos.
· **xAI: Grok Build 0.1 [OpenRouter]** — El Grok actualizado en OpenRouter.
  → *por qué importa:* Una opción más para diversificar tus APIs.

📰 Noticias
· **Shipping a Trillion Parameters With a Hub Bucket**
  → https://huggingface.co/blog/delta-weight-sync
  → *por qué importa:* Útil si experimentás con fine-tuning distribuido.
...
```

**Stats:** curated_by_llm=True, ~1600 chars  
**Entrega Discord:** ✅ `delivered to discord:1508529853127856238 via live adapter`

---

## Comandos de gestión

```bash
# Test del endpoint
curl -s http://localhost:8002/digest-smart?days=7 | python3 -m json.tool

# Test del script
bash ~/.hermes/scripts/ai_digest.sh

# Forzar ejecución del cron
~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main cron run weekly-ai-digest

# Ver últimas entregas
grep 'cron.scheduler\|delivered' ~/.hermes/logs/agent.log | tail -10
```

---

## Pendiente para próxima sesión

| Item | Prioridad | Notas |
|---|---|---|
| Recibir y evaluar el primer digest el lunes 1 jun (9am ART) | Alta | Ver si la curaduría de Gemini es útil en la práctica |
| Polish: prompt tuning del digest | Media | Puede necesitar ajustes según feedback del 1er run real |
| Polish + Portfolio (README, diagrama arq, demo GIF) | Media | Útil para búsqueda laboral |
| Renombrar `~/projects/clawnest` → `~/projects/iris` | Baja | Con Claude Code cerrado |
| Definir Fase 9 | Media | Según feedback del digest real |
