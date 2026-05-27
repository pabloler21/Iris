# Guía completa de Iris — Para Pablo

Este archivo es tu manual de operaciones personal. Explica **qué hace cada parte,
por qué está hecha así, y cómo mantenerla**. No está pensado para GitHub — es para vos.

---

## Qué es Iris

Un asistente personal de AI que corre 24/7 en tu homelab y respondés desde Discord.
No es un chatbot genérico — tiene herramientas específicas para tus necesidades:

1. **Buscar en tus documentos** — le metés texto, lo indexa, lo encontrás semánticamente
2. **Rastrear novedades de AI** — modelos, repos, noticias, cursos
3. **Mandarte un digest semanal** — el lunes a las 9am llegó solo a tu DM, curado por IA

La metáfora: un asistente real al que le das acceso a herramientas específicas.

---

## Los tres sistemas que conviven

### 1. Hermes Agent (el agente en sí)

**Qué es:** Un proceso Python que corre permanentemente en tu homelab como servicio systemd.
Es el "cerebro" que coordina todo.

**Dónde vive:** En el host (NO en Docker). Tiene que correr en el host porque necesita
acceso al filesystem, a la red, y al sistema operativo.

**Cómo arranca:** `systemctl --user start hermes-gateway`

**Qué hace:**
- Conecta con Discord y escucha mensajes
- Cuando llega un mensaje, lo manda al LLM (Kimi K2.6 via OpenRouter)
- Kimi decide qué herramientas usar (search_my_docs, ai_intel, web_search)
- Llama a los servicios correspondientes por HTTP
- Le devuelve la respuesta formateada a Discord

**Archivos importantes (homelab, NO en repo):**
```
~/.hermes/config.yaml      # Config principal: modelo, plataformas, plugins
~/.hermes/SOUL.md          # Personalidad + reglas de routing de Iris
~/.hermes/.env             # Secrets: OPENAI_API_KEY (=OpenRouter), DISCORD_BOT_TOKEN
~/.hermes/plugins/         # Plugins de Hermes (ai-intel, search-my-docs)
~/.hermes/logs/            # Logs de todo
```

**Gotcha crítico:** La API key de OpenRouter va como `OPENAI_API_KEY` en `~/.hermes/.env`
(no `OPENROUTER_API_KEY`). Hermes viene hardcodeado con el nombre de OpenAI.

---

### 2. Los servicios Docker (las "herramientas")

Iris tiene dos skills propias corriendo como containers:

```
docker ps
NAMES               PORTS
iris-ai-intel       0.0.0.0:8002→8002   ← tracker de novedades AI
iris-search-docs    0.0.0.0:8001→8001   ← RAG sobre tus documentos
iris-qdrant         0.0.0.0:6333→6333   ← base de datos vectorial
```

Hermes se comunica con ellos por HTTP (localhost:8001, localhost:8002).
Qdrant no lo toca Hermes directamente — lo usa `iris-search-docs` internamente.

**Por qué en Docker y no en el host:**
- Aislamiento: si un servicio crashea, no mata al agente
- Reproducibilidad: rebuild en un comando
- Separación de dependencias (cada uno tiene su `requirements.txt`)

---

### 3. OpenRouter (los modelos de IA)

Todo el inference va a OpenRouter — no hay nada local, no necesitás GPU.

**Qué modelos usás:**
| Modelo | Para qué | Costo aprox. |
|---|---|---|
| `moonshotai/kimi-k2.6` | Agente principal — conversaciones, razonamiento | ~$0.014/M tokens |
| `google/gemini-2.0-flash-001` | Curaduría del digest semanal | ~$0.0004/M tokens |
| `openai/text-embedding-3-small` | Embeddings para RAG | $0.02/M tokens |

**Por qué Kimi K2.6 para el agente:**
Seguía instrucciones de routing correctamente (DeepSeek V4 Flash las ignoraba).
Ver ADR 005 y handoff Fase 6 para el detalle completo.

