# Iris

Personal AI assistant running 24/7 on Linux homelab, accessible via Discord.
Portfolio piece for AI Engineer Jr — Pablo, Buenos Aires.

## Status
Fase 6 completada — ai_intel skill operativa: modelos, repos GitHub, noticias y cursos de AI.

| Fase | Descripción | Estado |
|------|-------------|--------|
| 0 | Setup de contexto y repo | ✅ Completa |
| 1 | Homelab SSH + Tailscale | ✅ Completa |
| 2 | Docker + Qdrant | ✅ Completa |
| 3 | Hermes Agent + LLM via OpenRouter | ✅ Completa |
| 3.5 | Migración a Hermes + Discord + Gemini Flash | ✅ Completa |
| 4 | Pulido: rename → Iris, fix APIConnectionError post-ddgs | ✅ Completa |
| 5 | RAG con Qdrant (search_my_docs + ingest_doc) | ✅ Completa |
| 6 | ai_intel: tracker de novedades AI (modelos, repos, noticias, cursos) | ✅ Completa |
| 7 | Por definir | ⏳ Pendiente |

## Stack activo en el homelab

- **Hermes Agent 0.14.0** — gateway del agente, systemd user service (`hermes-gateway`)
- **DeepSeek V4 Flash** (deepseek/deepseek-v4-flash) — LLM via OpenRouter
- **Discord** — canal de mensajería (bot: Iris#4138)
- **DuckDuckGo (ddgs)** — web search sin API key
- **Qdrant 1.18.1** — corriendo en Docker, puerto 6333
- **ai_intel** — Docker, puerto 8002 — tracker de novedades AI (modelos, repos, noticias, cursos)
- **search_my_docs** — Docker, puerto 8001 — RAG sobre knowledge base personal
- **Tailscale** — red privada para acceso remoto seguro
- **SSH con llaves ed25519** — sin password auth

## Documentation
- [Project context for AI agents](AGENTS.md)
- [Architecture decisions](decisions/)
- [Session handoff notes](notes/)

## Multi-agent compatibility
This project is built using multiple AI coding agents.
CLAUDE.md is symlinked to AGENTS.md for unified context across all tools.
