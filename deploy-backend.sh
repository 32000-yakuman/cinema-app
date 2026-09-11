#!/bin/bash
docker buildx build \
  --platform linux/arm64 \
  -f backend/Dockerfile.prod \
  -t ghcr.io/32000-yakuman/cinema-backend:latest \
  --cache-to type=local,dest=/tmp/buildx-cache-backend,mode=max \
  --cache-from type=local,src=/tmp/buildx-cache-backend \
  --push \
  ./backend