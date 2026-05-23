# Handoff: Fase 1 - Preparación del homelab

## Status
✅ Completed — 2026-05-23

## Completed
- Sistema actualizado (apt update/upgrade) con herramientas base instaladas
- openssh-server instalado y habilitado como servicio systemd
- SSH configurado con llaves (PasswordAuthentication no, PermitRootLogin no,
  PubkeyAuthentication yes)
- Llave pública ed25519 de WSL2 agregada a authorized_keys del homelab
- Tailscale instalado y autenticado en el homelab
- Tailscale SSH habilitado (sudo tailscale up --ssh)
- Tailscale instalado en Windows (compu principal)
- SSH alias configurado en WSL2 (~/.ssh/config): `ssh clawnest-homelab`
- Repo clonado en ~/clawnest del homelab

## Network info
- Hostname homelab: pablo-MS-7721
- IP Tailscale homelab: 100.109.56.91
- SSH alias: clawnest-homelab → pablo@100.109.56.91
- Cuenta Tailscale: pabloo.ale1111@gmail.com

## SSH config en WSL2 (~/.ssh/config)
```
Host clawnest-homelab
    HostName 100.109.56.91
    User pablo
    IdentityFile ~/.ssh/id_ed25519
```

## Decisions made
- Tailscale sobre Cloudflare Tunnel (ver ADR 003)
- SSH con llaves ed25519, password auth desactivado

## Files created/modified
- decisions/003-tailscale-vs-cloudflare.md
- notes/handoff-fase-1.md (este archivo)
- ~/.ssh/config en WSL2 (no en el repo — es config local)

## Pending
- Ninguno — listo para Fase 2

## Bugs / issues encontrados
- Los comandos sed en el terminal del homelab fallaban por saltos de línea
  en el copy/paste. Solución: usar nano directamente.
- El agente del homelab (OpenCode/Kimi) no puede ejecutar sudo interactivo.
  Solución: el usuario ejecuta los comandos con sudo manualmente.

## Next session: Fase 2 (Docker + Qdrant)
- Todo se hace por SSH desde la compu principal: `ssh clawnest-homelab`
- Agente recomendado: OpenCode con Kimi K2 (boilerplate de docker-compose)
- Al final crear decisions/004-qdrant-config.md y handoff-fase-2.md

## Notes for next agent
- El homelab ya tiene git y el repo clonado en ~/clawnest
- Conectarse siempre via: ssh clawnest-homelab
- No hay Docker instalado todavía — ese es el primer paso de la Fase 2
