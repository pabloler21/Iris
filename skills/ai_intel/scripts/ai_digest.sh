#!/usr/bin/env bash
# ai_digest.sh — Digest semanal de AI para Iris (modo cron --no-agent)
#
# Uso: invocado por Hermes cron con --no-agent --script ai_digest.sh
# El stdout se entrega verbatim a Discord. Sin LLM en el loop.
#
# Deploy: cp skills/ai_intel/scripts/ai_digest.sh ~/.hermes/scripts/ai_digest.sh
#         chmod +x ~/.hermes/scripts/ai_digest.sh

set -euo pipefail

ENDPOINT="http://localhost:8002/digest?days=7"

# Verificar que el servicio está up
if ! curl -sf "http://localhost:8002/health" > /dev/null 2>&1; then
    echo "⚠️ ai_intel no disponible — digest semanal no generado." >&2
    exit 0
fi

# Llamar al endpoint y dejar que Python parsee la respuesta
# curl -sf: silent + fail-on-error; si falla → exit sin output (Hermes ignora silent exit)
curl -sf "$ENDPOINT" | python3 -c "
import sys, json

try:
    data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f'⚠️ Error al parsear digest: {e}', file=sys.stderr)
    sys.exit(0)

messages = data.get('messages', [])
if not messages:
    print('📬 Sin novedades esta semana.')
    sys.exit(0)

# Imprimir mensajes (cada uno < 1900 chars, diseñado para caber en Discord)
print('\n\n'.join(messages))
"
