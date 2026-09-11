#!/bin/bash
docker buildx build \
  --platform linux/arm64 \
  -f frontend/Dockerfile.prod \
  -t ghcr.io/32000-yakuman/cinema-frontend:latest \
  --cache-to type=local,dest=/tmp/buildx-cache-frontend,mode=max \
  --cache-from type=local,src=/tmp/buildx-cache-frontend \
  --push \
  ./frontend