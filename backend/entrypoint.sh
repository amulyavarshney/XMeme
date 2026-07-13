#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head || echo "Alembic baseline skipped/failed; continuing with create_all/migrate.py"

echo "Starting XMeme API..."
exec gunicorn -c gunicorn.conf.py src.main:app
