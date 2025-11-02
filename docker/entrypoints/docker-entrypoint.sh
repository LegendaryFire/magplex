#!/bin/sh
set -e

# Substitute environment variables in nginx template
export STB_PORT="${STB_PORT:-34400}"
export WEB_PORT="${WEB_PORT:-8080}"
envsubst '${STB_PORT} ${WEB_PORT}' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/conf.d/default.conf

# Link nginx logs to stdout/stderr
ln -sf /dev/stdout /var/log/nginx/access.log
ln -sf /dev/stderr /var/log/nginx/error.log

# Start nginx in background.
nginx


if [ "$PYCHARM_DEBUG" = "1" ]; then
    echo "Starting MagPlex in PyCharm debugger mode..."
    exec python /main.py
else
    # Run gunicorn in the foreground.
    exec gunicorn -c gunicorn.conf.py main:app
fi
