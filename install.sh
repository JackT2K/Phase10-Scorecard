#!/usr/bin/env bash
set -euo pipefail
command -v docker >/dev/null || { echo "Run install-prereqs.sh first"; exit 1; }
mkdir -p data
if [ ! -f .env ]; then
 cp .env.example .env
 SECRET=$(openssl rand -hex 32)
 PIN=$(openssl rand -hex 3)
 sed -i "s/replace-me/$SECRET/" .env
 sed -i "s/change-me/$PIN/" .env
 echo "Household PIN: $PIN"
fi
docker compose up -d --build
echo "P10 started"
