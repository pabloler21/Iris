# Handoff — Fase 6: ai_intel skill (AI News Tracker)

**Fecha:** 2026-05-26  
**Estado:** ✅ Completo y deployado en homelab  
**Rama:** main (mergeado)

---

## Qué se construyó

Skill `ai_intel` — un tracker de novedades del mundo de AI accesible desde Discord via Iris.  
El usuario pregunta, Iris llama a la tool y responde con datos frescos (Modo B: pull/on-demand).

### Secciones de output

| Sección | Fuentes | Endpoint |
|---|---|---|
| 🤖 Modelos nuevos | OpenRouter API + HuggingFace API | `/models` |
| ⭐ Repos GitHub | GitHub Search API (3 topics, dedup) | `/repos` |
| 📰 Noticias | 7 RSS feeds (OpenAI, DeepMind, TLDR AI, ArXiv, HN, Google AI, HuggingFace Blog) | `/news` |
| 📚 Cursos y certificaciones | 5 feeds educativos (NVIDIA DLI, Coursera, fast.ai, Google Dev, AWS ML) | `/courses` |

---

## Stack técnico

- FastAPI microservicio en Docker (`iris-ai-intel`, puerto 8002)
- Hermes user plugin en `~/.hermes/plugins/ai-intel/__init__.py`
- `asyncio.gather()` para fetch concurrente de todas las fuentes
- `feedparser` + `httpx` para RSS
- Keyword matching con **word boundaries** (`re.compile(r'\b...\b')`) para evitar falsos positivos

---

## Decisiones de diseño importantes

### Fechas inline en noticias
Problema: el LLM parafrasea el output de tools y descarta metadatos en líneas separadas.  
Solución: fechas pegadas al título `• [26-may] Título 🔗 URL` → no se pueden omitir sin romper la oración.  
Aplica a: `_fmt_news()` y `_fmt_courses()` en `hermes_plugin/__init__.py`.

### Keyword filter solo en título (no summary)
El campo `summary` de posts técnicos frecuentemente contiene keywords educativos en contexto no educativo
(ej: "radiologist specialization", "training loss"). Checkear solo el `title` elimina falsos positivos.

### 3-topic strategy en GitHub
Búsquedas separadas por `topic:llm`, `topic:generative-ai`, `topic:large-language-model` + merge + dedup.
`_is_ai_related()` verifica SOLO nombre + descripción (no el array de topics) para evitar repos auto-taggeados.

### Mode B (pull/on-demand)
El usuario consulta → Iris responde. No hay polling/schedule. Evita gasto de API credits sin necesidad.

---

## Archivos clave

```
skills/ai_intel/
├── main.py                    # FastAPI: /health /models /repos /news /courses /summary
├── models/schemas.py          # ModelEntry, RepoEntry, NewsEntry, CourseEntry, IntelResponse
├── sources/
│   ├── openrouter.py          # GET /api/v1/models con Authorization header
│   ├── huggingface.py         # GET /api/models filtrando por KNOWN_ORGS
│   ├── github.py              # GitHub Search API, 3 topics, keyword filter
│   ├── rss_feeds.py           # 7 feeds de noticias verificados
│   └── courses.py             # 5 feeds educativos, regex con word boundaries
└── hermes_plugin/__init__.py  # register(), schema, formatters

~/.hermes/plugins/ai-intel/__init__.py  # (homelab only) copia del hermes_plugin
```

---

## RSS feeds activos

### Noticias (`rss_feeds.py`)
- OpenAI: `https://openai.com/news/rss.xml`
- Google DeepMind: `https://deepmind.google/blog/rss.xml`
- Google AI: `https://blog.google/technology/ai/rss/`
- HuggingFace Blog: `https://huggingface.co/blog/feed.xml`
- TLDR AI: `https://tldr.tech/api/rss/ai`
- ArXiv cs.AI: `https://rss.arxiv.org/rss/cs.AI`
- Hacker News AI: `https://hnrss.org/newest?q=LLM+OR+...`

### Cursos (`courses.py`)
- NVIDIA DLI: `https://developer.nvidia.com/blog/feed/`
- Coursera: `https://blog.coursera.org/feed/`
- fast.ai: `https://www.fast.ai/index.xml`
- Google Dev: `https://developers.googleblog.com/feeds/posts/default`
- AWS ML: `https://aws.amazon.com/blogs/machine-learning/feed/`

### Excluidos (sin RSS funcional)
- Anthropic: sin RSS oficial ni feed comunitario estable
- Meta AI: sin RSS
- DeepLearning.AI: 404 en todos los paths probados
- Mistral: sin RSS público

---

## Patches del homelab (no en repo)

Ver `~/.hermes/hermes-agent/` — ver `AGENTS.md` sección "Critical patches".  
Si Hermes auto-actualiza, re-aplicar los patches o Iris tendrá errores de conexión a OpenRouter.

---

## Bugs conocidos / pendientes

| Issue | Estado | Notas |
|---|---|---|
| `awesome-architecture` en repos GitHub | Pendiente | Pasa el filtro porque tiene "llm" en descripción. Revisar `_is_ai_related()`. |
| Cursos vacíos en semanas sin anuncios | Aceptado | Comportamiento correcto. La sección no aparece si no hay contenido. |
| `ai_intel` container rebuild lento | Conocido | `--no-cache` tarda ~90s. Normal para el Dockerfile con pip install. |

---

## Próxima fase (Fase 7 — pendiente definición)

Ideas posibles:
- Alertas proactivas opcionales (schedule semanal para un resumen del lunes)
- Integración con Google Calendar para novedades de eventos/conferencias de AI
- Mejorar sección de repos GitHub (filtro de calidad más estricto)
- Skills adicionales según necesidades que surjan
