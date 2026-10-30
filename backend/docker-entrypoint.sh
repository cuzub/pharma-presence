#!/bin/sh
set -e

# Applique les migrations de schéma avant de démarrer (sans effet si la base est à jour).
flask db upgrade

exec gunicorn --bind 0.0.0.0:5000 --workers "${GUNICORN_WORKERS:-2}" --access-logfile - run:app
