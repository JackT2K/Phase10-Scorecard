#!/usr/bin/env bash
set -euo pipefail
STAMP=$(date +%F-%H%M%S)
mkdir -p backups
mkdir -p data
cp data/p10.db backups/p10-$STAMP.db
tar -czf backups/p10-$STAMP-full.tar.gz data .env 2>/dev/null || true
echo "Backup saved to backups/"
