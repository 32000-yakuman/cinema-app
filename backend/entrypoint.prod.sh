#!/bin/sh
set -e

echo "Waiting for MySQL..."

until mysql \
  --skip-ssl \
  -h app-db \
  -u "$MYSQL_USER" \
  -p"$MYSQL_PASSWORD" \
  -e "SELECT 1" > /dev/null 2>&1
do
    sleep 2
done

echo "MySQL is ready."

python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 60