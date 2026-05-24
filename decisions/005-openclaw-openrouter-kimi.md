# ADR 005: OpenClaw + OpenRouter + Kimi K2.6 como stack del agente

## Context

Necesitamos definir el framework del agente personal (OpenClaw) y el modelo LLM
que va a usar como cerebro. Estas son decisiones separadas pero relacionadas.

## Decisión 1: OpenClaw como framework

### Options considered
- **OpenClaw**: self-hosted, multicanal (Telegram/Discord/WhatsApp), Node.js, skills system
- **LangChain + FastAPI custom**: más control, mucho más trabajo de implementación
- **n8n**: no-code, menos flexible para skills custom

### Decision
OpenClaw instalado vía npm global, corriendo como systemd user service.

### Justification
- Integración nativa con Telegram (Fase 4 es solo configurar el channel)
- Sistema de skills extensible sin reimplementar el loop del agente
- Activo en 2026, buena comunidad, compatible con cualquier provider OpenAI-compatible
- Systemd user service: no requiere root, arranca automático con linger habilitado

## Decisión 2: Kimi K2.6 vía OpenRouter

### Options considered
- **moonshotai/kimi-k2.6** vía OpenRouter: MoE, 262K contexto, muy bueno en código
- **claude-sonnet-4-6** vía OpenRouter: caro para uso 24/7 personal
- **deepseek/deepseek-chat**: buena relación precio/calidad, opción de fallback

### Decision
Modelo primario: `openrouter/moonshotai/kimi-k2.6`

### Justification
- Precio razonable: $0.73/1M input, $3.49/1M output
- 262K tokens de contexto: suficiente para conversaciones largas
- Multimodal (texto + imagen): útil para futuras skills
- Kimi K2.6 salió en abril 2026, más nuevo que el K2 original del plan

## Configuration final

```
# ~/.openclaw/openclaw.json (fragmento)
agents.defaults.model        = "openrouter/moonshotai/kimi-k2.6"
agents.defaults.params.max_tokens = 8192

# ~/.openclaw/secrets.env (gitignoreado, solo en homelab)
OPENROUTER_API_KEY=sk-or-v1-...
```

## Consequences

- Pro: agente 24/7 corriendo sin intervención
- Pro: modelo de calidad a costo razonable
- Pro: linger habilitado → sobrevive reinicios del homelab sin login manual
- Con: API key solo guardada en homelab (sin backup — se regenera en OpenRouter si se pierde)
- Con: max_tokens=8192 limita respuestas muy largas (ajustable si hace falta)

## Issues encontrados y resueltos

- Context overflow: OpenClaw pedía 262K output + input > 262K límite del modelo.
  Fix: `agents.defaults.params.max_tokens = 8192`
- Sistema Node: había Node 18 instalado, OpenClaw requiere 22+.
  Fix: nvm instalado, Node 22.22.3 configurado como default
- Healthcheck de Qdrant usaba curl (no disponible en la imagen).
  Fix: cambiado a bash /dev/tcp

## Date
2026-05-24

## Author
Pablo + Claude Code
