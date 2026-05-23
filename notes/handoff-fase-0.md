# Handoff: Fase 0 - Setup de contexto

## Status
✅ Completed — 2026-05-23

## Completed
- Initial repo structure
- AGENTS.md with project constitution (stack, rules, branching strategy, user context)
- CLAUDE.md symlinked to AGENTS.md (multi-agent compatibility)
- Folder structure: notes/, decisions/, backend/src/, skills/, nginx/
- .gitignore with security defaults (secrets, caches, CLAUDE.local.md)
- Initial README.md
- decisions/000-template.md — ADR template
- decisions/001-multi-agent-context.md — why AGENTS.md + symlink
- decisions/002-branching-strategy.md — main + feature/fase-X, no dev branch
- First commit pushed to GitHub

## Decisions made
- AGENTS.md as primary context file (cross-tool standard, see ADR 001)
- CLAUDE.md symlinked to AGENTS.md (see ADR 001)
- Branching: main + feature/fase-X, no dev branch (see ADR 002)
- Phase 0 setup goes directly to main (no feature branch needed for scaffolding)

## Files created
- AGENTS.md
- CLAUDE.md → AGENTS.md (symlink)
- .gitignore
- README.md
- notes/handoff-fase-0.md (this file)
- decisions/000-template.md
- decisions/001-multi-agent-context.md
- decisions/002-branching-strategy.md

## Pending
- None — ready to start Fase 1

## Bugs / issues
- None

## Next session: Fase 1 (Preparación del homelab)
- Requires PHYSICAL access to the Linux Mint machine (no SSH yet)
- Recommended agent: OpenCode with Kimi K2
- Read AGENTS.md first, then this note, then proceed with Fase 1 from the plan
- At end of Fase 1, create decisions/003-tailscale-vs-cloudflare.md

## Notes for next agent
- CLAUDE.md symlink works on Linux/WSL2/Mac. Native Windows requires admin.
  Verify with: ls -la CLAUDE.md
- Branching from Fase 1 onwards: git checkout -b feature/fase-1 before starting
- The plan technical document is clawnest-plan-tecnico.md in the repo root
