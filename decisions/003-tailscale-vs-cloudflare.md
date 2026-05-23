# ADR 003: Tailscale vs Cloudflare Tunnel para conectividad remota

## Context
El homelab necesita ser accesible remotamente para desarrollo por SSH y
eventualmente para exponer el webhook de Telegram públicamente. Hay dos
opciones principales para esto en 2026.

## Options considered

- **Tailscale:** VPN mesh peer-to-peer basada en WireGuard. Cada dispositivo
  conectado recibe una IP privada fija (100.x.x.x). Incluye Tailscale SSH
  (autenticación delegada a Tailscale) y Tailscale Funnel (exposición pública
  selectiva de puertos). Gratis hasta 3 usuarios / 100 dispositivos.

- **Cloudflare Tunnel:** Túnel saliente desde el homelab hacia Cloudflare.
  No requiere IP pública ni abrir puertos. Mejor para exponer servicios web
  públicos con dominio propio. Más complejo de configurar para SSH puro.

## Decision
Tailscale para conectividad entre dispositivos (SSH) y Tailscale Funnel para
exposición pública del webhook de Telegram.

## Justification
- Setup en minutos vs configuración más larga de Cloudflare
- Tailscale SSH elimina la necesidad de gestionar authorized_keys en múltiples
  dispositivos a futuro
- Tailscale Funnel cubre el único caso de uso público que necesitamos
  (webhook de Telegram en Fase 4)
- La IP Tailscale es fija y no cambia aunque el homelab cambie de red local
- Plan gratuito más que suficiente para uso personal

## Consequences
- Pro: SSH desde cualquier dispositivo con Tailscale instalado, sin configurar nada extra
- Pro: No hay puertos abiertos al internet público (solo Tailscale Funnel cuando se active)
- Pro: Si el ISP cambia la IP pública, no afecta en nada
- Con: Requiere Tailscale instalado en cada dispositivo cliente
- Con: Tailscale Funnel tiene limitaciones de ancho de banda en plan gratuito

## IPs asignadas
- Homelab (pablo-ms-7721): `100.109.56.91`

## Date
2026-05-23

## Author
Pablo + Claude Code (claude-sonnet-4-6)
