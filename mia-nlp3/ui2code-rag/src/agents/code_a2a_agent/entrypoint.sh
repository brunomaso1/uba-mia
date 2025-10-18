#!/bin/bash
set -e

# Check if GUARDRAILS_API_KEY is set
if [ -z "$GUARDRAILS_API_KEY" ]; then
  echo "Error: GUARDRAILS_API_KEY is not set."
  exit 1
fi

# Configurar Guardrails
poetry run guardrails configure --token "$GUARDRAILS_API_KEY" --disable-metrics --disable-remote-inferencing

# Instalar hubs si no están
poetry run guardrails hub install \
    hub://guardrails/regex_match \
    hub://guardrails/valid_json \
    hub://guardrails/web_sanitization || true

# Ejecutar servidor
exec su app -c "python -m src.server.main --port ${PORT:-10001}"