**Por qué Gemini Flash para el digest:**
Kimi K2.6 es un *reasoning model* — gasta 2000+ tokens "pensando" antes de responder,
incluso para tareas simples de formateo. Gemini Flash no tiene ese overhead, responde en
~5s y es perfecto para "seleccioná los mejores items y formateálos".

---

## Flujo de datos detallado

### Cuando le mandás un mensaje a Iris

```
Vos en Discord
    ↓ "¿qué modelos nuevos salieron esta semana?"
Hermes recibe el mensaje
    ↓
Kimi K2.6 piensa:
  "necesito datos frescos → voy a llamar a ai_intel con type='models'"
    ↓
Hermes llama: GET http://localhost:8002/models?days=7
    ↓
iris-ai-intel:
  - llama OpenRouter API para modelos nuevos
  - llama HuggingFace API para modelos de orgs conocidas
  - devuelve JSON estructurado con ModelEntry[]
    ↓
Kimi recibe los datos y redacta la respuesta
    ↓
Hermes envía el mensaje formateado a Discord
```

### Cuando cae el digest del lunes

```
Hermes cron (lunes 12:00 UTC = 09:00 ART)
    ↓ ejecuta ~/.hermes/scripts/ai_digest.sh
bash script:
  curl http://localhost:8002/digest-smart?days=7
    ↓
iris-ai-intel:
  - fetch modelos, repos, noticias, cursos EN PARALELO
  - manda todo a Gemini Flash: "elegí el top, agregá por qué importa"
  - Gemini devuelve texto Discord-ready
  - la respuesta llega en 5-8s
    ↓
bash script imprime el texto a stdout
    ↓
Hermes entrega stdout a Discord DM (sin pasar por el LLM — --no-agent)
    ↓
Vos recibís el AI Weekly en el DM
```

---

## La skill `ai_intel` por dentro

### Fuentes de datos

**Modelos nuevos:**
- `sources/openrouter.py` → llama `GET https://openrouter.ai/api/v1/models` con Authorization header
- `sources/huggingface.py` → llama `GET https://huggingface.co/api/models` filtrando por orgs conocidas (OpenAI, Anthropic, Google, etc.)

**Repos GitHub:**
- `sources/github.py` → GitHub Search API, sin API key (rate limit público)
- Búsqueda en 3 topics: `llm`, `generative-ai`, `large-language-model`
- Deduplicación por `full_name` + filtro de keywords AI en nombre/descripción
- Fix de Fase 8: regex `_AWESOME_NOISE` filtra `awesome-architecture` y similares

**Noticias:**
- `sources/rss_feeds.py` → 8 feeds RSS (feedparser + httpx)
- Feeds actuales: OpenAI, Google DeepMind, Google AI, HuggingFace Blog, TLDR AI, Simon Willison, Interconnects (Nathan Lambert), Ahead of AI (Sebastian Raschka)
- Removidos en Fase 8: ArXiv cs.AI (demasiado volumen) y HN AI (mucho ruido)

**Cursos:**
- `sources/courses.py` → 5 feeds RSS educativos
- Keyword matching con `\b` word boundaries (evita "course" matcheando "Coursera")
- Solo matchea en el `title`, no en el `summary` (el summary tiene muchos falsos positivos)
- DeepLearning.AI NO tiene RSS → cubierto por `web_search` en Kimi (instrucción en SOUL.md)

### Endpoints

| Endpoint | Usado por |
|---|---|
| `/summary` | Plugin de Hermes (cuando preguntás en Discord) |
| `/digest` | Fallback del cron (formato determinístico, $0) |
| `/digest-smart` | Cron semanal (Gemini Flash cura el contenido) |

### El plugin de Hermes

