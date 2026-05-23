# ADR 002: Branching strategy — main + feature/fase-X

## Context
This is a solo project with a clear phase-based roadmap. We need a branching
strategy that keeps main stable without adding overhead from long-lived branches
(like a permanent dev branch).

## Options considered
- Trunk-based (everything to main): simple, but risky if a phase breaks something
- Gitflow (main + dev + feature): overkill for solo, too much ceremony
- main + feature/fase-X (no dev): clean phase isolation, low overhead

## Decision
Use `main` as the stable branch. Each phase from Phase 1 onwards gets its own
short-lived feature branch named `feature/fase-X`. Branches are merged to main
and deleted when the phase is complete.

Phase 0 (this setup) goes directly to main — it's pure scaffolding with no
application logic that could break anything.

## Justification
- main is always deployable (important for a 24/7 homelab assistant)
- feature/fase-X branches provide isolation while a phase is in progress
- No dev branch avoids the "dev vs main drift" problem common in gitflow
- Low ceremony for a solo project — one active branch at a time

## Consequences
- Pro: main is always clean and deployable
- Pro: Easy to see which phase is in progress (just check active branches)
- Pro: Minimal branch overhead for a solo developer
- Con: If two phases need to be worked on in parallel (unlikely), we'd need
  to adapt this strategy

## Date
2026-05-23

## Author
Pablo + Claude Code (claude-sonnet-4-6)
