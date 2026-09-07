#!/bin/sh
set -e

if [ "$NODE_ENV" = "production" ]; then
    echo "Starting in PRODUCTION mode (next build && next start)"
    npm run build
    npm run start
else
    echo "Starting in DEVELOPMENT mode (next dev)"

    if [ ! -x /app/node_modules/.bin/next ]; then
        echo "node_modules is empty. Installing dependencies..."
        npm ci
    fi

    npm run dev
fi