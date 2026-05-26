# Handoff: Fase 4 — Migración a Hermes Agent + Discord

## Status
✅ Completado — 2026-05-25 (migración + fix crítico de Connection error)

## Cambios respecto a Fase 3

La Fase 3 usaba **OpenClaw** (Node.js). Esa decisión fue revertida:
- OpenClaw fue deprecado
- Migrado a **Hermes Agent v0.14.0** (Python) vía `hermes claw migrate`
- Canal cambiado de Telegram → **Discord** (bot Iris#4138)
- Modelo cambiado de kimi-k2.6 → **google/gemini-2.0-flash-001** (vía OpenRouter)

Ver ADR 006 (pendiente de crear) para la justificación.

## Bug Crítico Resuelto: APIConnectionError en Gateway

### Síntoma
Cada mensaje enviado a Discord fallaba con:
```
APIConnectionError: Connection error.
RemoteProtocolError: Server disconnected without sending a response.
```
Los 3 reintentos fallaban. El agente respondía con mensaje de error genérico.

### Root Cause
OpenRouter droppeaba las conexiones SSE (streaming) cuando el payload de tools
era grande (~52KB, 33 herramientas definidas para la plataforma Discord).

- Sin tools: funciona en <2s
- Con 5 tools: funciona
- Con 15 tools: funciona con ~75s de latencia
- Con 33 tools: **FALLA 100% de las veces** en modo streaming

El non-streaming con 33 tools funciona (aunque lento, ~15-50s).

### Fix Aplicado
**Archivo:** `~/.hermes/hermes-agent/agent/conversation_loop.py`
**Backup:** `~/.hermes/hermes-agent/agent/conversation_loop.py.bak`

Cambiado el bloque `elif not agent._has_stream_consumers()` para que use
non-streaming cuando no hay stream consumers (el gateway Discord sin streaming
habilitado no tiene stream consumers).

**Antes:**
```python
elif not agent._has_stream_consumers():
    # No display/TTS consumer. Still prefer streaming for
    # health checking, but skip for Mock clients in tests
    from unittest.mock import Mock
    if isinstance(getattr(agent, "client", None), Mock):
        _use_streaming = False
```

**Después:**
```python
elif not agent._has_stream_consumers():
    # No display/TTS consumer. Skip streaming to avoid provider
    # connection issues with large tool payloads (e.g. OpenRouter
    # drops streaming connections silently when tools payload is
    # large for certain models). Non-streaming is reliable here.
    # PATCH: disable streaming when no consumers (was: skip only for Mock).
    _use_streaming = False
```

### Comportamiento Post-Fix
- Los logs muestran `chat_completion_request` (non-streaming) en vez de
  `chat_completion_stream_request` (streaming)
- El primer intento puede fallar ocasionalmente (~50% chance) por inconsistencia
  de OpenRouter con payloads grandes, pero el reintento siempre funciona
- El gateway completa correctamente las conversaciones con 1-2 intentos

## Estado actual del homelab

```
systemctl --user status hermes-gateway → active (running), enabled
Linger=yes (sobrevive reinicios sin login)

Hermes v0.14.0
Modelo: google/gemini-2.0-flash-001
Provider: openrouter
Bot Discord: Iris#4138
Config: ~/.hermes/config.yaml
Logs: ~/.hermes/logs/agent.log
```

## Archivos creados/modificados

### En el repo
- `notes/handoff-fase-4.md` — este archivo

### Solo en el homelab (no commitear)
- `~/.hermes/.env` — API keys (OPENROUTER_API_KEY, DISCORD_TOKEN, etc.)
- `~/.hermes/config.yaml` — configuración de Hermes
- `~/.hermes/hermes-agent/agent/conversation_loop.py` — PATCHEADO
- `~/.hermes/hermes-agent/agent/conversation_loop.py.bak` — backup pre-patch
- `~/.hermes/hermes-agent/run_agent.py.bak` — backup original run_agent.py
- `~/.hermes/hermes-agent/run_agent.py` — tiene patches de HTTP/2 (http2=False)

## Issues conocidos / deuda técnica

1. **Latencia alta**: Las respuestas toman 15-87s con 33 tools y gemini-2.0-flash
   Causa: OpenRouter es lento para este modelo con payloads grandes.
   Alternativa: probar `moonshotai/kimi-k2` que puede ser más rápido con tools.

2. **Primer intento intermitente**: ~50% de las veces el primer attempt falla
   con RemoteProtocolError (OpenRouter dropea conexión). El retry funciona.
   Fix potencial: reducir toolset Discord, o cambiar modelo.

3. **Patch en archivo fuera de repo**: el fix en conversation_loop.py no está
   en el repo clawnest (está en ~/.hermes/hermes-agent/). Si Hermes se actualiza,
   el patch se pierde. Considerar reportar issue upstream o hacer fork.

4. **ADR 006 pendiente**: Documentar la decisión de migrar OpenClaw → Hermes.

5. **README desactualizado**: Aún muestra Fase 2/3 con OpenClaw como activo.

## Comandos útiles

```bash
# Ver estado del gateway
systemctl --user status hermes-gateway

# Ver logs en tiempo real
journalctl --user -u hermes-gateway -f
# o bien
tail -f ~/.hermes/logs/agent.log

# Reiniciar gateway
systemctl --user restart hermes-gateway

# Ver configuración
cat ~/.hermes/config.yaml

# Verificar que el patch está aplicado
grep -A3 'PATCH: disable streaming' ~/.hermes/hermes-agent/agent/conversation_loop.py
```

## Próxima sesión: Fase 5 (Memoria RAG con Qdrant)

- Diseñar skill RAG custom sobre Qdrant (ya en Docker, puerto 6333)
- Conectar Qdrant al agente como skill de FastAPI
- Implementar ingesta de documentos y búsqueda semántica
- Ver task #12: "Diseñar skill RAG custom sobre Qdrant"
