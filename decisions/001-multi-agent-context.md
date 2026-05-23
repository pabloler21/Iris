# ADR 001: Multi-agent context management with AGENTS.md + CLAUDE.md symlink

## Context
This project will be developed using multiple AI coding agents (Claude Code,
OpenCode with Kimi K2, possibly Codex/Cursor in the future). Each agent needs
project context to be effective, but maintaining duplicate context files would
cause drift.

## Options considered
- Maintain separate CLAUDE.md and AGENTS.md: high risk of drift
- Use only CLAUDE.md: would break OpenCode and other non-Claude agents
- Use only AGENTS.md: Claude Code doesn't read it natively
- Symlink CLAUDE.md → AGENTS.md: single source of truth, both agents work

## Decision
Use AGENTS.md as primary context file, create symlink CLAUDE.md → AGENTS.md.

## Justification
- AGENTS.md is the Linux Foundation-backed open standard for 2026
- Most modern coding agents support it natively
- Symlink solves Claude Code's lack of native AGENTS.md support
- Single file to maintain, zero drift risk
- Future-proof: when Claude Code adds AGENTS.md support, just delete the symlink

## Consequences
- Pro: One source of truth across all agents
- Pro: Easy to maintain
- Con: Symlinks require admin on native Windows (not an issue with WSL2)
- Con: Some legacy tools might not follow symlinks (none we use)

## Date
2026-05-23

## Author
Pablo + Claude Code (claude-sonnet-4-6)
