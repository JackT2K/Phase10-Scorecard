#!/usr/bin/env bash
set -euo pipefail
mkdir -p backups
docker compose cp p10:/data/p10.db "backups/p10-$(date +%F-%H%M%S).db"
echo "Backup saved under ./backups"
