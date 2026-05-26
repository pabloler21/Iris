# Handoff: Fase 4 — Rename Iris + Fix APIConnectionError post-ddgs

## Status
✅ Completado — 2026-05-26

---

## Cambios de esta sesión

### 1. Rename ClawNest → Iris (completado)

| Artefacto | Cambio |
|---|---|
| AGENTS.md / CLAUDE.md | Reescrito: Iris, Hermes/Discord/Gemini Flash, patches documentados |
| docker-compose.yml | `container_name: clawnest-qdrant` → `iris-qdrant` |
| README.md | Título `Iris (ex-ClawNest)` → `Iris` |
| GitHub repo | Renombrado a `pabloler21/Iris` (hecho manualmente en UI) |
| git remote | `git remote set-url origin git@github.com:pabloler21/Iris.git` |
| settings.local.json | Path interno actualizado a /iris |

**Pendiente del rename:** renombrar directorio local `~/projects/clawnest` → `~/projects/iris`
(hacerlo con una sesión de Claude Code cerrada):
```bash
mv ~/projects/clawnest ~/projects/iris
cd ~/projects/iris
```

### 2. Fix APIConnectionError post-ddgs (Patch v2 en run_agent.py)

**Root cause confirmado** (vía logs):
- ddgs tarda 4-9s en buscar
- Hermes intenta reusar la conexión TCP keep-alive a OpenRouter
- OpenRouter cerró esa conexión mientras ddgs buscaba (idle timeout)
- Resultado: `APIConnectionError` en el primer intento → retry de 2.5s → total 30-45s

**Fix aplicado** en `~/.hermes/hermes-agent/run_agent.py`:
```python
# _build_keepalive_http_client — PATCH v2
return _httpx.Client(
    http2=False,
    proxy=_proxy,
    limits=_httpx.Limits(max_keepalive_connections=0, max_connections=10),
)
```
`max_keepalive_connections=0` fuerza una conexión TCP nueva en cada llamada a la API.
Nunca reutiliza conexiones potencialmente stale.

**Backup:** `~/.hermes/hermes-agent/run_agent.py.bak2`

**Resultado verificado post-fix:**
- API call #2 latency: 2.0s (antes: 32-44s con retry)
- `tcp_force_closed=0` (antes: `1`)
- Sin `APIConnectionError` ni `attempt 1/3`
- Tiempo total de respuesta: 22s (antes: 45-70s)

---

## Estado del homelab al final de la sesión

```
systemctl --user status hermes-gateway → active (running), enabled
Hermes v0.14.0
Modelo: deepseek/deepseek-v4-flash  ← cambiado de gemini-2.0-flash-001 (2026-05-26)
Provider: OpenRouter
Bot Discord: Iris#4138 — conectada y respondiendo
Config: ~/.hermes/config.yaml

Patches activos en el homelab (no en repo):
  run_agent.py        — PATCH v2: http2=False + max_keepalive_connections=0
  conversation_loop.py — PATCH: non-streaming forzado (sin cambios esta sesión)
```

---

## Issues conocidos / deuda técnica (post Fase 4)

1. **Directorio local sin renombrar**: `~/projects/clawnest` → `~/projects/iris`
   Hacerlo cuando no haya sesión de Claude Code activa.

2. **Latencia ~22s** con web search — normal dado que ddgs tarda ~8s + OpenRouter ~2s + overhead.
   Mejorable en fases futuras (cambiar a ddgs con backend más rápido, o brave-free si se consigue API key gratis).

3. **Patches locales al código de Hermes** — si Hermes se actualiza, se pierden.
   Considerar reportar como issues upstream o hacer fork del repo.

4. **Discord connect timeout al arrancar** — ocurrió una vez (15:39 hoy), el reconnection watcher lo resolvió solo.
   No requiere acción.

---

## Comandos útiles

```bash
# Ver estado
systemctl --user status hermes-gateway

# Logs en tiempo real
tail -f ~/.hermes/logs/agent.log

# Reiniciar
systemctl --user restart hermes-gateway

# Verificar patch v2 activo
grep -A3 'PATCH v2' ~/.hermes/hermes-agent/run_agent.py

# Verificar patch non-streaming activo
grep -A3 'PATCH: disable streaming' ~/.hermes/hermes-agent/agent/conversation_loop.py
```

---

## Próxima sesión: Fase 5 — RAG con Qdrant

- Diseñar skill `search_my_docs` como FastAPI microservice en Docker
- Conectar Qdrant (ya corriendo en Docker, puerto 6333) al agente via tool
- Implementar ingesta de documentos (PDFs, markdown) y búsqueda semántica
- Embeddings: decidir provider (OpenAI text-embedding-3-small via OpenRouter, o local con sentence-transformers)