El archivo `skills/ai_intel/hermes_plugin/__init__.py` es el "conector" entre Hermes y el servicio Docker.
Cuando Kimi decide llamar a `ai_intel`, Hermes ejecuta este plugin que:
1. Hace HTTP GET al servicio Docker
2. Formatea la respuesta JSON en texto para el LLM (con fechas inline para que Kimi no las pierda)

**Cómo actualizar el plugin en el homelab:**
```bash
cp skills/ai_intel/hermes_plugin/__init__.py ~/.hermes/plugins/ai-intel/__init__.py
systemctl --user restart hermes-gateway
```

---

## La skill `search_my_docs` por dentro

### Cómo funciona el RAG

1. **Ingest:** Mandás texto a Iris ("guardá esto")
   - El servicio divide el texto en chunks (por palabras, con overlap)
   - Genera un embedding por chunk (1536 dimensiones con `text-embedding-3-small`)
   - Guarda los chunks + embeddings en Qdrant

2. **Search:** Hacés una pregunta
   - Genera embedding de la pregunta
   - Busca los N chunks más similares por cosine similarity en Qdrant
   - Devuelve los chunks relevantes + scores

3. **Kimi usa los resultados** para responder en contexto

### Qdrant

Es la base de datos vectorial. Guarda los embeddings y los chunks originales.
Los datos persisten en `./data/qdrant/` (bind mount en docker-compose.yml).
Si el container se cae y relevantás, los datos siguen ahí.

---

## Los patches críticos de Hermes (homelab)

Hay dos archivos en `~/.hermes/hermes-agent/` que están modificados manualmente.
**Si Hermes se auto-actualiza, hay que re-aplicarlos o el bot va a tener errores de conexión.**

### Patch 1: `agent/conversation_loop.py`
```python
# Fuerza non-streaming (evita SSE drops de OpenRouter)
else:
    _use_streaming = False
```
OpenRouter a veces corta conexiones SSE en el medio del stream. Esto fuerza modo non-streaming.

### Patch 2: `run_agent.py`
```python
# Deshabilita HTTP/2 y keepalive connections
def _build_keepalive_http_client():
    return httpx.Client(
        http2=False,
        limits=httpx.Limits(max_keepalive_connections=0, max_connections=10)
    )
```
Evita errores de TLS/keepalive con la API de OpenRouter.

**Cómo verificar si están aplicados:**
```bash
grep "use_streaming = False" ~/.hermes/hermes-agent/agent/conversation_loop.py
grep "http2=False" ~/.hermes/hermes-agent/run_agent.py
```

---

## Mantenimiento del día a día

### Ver si Iris está viva

```bash
# Estado del servicio
systemctl --user status hermes-gateway

# Últimos logs (incluye si Discord está conectado)
journalctl --user -u hermes-gateway -n 30

# Estado de los containers Docker
docker ps

# Logs de un container específico
docker logs iris-ai-intel --tail 20
```

### Reiniciar Iris

```bash
# Solo el agente
systemctl --user restart hermes-gateway

# Solo el container ai_intel
cd ~/clawnest && docker compose restart ai_intel

# Todo
cd ~/clawnest && docker compose restart
systemctl --user restart hermes-gateway
```

### Actualizar después de cambios en el repo

```bash
cd ~/clawnest

# Pull de los cambios
git pull origin main

# Rebuild del container que cambió (sin caché)
docker compose build ai_intel --no-cache
docker compose up -d ai_intel

# Si cambiaste el plugin de Hermes
cp skills/ai_intel/hermes_plugin/__init__.py ~/.hermes/plugins/ai-intel/__init__.py
systemctl --user restart hermes-gateway
```

### Agregar documentos al RAG

```bash
# Via Discord — mandá el texto a Iris directamente:
"guardá esto en mis notas: [texto]"

# Via curl directo al servicio
curl -X POST http://localhost:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "tu texto aquí",
    "source": "nombre del documento",
    "collection": "personal",
    "chunk_size": 200,
    "chunk_overlap": 30
  }'
```

### Ver el cron del digest

