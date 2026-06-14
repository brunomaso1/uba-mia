#!/bin/sh
# Reemplazar las variables de entorno en la plantilla JSON
envsubst '${API_URL}' < /usr/share/nginx/html/config.template.json > /usr/share/nginx/html/config.json

# Ejecutar el comando que viene por defecto (Nginx)
exec "$@"