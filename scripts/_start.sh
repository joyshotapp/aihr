#!/bin/bash
ssh -i ~/.ssh/id_ed25519_aihr -o StrictHostKeyChecking=no root@172.235.216.122 '
cd /opt/aihr
echo "Recreating containers with updated env..."
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --no-build --force-recreate web admin-api worker 2>&1
echo "UP_DONE"
sleep 8
docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null
'
