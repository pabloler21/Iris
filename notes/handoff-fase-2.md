# Handoff: Fase 2 — Docker + Qdrant

## Status
✅ Completed — 2026-05-24

## Completed

- Docker Engine 29.5.2 instalado en el homelab (via script oficial get.docker.com)
- Usuario pablo agregado al grupo docker
- docker-compose.yml creado en la raíz del repo con servicio Qdrant
- Qdrant 1.18.1 corriendo en Docker, puertos 6333 (REST/dashboard) y 6334 (gRPC)
- Volume persistente configurado en ./data/qdrant
- Healthcheck configurado y pasando
- Script de exploración creado en scripts/explore_qdrant.py
- Insert + search verificados — búsqueda semántica funcionando correctamente

## Estado actual del homelab

```
docker ps → clawnest-qdrant corriendo (Up, healthy)
Qdrant API: http://localhost:6333
Qdrant dashboard: http://100.109.56.91:6333/dashboard  (vía Tailscale)
```

## Archivos creados/modificados

- `docker-compose.yml` — servicio Qdrant con volume persistente
- `scripts/explore_qdrant.py` — script de exploración insert + search
- `decisions/004-qdrant-config.md` — ADR con justificación de la elección
- `notes/handoff-fase-2.md` — este archivo

## Bugs / issues encontrados

- `sudo` via SSH automático no funciona (requiere TTY interactivo).
  Solución: Pablo corrió `curl -fsSL https://get.docker.com | sudo sh`
  desde una terminal WSL2 separada con `ssh clawnest-homelab`.
- El repo en el homelab estaba 3 commits atrás — resuelto con git pull.

## Decisiones tomadas

- Qdrant sobre Pinecone/Chroma/pgvector (ver ADR 004)
- Sin autenticación en Qdrant por ahora — red Tailscale es el perímetro de seguridad
- data/ en .gitignore — los datos no se commitean al repo

## Para hacer Qdrant persistente al reinicio

Qdrant ya tiene `restart: unless-stopped` en docker-compose.yml.
Para que Docker arranque automáticamente al boot del homelab:
```bash
sudo systemctl enable docker
```
(Esto se hace en la Fase 7 como parte del polish de producción)

## Next session: Fase 3 (OpenClaw + Kimi K2)

- Instalar Node.js 20+ en el homelab
- Instalar OpenClaw via hackable method (git clone)
- Configurar OpenRouter como provider con API key
- Configurar modelo (verificar ID correcto en openrouter.ai/models antes de empezar)
- Levantar OpenClaw como servicio systemd
- Nota: el modelo "Kimi 2.6" mencionado por Pablo requiere verificación del model ID
  exacto en OpenRouter antes de configurarlo

## Notes for next agent

- Conectarse siempre via: ssh clawnest-homelab
- Qdrant corre en Docker, NO tocar manualmente
- El repo en el homelab está en ~/clawnest y sigue la branch feature/fase-2
  (a mergear a main al final de esta fase)
- scripts/explore_qdrant.py muestra cómo funciona insert + search
