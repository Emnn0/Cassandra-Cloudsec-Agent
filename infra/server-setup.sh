#!/bin/bash
# One-time Hetzner server bootstrap (Ubuntu 22.04)
# Run as root: curl -sL https://raw.githubusercontent.com/your-org/loglens/main/infra/server-setup.sh | bash

set -euo pipefail

echo "=== LogLens Server Bootstrap ==="

# System update
apt-get update -y && apt-get upgrade -y

# Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu

# Docker Compose plugin (v2)
apt-get install -y docker-compose-plugin

# UFW firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp   # HTTP/3
ufw --force enable

# fail2ban
apt-get install -y fail2ban
systemctl enable fail2ban

# App directory
mkdir -p /opt/loglens
chown ubuntu:ubuntu /opt/loglens

# Swap (2 GB)
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# Daily backup cron (2 AM)
echo '0 2 * * * ubuntu cd /opt/loglens && docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip | \
  aws s3 cp - s3://$S3_BACKUP_BUCKET/postgres/loglens_$(date +\%Y\%m\%d_\%H\%M\%S).sql.gz' \
  > /etc/cron.d/loglens-backup

echo "=== Bootstrap complete. Reboot recommended. ==="