#!/bin/sh
set -e

# Substitute environment variables in nginx template
export STB_PORT="${STB_PORT:-34400}"
export WEB_PORT="${WEB_PORT:-8080}"
envsubst '${STB_PORT} ${WEB_PORT}' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx in background.
nginx

# Run gunicorn in the foreground.
exec gunicorn --worker-class gthread -w $((2*$(nproc)+1)) --threads 8 -b 0.0.0.0:8000 main:app