# ClawNest

Personal AI assistant running 24/7 on Linux homelab, accessible via Telegram.
Portfolio piece for AI Engineer Jr job search by Pablo (Buenos Aires).

## Stack
- Runtime: Python 3.11 (services), Node.js 20+ (OpenClaw)
- LLM: Kimi K2 via OpenRouter (model: moonshotai/kimi-k2)
- Agent framework: OpenClaw (hackable install method)
- Memory: Qdrant via Docker
- API services: FastAPI + Pydantic v2
- Reverse proxy: Nginx in Docker
- Network: Tailscale + Funnel
- OS: Linux Mint (homelab), Windows + WSL2 (dev)

## Build & Run
```bash
# Start all services on homelab
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f [service_name]

# OpenClaw runs as systemd service (NOT in Docker)
sudo systemctl status clawnest
journalctl -u clawnest -f
```

## Code conventions
- Python: ruff for lint, black for format, type hints required
- Code in English, comments in Spanish
- Commit messages in English, conventional commits format
- Async by default for I/O operations
- All Pydantic models in `models/` directories

## Architecture rules
- No LLM inference locally (use OpenRouter)
- Custom skills as separate FastAPI services in Docker
- OpenClaw runs on host, NOT in Docker (needs system access)
- All secrets in .env (never commit, gitignored)
- One service per docker-compose service

## Branching strategy
- `main` — stable, deployable. Phase 0 setup goes directly here.
- `feature/fase-X` — one branch per phase from Phase 1 onwards.
- No long-lived `dev` branch. Feature branches are merged and deleted.
- See ADR 002 for the full rationale.

## Workflow rules
This project is developed with Claude Code. To keep context coherent across sessions:
- CLAUDE.md is a symlink to this file (`ln -s AGENTS.md CLAUDE.md`)
- At the end of EVERY task, update `notes/handoff-fase-X.md`
- Create ADR in `decisions/NNN-title.md` for any architectural decision
- Update README when project status changes visibly
- Never end a session without updating context files

## Workflow
- One phase per session, max 4hs of work
- Read latest handoff note at start of session
- Always generate/update handoff note at end of session
- Update README per phase completed
- Architecture decisions documented in `decisions/NNN-title.md`

## Hard rules — never break
- Never commit .env, API keys, or tokens
- Never modify production homelab without testing locally first
- Never delete data without explicit user confirmation
- Never modify systemd services without backing up first

## User context (Pablo)
- AI Engineer Jr, transitioning from data analytics
- Strong: Python, FastAPI, LangChain, Pydantic
- Learning: Docker, Nginx, Tailscale, vector DBs
- Hardware homelab: Linux Mint, 16GB RAM, no GPU
- Dev machine: Windows 10 + WSL2
- Learning style: explain concepts before code
- Prefer Socratic questioning when learning new things
- Spanish (Rioplatense), B2 English

## Key directories
- `backend/src/` — Python services source
- `skills/` — Custom OpenClaw skills
- `notes/` — Handoff notes between sessions (READ ON SESSION START)
- `decisions/` — Architecture Decision Records (ADRs)
- `nginx/` — Reverse proxy config

## When in doubt
- Read latest handoff note in `notes/`
- Check `decisions/` for past architectural choices
- Ask before changing existing patterns
