# Handoff: Fase 3 — OpenClaw + Kimi K2.6

## Status
✅ Completed — 2026-05-24

## Completed

- Node.js 22.22.3 instalado via nvm (sistema tenía Node 18, insuficiente)
- nvm configurado como default en ~/.bashrc del homelab
- OpenClaw 2026.5.22 instalado via npm global
- OpenRouter configurado como provider con API key en ~/.openclaw/secrets.env
- Modelo configurado: openrouter/moonshotai/kimi-k2.6
- max_tokens=8192 configurado (fix al context overflow)
- Gateway corriendo como systemd user service (enabled + active)
- loginctl linger habilitado → servicio sobrevive reinicios sin login
- Prueba exitosa: agente respondió "Soy openrouter/moonshotai/kimi-k2.6"

## Estado actual del homelab

```
systemctl --user status openclaw-gateway → active (running), enabled
Linger=yes (sobrevive reinicios)

Gateway: ws://127.0.0.1:18789 (solo local, no expuesto aún)
Modelo: openrouter/moonshotai/kimi-k2.6
Max tokens: 8192

docker ps → clawnest-qdrant Up, healthy
```

## Archivos creados/modificados

- `decisions/005-openclaw-openrouter-kimi.md` — ADR con justificación de stack
- `notes/handoff-fase-3.md` — este archivo
- `README.md` — actualizado a Fase 3 completa

## Archivos SOLO en el homelab (no en repo — secretos)

- `~/.openclaw/secrets.env` — API key de OpenRouter (chmod 600)
- `~/.openclaw/openclaw.json` — config de OpenClaw con modelo y params

## Bugs / issues encontrados

- Node 18 preinstalado: insuficiente para OpenClaw (requiere 22+). Fix: nvm.
- Context overflow (max_tokens default = contexto completo del modelo). Fix: 8192.
- Healthcheck Qdrant con curl (no disponible en imagen). Fix: /dev/tcp (ya aplicado en Fase 2).
- `openclaw agent` sin --session-key falla si hay sesión corrupta. Fix: limpiar .jsonl.

## Next session: Fase 4 (Telegram + Nginx + Tailscale Funnel)

### Prerequisito: tener el token del bot de Telegram
Antes de arrancar Fase 4, crear el bot con @BotFather:
1. Hablar con @BotFather en Telegram
2. `/newbot` → nombre: ClawNest → username: clawnest_bot (o similar)
3. Guardar el token (formato: 123456789:AABBcc...)
4. Obtener tu user ID de Telegram con @userinfobot

### Pasos de Fase 4
1. Configurar Tailscale Funnel (expone puerto 80 públicamente)
2. Levantar Nginx en Docker (reverse proxy)
3. Conectar Telegram channel en OpenClaw (`openclaw channels add telegram`)
4. Configurar allowed_users con tu user ID (seguridad)
5. Probar mensaje desde el celular → respuesta de Kimi K2.6

## Notes for next agent

- OpenClaw corre como: `systemctl --user status openclaw-gateway`
- Para ver logs: `journalctl --user -u openclaw-gateway -f`
- API key en: `~/.openclaw/secrets.env` (no tocar, no commitear)
- Config en: `~/.openclaw/openclaw.json`
- Para recargar config: `systemctl --user restart openclaw-gateway`
- nvm debe sourciarse antes de usar node/openclaw:
  `export NVM_DIR="$HOME/.nvm" && source "$NVM_DIR/nvm.sh"`
