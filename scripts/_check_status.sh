#!/bin/bash
# 上傳新 migration 檔案 + 執行
wsl scp -i ~/.ssh/id_ed25519_aihr -o StrictHostKeyChecking=no \
  /mnt/c/Users/User/Desktop/aihr/alembic/versions/t13_1_superuser_nullable_tenant.py \
  root@172.235.216.122:/opt/aihr/alembic/versions/t13_1_superuser_nullable_tenant.py

ssh -i ~/.ssh/id_ed25519_aihr -o StrictHostKeyChecking=no root@172.235.216.122 \
  'docker exec -w /code aihr-web-1 alembic upgrade head 2>&1 | tail -15'
