# ClawNest

Personal AI assistant running on Linux homelab.

## Status
Currently in development — Fase 2 completed.

| Fase | Descripción | Estado |
|------|-------------|--------|
| 0 | Setup de contexto y repo | ✅ Completa |
| 1 | Homelab SSH + Tailscale | ✅ Completa |
| 2 | Docker + Qdrant | ✅ Completa |
| 3 | OpenClaw + LLM via OpenRouter | 🔜 Próxima |
| 4 | Integración Telegram | ⏳ Pendiente |
| 5 | Memoria extendida (Qdrant) | ⏳ Pendiente |
| 6 | Job Tracker | ⏳ Pendiente |
| 7 | Polish + deploy final | ⏳ Pendiente |

## Stack activo en el homelab

- **Qdrant 1.18.1** — corriendo en Docker, puerto 6333
- **Tailscale** — red privada para acceso remoto seguro
- **SSH con llaves ed25519** — sin password auth

## Documentation
- [Project context for AI agents](AGENTS.md)
- [Architecture decisions](decisions/)
- [Session handoff notes](notes/)

## Multi-agent compatibility
This project is built using multiple AI coding agents.
CLAUDE.md is symlinked to AGENTS.md for unified context across all tools.
