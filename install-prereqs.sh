#!/usr/bin/env bash
set -euo pipefail
if command -v docker >/dev/null && docker compose version >/dev/null 2>&1; then echo "Docker already installed"; exit 0; fi
if command -v apt-get >/dev/null; then
 sudo apt-get update
 sudo apt-get install -y docker.io docker-compose-v2 curl openssl || true
elif command -v dnf >/dev/null; then
 sudo dnf install -y docker docker-compose curl openssl || true
elif command -v yum >/dev/null; then
 sudo yum install -y docker docker-compose curl openssl || true
else
 echo "Unsupported distribution. Install Docker manually."; exit 1
fi
sudo systemctl enable --now docker || true
