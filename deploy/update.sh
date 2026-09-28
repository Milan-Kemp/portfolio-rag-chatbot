#!/usr/bin/env bash
# Run ON THE SERVER, from anywhere:   bash ~/portfolio-rag-chatbot/deploy/update.sh
#
# Pulls the latest code/content from GitHub, rebuilds the image, embeds only
# new or changed content (cached, so it costs almost nothing) into the
# persistent volume, and restarts the containers.
set -euo pipefail

cd "$(dirname "$0")/.."

git pull --ff-only
docker compose build
docker compose run --rm api python ingest.py
docker compose up -d
docker compose ps
