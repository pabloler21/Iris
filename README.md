# Iris

Personal AI assistant running 24/7 on Linux homelab, accessible via Discord.
Portfolio piece for AI Engineer Jr — Pablo, Buenos Aires.

## Status
Fase 3.5 completada — bot Iris respondiendo en Discord.

| Fase | Descripción | Estado |
|------|-------------|--------|
| 0 | Setup de contexto y repo | ✅ Completa |
| 1 | Homelab SSH + Tailscale | ✅ Completa |
| 2 | Docker + Qdrant | ✅ Completa |
| 3 | Hermes Agent + LLM via OpenRouter | ✅ Completa |
| 3.5 | Migración a Hermes + Discord + Gemini Flash | ✅ Completa |
| 4 | Pulido: rename repo, /sethome, ddgs fix | 🔜 Próxima |
| 5 | RAG con Qdrant (search_my_docs skill) | ⏳ Pendiente |
| 6 | Skills hub: arxiv, blogwatcher, github | ⏳ Pendiente |
| 7 | Polish + deploy final | ⏳ Pendiente |

## Stack activo en el homelab

- **Hermes Agent 0.14.0** — gateway del agente, systemd user service (`hermes-gateway`)
- **Gemini 2.0 Flash** (google/gemini-2.0-flash-001) — LLM via OpenRouter
- **Discord** — canal de mensajería (bot: Iris#4138)
- **DuckDuckGo (ddgs)** — web search sin API key
- **Qdrant 1.18.1** — corriendo en Docker, puerto 6333 (listo para RAG en Fase 5)
- **Tailscale** — red privada para acceso remoto seguro
- **SSH con llaves ed25519** — sin password auth

## Documentation
- [Project context for AI agents](AGENTS.md)
- [Architecture decisions](decisions/)
- [Session handoff notes](notes/)

## Multi-agent compatibility
This project is built using multiple AI coding agents.
CLAUDE.md is symlinked to AGENTS.md for unified context across all tools.
