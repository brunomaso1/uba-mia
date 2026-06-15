#!/bin/sh
# Reemplazar las variables de entorno en la plantilla JSON
# Whitelist de variables de entorno que se pueden usar en el template
# Cargo las variables whitelistadas en VARS, luego uso envsubst para reemplazarlas en el template y generar config.json
VARS="$(grep -o '\${[A-Za-z_][A-Za-z0-9_]*}' /usr/share/nginx/html/config.template.json | sort -u | tr '\n' ' ')"
envsubst "$VARS" < /usr/share/nginx/html/config.template.json > /usr/share/nginx/html/config.json

# Ejecutar el comando que viene por defecto (Nginx)
exec "$@"