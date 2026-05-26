# Handoff — Fase 6: ai_intel skill (AI News Tracker)

**Fecha:** 2026-05-26 (actualizado al cierre de sesión)
**Estado:** ✅ Completo y deployado en homelab
**Rama:** main (mergeado)

---

## Qué se construyó

Skill `ai_intel` — tracker de novedades del mundo de AI accesible desde Discord via Iris.
El usuario pregunta, Iris llama a la tool y responde con datos frescos (Modo B: pull/on-demand).

### Secciones de output

| Sección | Fuentes | Endpoint |
|---|---|---|
| 🤖 Modelos nuevos | OpenRouter API + HuggingFace API | `/models` |
| ⭐ Repos GitHub | GitHub Search API (3 topics, dedup) | `/repos` |
| 📰 Noticias | 7 RSS feeds (OpenAI, DeepMind, TLDR AI, ArXiv, HN, Google AI, HuggingFace Blog) | `/news` |
| 📚 Cursos y certificaciones | 5 feeds RSS (NVIDIA DLI, Coursera, fast.ai, Google Dev, AWS ML) | `/courses` |

---

## Cambio de modelo — DeepSeek V4 Flash → Kimi K2.6

**Motivo:** DeepSeek ignoraba instrucciones en tool output cuando tenía training data
relevante (alucinaba cursos de DeepLearning.AI incluso con `"INSTRUCCIÓN: no agregues de tu conocimiento"`).
Kimi K2.6 sigue las instrucciones de routing correctamente.

**Archivos modificados:**
- `~/.hermes/config.yaml` (homelab): `default: moonshotai/kimi-k2.6`
- `AGENTS.md` + `README.md`: referencia de modelo actualizada
- `~/.hermes/SOUL.md` (homelab): identidad actualizada a Kimi K2.6

---

## Routing de cursos de AI

Descubrimiento clave de esta sesión: **DeepLearning.AI no tiene RSS ni API pública**, y su org en GitHub (`deeplearning-ai`) solo tiene 4 repos públicos de 2018 — no publican cursos ahí.

**Solución implementada:** routing por schema + SOUL.md

- `ai_intel(type=courses)` → cubre NVIDIA DLI, Coursera, fast.ai, Google Dev, AWS ML via RSS
- `web_search` → cubre DeepLearning.AI, Udemy, edX (Kimi lo hace automáticamente)

**Lo que se intentó y no funcionó:**
1. Instrucciones `"no halucines"` en tool output → DeepSeek/Kimi las ignoraban
2. `duckduckgo-search` lib 6.x → rate limit 202 desde Docker (curl-cffi necesita browser profiles)
3. DDG Lite via httpx → también 202 desde IPs de servidor
4. `lxml` + backend='html' → fallback a API igualmente
5. GitHub `org:deeplearning-ai` → 4 repos, ninguno es un curso
6. `web_courses.py` fue creado, iterado 5 veces, y finalmente eliminado

**Estado final del schema de ai_intel:**
```
"LÍMITE IMPORTANTE: DeepLearning.AI NO tiene RSS → si Pablo pregunta
específicamente por cursos de DeepLearning.AI, usá web_search en vez de este tool."
```

**SOUL.md rule:**
```
Para DeepLearning.AI: SIEMPRE llamá web_search con query 'new DeepLearning.AI courses [mes año]'
ANTES de responder. Nunca respondas sobre cursos de DL.AI sin buscar primero.
```

**Resultado verificado:** Kimi K2.6 llama web_search 3 veces para DL.AI (una para descubrir, dos para verificar), devuelve URLs reales con fechas correctas.

---

## Decisiones de diseño importantes

### Fechas inline en noticias y cursos
Problema: LLM parafrasea el output de tools y descarta metadatos en líneas separadas.
Solución: fechas pegadas al título `• [26-may] Título 🔗 URL` → no se pueden omitir sin romper la oración.
Aplica a: `_fmt_news()` y `_fmt_courses()` en `hermes_plugin/__init__.py`.

### Keyword filter solo en título (no summary)
El campo `summary` de posts técnicos frecuentemente contiene keywords educativos en contexto no educativo
(ej: "radiologist specialization", "training loss"). Checkear solo el `title` elimina falsos positivos.

### Word boundaries en keyword matching
`_COURSE_PATTERN = re.compile(r"\b(course|...)\b", re.I)` evita que "course" matchee "Coursera".

### 3-topic strategy en GitHub
Búsquedas separadas por `topic:llm`, `topic:generative-ai`, `topic:large-language-model` + merge + dedup.
`_is_ai_related()` verifica SOLO nombre + descripción (no el array de topics) para evitar repos auto-taggeados.

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
│   └── courses.py             # 5 feeds RSS educativos, regex con word boundaries
└── hermes_plugin/__init__.py  # register(), schema, formatters

~/.hermes/plugins/ai-intel/__init__.py  # (homelab only) copia del hermes_plugin
~/.hermes/config.yaml                   # model: moonshotai/kimi-k2.6
~/.hermes/SOUL.md                       # identidad + reglas de routing
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
- Anthropic: sin RSS oficial
- Meta AI: sin RSS
- DeepLearning.AI: 404 en todos los paths + sin repos GitHub → cubierto por web_search
- Mistral: sin RSS público

---

## Patches del homelab (no en repo)

Ver `~/.hermes/hermes-agent/` — ver `AGENTS.md` sección "Critical patches".
Si Hermes auto-actualiza, re-aplicar los patches o Iris tendrá errores de conexión a OpenRouter.

---

## Pendiente para próxima sesión

| Item | Prioridad | Notas |
|---|---|---|
| Renombrar `~/projects/clawnest` → `~/projects/iris` en WSL | Baja | Hacer con Claude Code cerrado |
| `awesome-architecture` se cuela en repos GitHub a veces | Media | Revisar `_is_ai_related()` |
| Definir Fase 7 | Alta | Opciones: job tracker, digest semanal, Arxiv summarizer, polish/portfolio |

---

## Comportamiento verificado (2026-05-26)

| Query | Tool llamada | Resultado |
|---|---|---|
| "¿qué hay de nuevo en AI esta semana?" | `ai_intel(all)` | modelos + repos + noticias + cursos RSS |
| "¿cursos de NVIDIA?" | `web_search` | datos reales, respuesta honesta |
| "¿cursos de DeepLearning.AI?" | `web_search` × 3 | URLs reales, fechas correctas |
| "¿qué modelos salieron?" | `ai_intel(models)` | OpenRouter + HuggingFace |
