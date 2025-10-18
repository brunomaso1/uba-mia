#!/usr/bin/env bash
set -e

# Ruta al .env (si no viene como argumento, usar el root por defecto)
ENV_FILE="${1:-.env}"

echo "Cargando variables de entorno desde $ENV_FILE..."
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "No se encontró $ENV_FILE"
    exit 1
fi

echo "Configurando Guardrails..."

echo "Ejecutando la configuración post-instalación de Guardrails..."
uv run guardrails hub install hub://guardrails/regex_match hub://guardrails/valid_json hub://guardrails/web_sanitization

echo "Configuración completa."