#!/bin/bash
ssh -i ~/.ssh/id_ed25519_aihr -o StrictHostKeyChecking=no root@172.235.216.122 '
cd /opt/aihr

# Check POSTGRES_SSL_MODE - disable for local container
grep "POSTGRES_SSL_MODE" .env.production | grep -v "^#" || echo "POSTGRES_SSL_MODE not set in env"

# Set to disable for local postgres container
if ! grep -q "^POSTGRES_SSL_MODE=" .env.production; then
    echo "POSTGRES_SSL_MODE=disable" >> .env.production
    echo "Added POSTGRES_SSL_MODE=disable"
fi

# Build and start all services
echo "Building images (this may take 5-10 minutes)..."
docker compose -f docker-compose.prod.yml --env-file .env.production build web frontend admin-api admin-frontend 2>&1 | tail -10
echo "BUILD_DONE"
'
