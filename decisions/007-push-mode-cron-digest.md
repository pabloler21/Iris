# ADR 007 — Push Mode: Weekly AI Digest via Hermes Cron (--no-agent)

**Fecha:** 2026-05-27  
**Estado:** Aceptado  
**Fase:** 7  

---

## Contexto

Hasta la Fase 6, Iris operaba únicamente en **modo Pull (Modo B)**: el usuario hace una
pregunta, Iris llama al tool `ai_intel`, y responde. El usuario debe acordarse de preguntar.

Para una herramienta de seguimiento de novedades, el modo Push (Modo A) tiene más valor:
el digest llega sin que el usuario lo pida, en horario fijo, con formato consistente.

El reto era elegir la arquitectura del Push mode, teniendo en cuenta:
- Hermes tiene un sistema de cron jobs (`hermes cron create`)
- El cron puede correr con LLM (`agent mode`) o sin él (`--no-agent`)
- El servicio `ai_intel` ya tiene toda la lógica de fetch y formato

---

## Decisión

**Push mode via Hermes cron con `--no-agent`.**

El cron job ejecuta `ai_digest.sh` (script bash) que:
1. Llama `http://localhost:8002/digest?days=7`
2. Imprime las messages del JSON response a stdout
3. Hermes entrega stdout directo a Discord (sin pasar por el LLM)

El endpoint `/digest` en el servicio Docker formatea los datos en mensajes
Discord-ready (< 1900 chars) usando `digest.py`.

**Schedule:** `0 12 * * 1` (lunes 12:00 UTC = 09:00 ART)  
**Target:** `discord:1508529853127856238` (DM pl101)

---

## Alternativas consideradas

### A. Cron con LLM (agent mode)
```
hermes cron create "0 12 * * 1" "Generá el resumen semanal de AI..."
```
- ❌ Costo: ~$0.05 por run en OpenRouter (Kimi K2.6)
- ❌ No determinístico — el formato puede variar
- ❌ Puede fallar por timeout del LLM (30s+) o errores de OpenRouter
- ✅ Podría agregar comentarios o análisis del LLM

### B. Nueva skill Docker "digest"
- Un servicio FastAPI separado dedicado al digest
- ❌ Overhead innecesario — el servicio `ai_intel` ya tiene todo lo que necesita
- ✅ Cumple arquitectura de "un servicio por responsabilidad"

### C. Cron systemd directo (sin Hermes)
```
# crontab
0 12 * * 1 /home/pablo/scripts/digest.sh
```
- ❌ Requiere integración manual con Discord API
- ❌ No aprovecha Hermes routing/delivery
- ✅ Independiente de Hermes

### D. **Seleccionado: Hermes cron --no-agent + /digest endpoint**
- ✅ $0 costo (no usa LLM)
- ✅ Determinístico — mismo formato siempre
- ✅ Rápido (< 5s en ejecutarse)
- ✅ Aprovecha Hermes para delivery a Discord
- ✅ El endpoint `/digest` también es útil para debugging manual
- ✅ El formato del digest es explícitamente diferente al formato de chat
  (más compacto, sin agrupar por fuente, sin instrucciones para el LLM)

---

## Consecuencias

**Positivas:**
- Iris ahora tiene los dos modos: Pull (on-demand) y Push (cron semanal)
- El digest corre sin costo de LLM
- El formato del digest está versionado en código y es reproducible
- El endpoint `/digest` puede usarse para tests o para pedir el digest manualmente

**Negativas:**
- El digest no tiene "inteligencia" — no puede destacar las noticias más relevantes
  ni agregar contexto. Es una lista formateada.
- Si el servicio `ai_intel` está down el lunes a las 9am, no hay retry automático
  (el cron simplemente no entrega nada ese día)

**Trabajo futuro:**
- Si se quiere agregar "highlights" o análisis, se puede crear un endpoint `/digest-smart`
  que use el LLM solo para la sección de resumen ejecutivo (< $0.01 por run)
- Para retry automático, se puede agregar un health check cron que notifique si
  `ai_intel` está down

---

## Archivos creados

```
skills/ai_intel/digest.py                   # Formatter: format_discord_digest()
skills/ai_intel/models/schemas.py           # DigestResponse model
skills/ai_intel/main.py                     # GET /digest endpoint (v1.3.0)
skills/ai_intel/scripts/ai_digest.sh        # Script Hermes (deploy: ~/.hermes/scripts/)
```

**Hermes cron job:**
```
ID:       efb842b408ac
Name:     weekly-ai-digest
Schedule: 0 12 * * 1 (lunes 12:00 UTC = 09:00 ART)
Deliver:  discord:1508529853127856238 (DM pl101)
Mode:     no-agent (stdout → Discord)
```
