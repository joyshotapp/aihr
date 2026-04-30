#!/bin/bash
ssh -i ~/.ssh/id_ed25519_aihr -o StrictHostKeyChecking=no root@172.235.216.122 'cd /opt/aihr
sed -i "s/172-237-5-254\.sslip\.io/172-235-216-122.sslip.io/g" .env.production
sed -i "s/172\.237\.5\.254/172.235.216.122/g" .env.production
sed -i "s/172-233-67-81\.sslip\.io/172-235-216-122.sslip.io/g" .env.production
sed -i "s/172\.233\.67\.81/172.235.216.122/g" .env.production
echo "--- Updated URLs ---"
grep -E "CORS|FRONTEND_URL|ADMIN_FRONTEND" .env.production | grep -v "^#"
echo "--- APP_ENV ---"
grep "APP_ENV" .env.production | grep -v "^#"'
