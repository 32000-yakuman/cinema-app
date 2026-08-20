#!/bin/sh
set -e

if [ "$NODE_ENV" = "production" ]; then
    echo "Starting in PRODUCTION mode (next build && next start)"
    npm run build
    npm run start
else
    echo "Starting in DEVELOPMENT mode (next dev)"
    npm run dev
fi