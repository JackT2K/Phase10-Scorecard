#!/usr/bin/env bash
set -euo pipefail
[ "$EUID" -eq 0 ] || { echo "Run: sudo ./install.sh"; exit 1; }
apt-get update
apt-get install -y ca-certificates curl openssl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${UBUNTU_CODENAME:-$VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
if [ ! -f .env ]; then
 cp .env.example .env
 sed -i "s/replace-me/$(openssl rand -hex 32)/" .env
 PIN=$(openssl rand -hex 3); sed -i "s/change-me/$PIN/" .env
 echo "Household PIN: $PIN"
fi
docker compose up -d --build
echo "P10 is running at http://SERVER-IP:$(sed -n 's/^P10_PORT=//p' .env)"
