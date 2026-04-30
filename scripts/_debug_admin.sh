#!/bin/bash
JAR=/tmp/j_admin_debug
rm -f $JAR
curl -s -o /dev/null -c $JAR -X POST http://localhost/api/v1/auth/login/access-token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'username=platform@unihr.internal' \
  --data-urlencode 'password=UniHR-Platform@2026!'
echo "=== /admin/tenants response ==="
curl -s -b $JAR http://localhost/api/v1/admin/tenants
echo ""
rm -f $JAR
