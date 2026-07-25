#!/bin/sh
set -e

echo "==> Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "==> Subindo Gunicorn na porta ${PORT:-8080}..."
exec gunicorn slj.wsgi --bind 0.0.0.0:${PORT:-8080}
