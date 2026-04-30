#!/bin/bash
JAR=/tmp/j_platform_guard
rm -f $JAR
curl -s -o /dev/null -c $JAR -X POST http://localhost/api/v1/auth/login/access-token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'username=platform@unihr.internal' \
  --data-urlencode 'password=UniHR-Platform@2026!'

echo '--- platform@unihr.internal guard 測試 ---'
echo -n '/users/me (允許): '
curl -s -o /dev/null -w '%{http_code}' -b $JAR http://localhost/api/v1/users/me
echo ''

echo -n '/admin/tenants (允許): '
curl -s -o /dev/null -w '%{http_code}' -b $JAR http://localhost/api/v1/admin/tenants
echo ''

echo -n '/billing/records (應 403): '
curl -s -o /dev/null -w '%{http_code}' -b $JAR http://localhost/api/v1/billing/records
echo ''

echo -n '/employees (應 403): '
curl -s -o /dev/null -w '%{http_code}' -b $JAR http://localhost/api/v1/employees
echo ''

rm -f $JAR

echo ''
echo '--- y.c.chen1112@gmail.com (純 owner，應可存取租戶端點) ---'
JAR2=/tmp/j_owner_guard
rm -f $JAR2
curl -s -o /dev/null -c $JAR2 -X POST http://localhost/api/v1/auth/login/access-token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'username=y.c.chen1112@gmail.com' \
  --data-urlencode 'password=mcWzOEha0w7zKH9u53yG7Q'

echo -n '/users/me (允許): '
curl -s -o /dev/null -w '%{http_code}' -b $JAR2 http://localhost/api/v1/users/me
echo ''

echo -n '/billing/records (允許): '
curl -s -o /dev/null -w '%{http_code}' -b $JAR2 http://localhost/api/v1/billing/records
echo ''

rm -f $JAR2
echo 'Done.'
