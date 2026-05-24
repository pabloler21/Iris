# ADR 004: Qdrant en Docker como vector database

## Context

ClawNest necesita una base de datos vectorial para la memoria semántica extendida
del agente (Fase 5). Necesitamos elegir la tecnología y definir cómo correrla
en el homelab con 16GB RAM y sin GPU.

## Options considered

- **Qdrant en Docker**: open source, self-hosted, liviano, API REST + gRPC, UI web
- **Pinecone**: SaaS managed, no requiere infra propia, tiene costo por uso
- **Chroma**: open source, más simple, menos features de producción
- **pgvector**: extensión de PostgreSQL, requiere Postgres instalado

## Decision

Qdrant corriendo en Docker con volume persistente en `./data/qdrant`.

## Justification

- **Self-hosted**: los datos del usuario no salen del homelab (privacidad)
- **Docker**: fácil de levantar, reiniciar y actualizar sin tocar el sistema base
- **Volume persistente**: los datos sobreviven reinicios del contenedor
- **Qdrant sobre Chroma**: mejor performance, UI web incluida, más mantenido en 2026
- **Qdrant sobre pgvector**: no queremos dependencia de PostgreSQL aún
- **Pinecone descartado**: costo recurrente, datos en la nube, no encaja con homelab

## Configuration

```yaml
# docker-compose.yml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"  # REST API + dashboard
      - "6334:6334"  # gRPC
    volumes:
      - ./data/qdrant:/qdrant/storage
    restart: unless-stopped
```

## Consequences

- Pro: privacidad total, costo cero, control total sobre actualizaciones
- Pro: UI web accesible via Tailscale en `http://100.109.56.91:6333/dashboard`
- Pro: API REST simple, cliente Python oficial disponible
- Con: responsabilidad de mantenimiento y backups (se atiende en Fase 7)
- Con: ocupa ~200MB de RAM en idle (aceptable con 16GB)

## Date
2026-05-24

## Author
Pablo + Claude Code