```bash
~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main cron list

# Forzar ejecución para testear
~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main cron run weekly-ai-digest

# Ver el output del último run
ls ~/.hermes/cron/output/efb842b408ac/
cat ~/.hermes/cron/output/efb842b408ac/*.md | tail -50
```

---

## Variables de entorno

Hay **dos** archivos `.env` y es importante no confundirlos:

### `~/.hermes/.env` (homelab, solo para Hermes)
```env
OPENAI_API_KEY=sk-or-...        # ← KEY DE OPENROUTER (no es de OpenAI, pero Hermes la llama así)
DISCORD_BOT_TOKEN=...
DISCORD_ALLOWED_USERS=1036628709735673916
```

### `~/clawnest/.env` (homelab, para Docker)
```env
OPENROUTER_API_KEY=sk-or-...    # ← misma key, nombre correcto
```
Los containers Docker usan este archivo via `docker-compose.yml`.

---

## Decisiones de arquitectura importantes

Si querés entender *por qué* algo está hecho de cierta forma, los ADRs son el lugar:

| ADR | Decisión |
|---|---|
| [002](decisions/002-branching-strategy.md) | Por qué `main` directo + `feature/fase-X` |
| [003](decisions/003-tailscale-vs-cloudflare.md) | Por qué Tailscale y no Cloudflare Tunnel |
| [004](decisions/004-qdrant-config.md) | Configuración de Qdrant |
| [005](decisions/005-openclaw-openrouter-kimi.md) | Por qué Kimi K2.6 (antes DeepSeek, antes Gemini) |
| [006](decisions/006-migracion-hermes-discord.md) | Migración a Hermes Agent |
| [007](decisions/007-push-mode-cron-digest.md) | Por qué `--no-agent` para el digest |

---

## Troubleshooting

### Iris no responde en Discord
```bash
# 1. Ver si el servicio está corriendo
systemctl --user status hermes-gateway

# 2. Si está crashed, ver por qué
journalctl --user -u hermes-gateway -n 50

# 3. ¿Discord conectó?
grep "Connected as Iris" ~/.hermes/logs/gateway.log | tail -3

# 4. Si no conectó, reiniciar (Discord a veces da timeout al arrancar)
systemctl --user restart hermes-gateway
```

### Iris responde pero da errores de conexión
```bash
# Verificar que los patches de Hermes están aplicados
grep "use_streaming = False" ~/.hermes/hermes-agent/agent/conversation_loop.py
grep "http2=False" ~/.hermes/hermes-agent/run_agent.py

# Si no están → re-aplicar (ver sección Patches arriba)
```

### El digest no llegó el lunes
```bash
# Ver si el cron corrió
~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main cron list
# Fijate en "Last run" y si dice "ok" o "error"

# Ver output del último run
ls ~/.hermes/cron/output/efb842b408ac/

# Testear manualmente
bash ~/.hermes/scripts/ai_digest.sh
```

### ai_intel devuelve datos viejos o errores
```bash
# Ver logs del container
docker logs iris-ai-intel --tail 30

# Healthcheck
curl http://localhost:8002/health

# Si está down, levantar
cd ~/clawnest && docker compose up -d ai_intel
```

### Qdrant / RAG no funciona
```bash
# Ver estado
docker ps | grep qdrant
curl http://localhost:6333/dashboard  # dashboard web

# Los datos están en
ls ~/clawnest/data/qdrant/
```

---

## Roadmap y notas

**Próximo a hacer (post Fase 8):**
- Ver el primer digest real el lunes 1 jun y evaluar si la curaduría es útil
- Tuning del prompt del digest según feedback
- Polish + portfolio (demo GIF, tests)

**Ideas futuras:**
- `/digest-smart` con sección de "resumen ejecutivo" de 3 líneas
- Más fuentes RSS (The Batch si arreglan el RSS, Lilian Weng's blog)
- Tracking de precios de modelos semana a semana
