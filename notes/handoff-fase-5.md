# Handoff: Fase 5 — RAG con Qdrant (search_my_docs)

## Status
✅ Completado — 2026-05-26

---

## Qué se construyó

### Skill `search_my_docs` — FastAPI microservice en Docker

**Directorio en repo:** `skills/search_my_docs/`

```
skills/search_my_docs/
  main.py              — FastAPI: /search, /ingest, /health, /collections
  models/schemas.py    — Pydantic v2: SearchRequest, IngestRequest, etc.
  requirements.txt     — fastapi, uvicorn, httpx, qdrant-client, pydantic
  Dockerfile           — python:3.11-slim, puerto 8001
  hermes_plugin/
    plugin.yaml        — define el plugin para Hermes
    __init__.py        — handlers HTTP + schemas JSON para el LLM
```

**Endpoints:**
- `GET  /health`       — verifica conexión con Qdrant
- `POST /search`       — query en lenguaje natural → chunks relevantes de Qdrant
- `POST /ingest`       — texto → chunking → embedding → upsert en Qdrant
- `GET  /collections`  — lista colecciones con cantidad de puntos

### Plugin Hermes — `~/.hermes/plugins/search-my-docs/`

Registra dos tools en Hermes:
- `search_my_docs` — busca en la knowledge base personal
- `ingest_doc` — indexa un nuevo documento

Ambas tools están en el toolset `hermes-discord-minimal`.

**Para actualizar el plugin en el homelab después de cambios en el repo:**
```bash
cd ~/clawnest && git pull origin main
cp skills/search_my_docs/hermes_plugin/__init__.py ~/.hermes/plugins/search-my-docs/
cp skills/search_my_docs/hermes_plugin/plugin.yaml ~/.hermes/plugins/search-my-docs/
systemctl --user restart hermes-gateway
```

### Embeddings

- Modelo: `openai/text-embedding-3-small` vía OpenRouter
- Dimensión: 1536
- Costo estimado: ~$0.002/mes para uso personal
- API key: la misma `OPENROUTER_API_KEY` que usa Hermes

---

## Estado del homelab al final de la sesión

```
Docker:
  iris-qdrant        → healthy, puerto 6333
  iris-search-docs   → healthy, puerto 8001

Hermes:
  Plugin search-my-docs → cargado y activo
  Tools: search_my_docs + ingest_doc en toolset hermes-discord-minimal

Qdrant:
  Colección 'docs' → 1 punto (notas-rag, chunk de prueba)
  Colección 'test_memoria' → 4 puntos (de pruebas anteriores)

Config Hermes (~/.hermes/config.yaml):
  plugins:
    enabled:
      - search-my-docs
```

---

## Test de integración — resultado

**Ingest:**
> "guardá esto en mi knowledge base: RAG es..."
- Iris usó `ingest_doc` ✅
- Respuesta: "Listo, guardado en tu knowledge base como notas-rag"
- Qdrant: colección 'docs' creada, 1 chunk indexado ✅

**Search:**
> "¿qué es RAG según mis notas?"
- Iris usó `search_my_docs` ✅
- Devolvió el contenido exacto del chunk indexado ✅
- Auto-comentario: *"Justo lo que estamos haciendo ahora — yo busco en tu knowledge base y uso eso como contexto para responderte"* 🎯

---

## Bugs encontrados y resueltos durante la implementación

1. **`max_result_size_chars` no aceptado por `PluginContext.register_tool()`**
   Fix: removido el parámetro, agregado `toolset="search-my-docs"` requerido.

2. **Plugin copiado al homelab antes del fix** — archivo viejo pisó el correcto.
   Fix: `git pull` en homelab + re-copia del archivo.

---

## Issues conocidos / deuda técnica

1. **Plugin no se auto-actualiza** — si se modifica `hermes_plugin/__init__.py` en el repo,
   hay que copiarlo manualmente al homelab y reiniciar gateway.
   Fix futuro: script de deploy o symlink desde `~/clawnest/` a `~/.hermes/plugins/`.

2. **Un solo chunk** por el texto corto de prueba. Para documentos largos el chunking
   (500 palabras, 50 overlap) va a generar múltiples chunks correctamente.

3. **Sin autenticación en la API** — el servicio escucha en `0.0.0.0:8001`.
   Aceptable en homelab privado con Tailscale, pero agregar auth si se expone públicamente.

4. **`ingest_doc` pasa el texto completo como string por Discord** — para PDFs largos
   habrá que agregar un endpoint que acepte URL o file upload.

---

## Comandos útiles

```bash
# Ver estado de la skill
curl http://localhost:8001/health
curl http://localhost:8001/collections

# Buscar manualmente (debug)
curl -s -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "RAG", "limit": 3}' | python3 -m json.tool

# Logs de la skill
docker compose -f ~/clawnest/docker-compose.yml logs -f search_my_docs

# Reiniciar solo la skill
docker compose -f ~/clawnest/docker-compose.yml restart search_my_docs
```

---

## Próxima sesión: Fase 6 — Skills hub

Opciones para próximas tools:
- `arxiv_search` — buscar papers nuevos por tema
- `rss_ingest` — suscribirse a feeds y auto-indexar en Qdrant
- `github_trending` — qué repos están trending en un tema
- Mejorar `ingest_doc` para aceptar URLs (web_extract → ingest automático)
