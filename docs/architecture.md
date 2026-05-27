# Iris — Architecture Reference

## System Diagram (Mermaid)

```mermaid
flowchart TB
    User(["👤 Pablo\n(Discord)"])

    subgraph Host["🖥️  Linux Homelab — systemd"]
        direction TB
        Hermes["Hermes Agent 0.14.0\n(Python process, always-on)"]
        Cron["Hermes Cron\nMon 09:00 ART"]
        DDG["DuckDuckGo\nweb search (fallback)"]
    end

    subgraph Docker["🐳  Docker Compose"]
        direction TB
        AiIntel["iris-ai-intel\nFastAPI · :8002\n\n/models /repos /news\n/courses /summary\n/digest /digest-smart"]
        SearchDocs["iris-search-docs\nFastAPI · :8001\n\n/search /ingest\n/collections"]
        Qdrant["iris-qdrant\nQdrant · :6333\n\nvector storage"]
    end

    subgraph OpenRouter["☁️  OpenRouter API"]
        Kimi["Kimi K2.6\nmain agent LLM"]
        Gemini["Gemini 2.0 Flash\ndigest curation"]
        Embed["text-embedding-3-small\n1536d embeddings"]
    end

    subgraph External["☁️  External Data Sources"]
        GH["GitHub Search API\n(trending repos)"]
        HF["HuggingFace API\n(new models)"]
        RSS["RSS Feeds\nOpenAI · DeepMind · HuggingFace\nTLDR AI · Simon Willison\nInterconnects · Ahead of AI\nGoogle AI"]
        CourseRSS["Course RSS Feeds\nNVIDIA DLI · Coursera\nfast.ai · Google Dev · AWS ML"]
    end

    %% User <-> Agent
    User <-->|"Discord messages"| Hermes

    %% Agent tools
    Hermes <-->|"LLM inference"| Kimi
    Hermes <--> DDG
    Hermes <-->|"HTTP tool call"| AiIntel
    Hermes <-->|"HTTP tool call"| SearchDocs

    %% RAG pipeline
    SearchDocs <-->|"vector ops"| Qdrant
    SearchDocs <-->|"embed query/chunks"| Embed

    %% ai_intel data sources
    AiIntel <-->|"new models"| Kimi
    AiIntel <--> HF
    AiIntel <--> GH
    AiIntel <--> RSS
    AiIntel <--> CourseRSS
    AiIntel <-->|"curate digest"| Gemini

    %% Push mode (cron)
    Cron -->|"--no-agent\nai_digest.sh"| AiIntel
    Cron -->|"Discord DM\n(no LLM)"| User

    %% Styles
    classDef host fill:#1e3a5f,stroke:#4a90d9,color:#fff
    classDef docker fill:#1a4731,stroke:#4caf50,color:#fff
    classDef api fill:#4a1942,stroke:#ce93d8,color:#fff
    classDef ext fill:#3d2b00,stroke:#ffa726,color:#fff
    classDef user fill:#1a1a2e,stroke:#e94560,color:#fff

    class Hermes,Cron,DDG host
    class AiIntel,SearchDocs,Qdrant docker
    class Kimi,Gemini,Embed api
    class GH,HF,RSS,CourseRSS ext
    class User user
```

---

## Component Responsibilities

| Component | Responsibility | Location |
|---|---|---|
| **Hermes Agent** | Orchestrates conversations, routes to tools, manages sessions | Host (systemd) |
| **Kimi K2.6** | Main LLM — complex reasoning, tool selection, response formatting | OpenRouter cloud |
| **Gemini 2.0 Flash** | Weekly digest curation — selects top items, adds context per item | OpenRouter cloud |
| **iris-ai-intel** | Fetches and structures AI industry data (models, repos, news, courses) | Docker :8002 |
| **iris-search-docs** | RAG service — chunk, embed, store, retrieve personal documents | Docker :8001 |
| **iris-qdrant** | Vector database for semantic search | Docker :6333 |
| **Hermes Cron** | Schedules weekly digest delivery without agent involvement | Host (embedded in gateway) |

---

## Key Flows

### Flow A — On-demand query
```
User (Discord)
  → Hermes (routes to LLM)
    → Kimi K2.6 (decides: tool call or direct answer)
      → iris-ai-intel OR iris-search-docs OR DuckDuckGo
        ← structured data
      ← formatted response
  ← Discord message
```

### Flow B — Weekly digest (Push mode, Mondays 09:00 ART)
```
Hermes Cron
  → ai_digest.sh (shell script, no LLM)
    → iris-ai-intel /digest-smart
      → [parallel] OpenRouter API + HuggingFace API + GitHub API + RSS feeds
      → Gemini 2.0 Flash (curates: selects top items + adds "why it matters")
      ← Discord-ready text (<1900 chars)
    ← stdout
  → Discord DM (direct delivery, bypasses Hermes agent)
```

---

## Port Map

| Port | Service | Notes |
|---|---|---|
| 6333 | iris-qdrant | REST API + web dashboard |
| 6334 | iris-qdrant | gRPC (high-performance clients) |
| 8001 | iris-search-docs | RAG skill |
| 8002 | iris-ai-intel | AI news tracker |

All ports are internal (localhost). No public exposure — access via Tailscale VPN.

---

## Network Topology

```
Internet
    │
    │ (no direct exposure)
    │
Linux Mint Homelab ────── Tailscale VPN ────── Dev machine (Windows/WSL2)
    │                     100.109.56.91              SSH alias: clawnest-homelab
    │
    ├── Hermes Agent (host)
    ├── Docker network (iris_default)
    │       ├── iris-ai-intel
    │       ├── iris-search-docs
    │       └── iris-qdrant
    └── OpenRouter API (HTTPS, outbound only)
```

---

## Model Selection Rationale

| Task | Model | Why |
|---|---|---|
| Main agent LLM | Kimi K2.6 | Follows complex routing instructions correctly; DeepSeek V4 Flash hallucinated tool outputs |
| Digest curation | Gemini 2.0 Flash | No reasoning overhead (~5s response); Kimi K2.6 spends 2000+ tokens "thinking" on simple formatting tasks |
| Embeddings | text-embedding-3-small | OpenAI-compatible API via OpenRouter; 1536d cosine similarity |

*Principle: right model for the right task — reasoning models are expensive for deterministic formatting.*
