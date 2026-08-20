#!/bin/bash
set -e

echo "Waiting for MySQL..."

until mysql --skip-ssl -h app-db -u root -p"$MYSQL_PASSWORD" -e "select 1" > /dev/null 2>&1; do
  sleep 2
done

echo "MySQL is ready."

python manage.py migrate

if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.product" ]; then
    echo "Starting in PRODUCTION mode (gunicorn)"
    python manage.py collectstatic --noinput
    gunicorn config.wsgi:application --bind 0.0.0.0:8000
else
    echo "Starting in DEVELOPMENT mode (runserver)"
    python manage.py runserver 0.0.0.0:8000
fi
