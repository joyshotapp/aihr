#!/bin/bash
BASE="http://localhost"
test_login() {
  local label="$1" email="$2" password="$3"
  local jar="/tmp/j_$(echo $email | tr -d '@.')"
  rm -f "$jar"
  HTTP=$(curl -s -o /dev/null -w '%{http_code}' -c "$jar" \
    -X POST "$BASE/api/v1/auth/login/access-token" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "username=$email" \
    --data-urlencode "password=$password")
  if [ "$HTTP" -ge 200 ] && [ "$HTTP" -lt 300 ]; then
    ME_CODE=$(curl -s -o /dev/null -w '%{http_code}' -b "$jar" "$BASE/api/v1/users/me")
    ME=$(curl -s -b "$jar" "$BASE/api/v1/users/me")
    INFO=$(echo "$ME" | python3 -c "import sys,json; d=json.load(sys.stdin); print('role='+str(d.get('role','?'))+' su='+str(d.get('is_superuser','?')))" 2>/dev/null)
    echo "  OK [$label] $email -> /me HTTP=$ME_CODE $INFO"
  else
    echo "  FAIL [$label] $email -> HTTP $HTTP"
  fi
  rm -f "$jar"
}
echo "=== 系統方 ==="
test_login "superuser" "y.c.chen1112@gmail.com" "Bravomix0715"
echo ""
echo "=== 客戶端 Demo Tenant ==="
test_login "owner"    "owner@upower.demo"    "UniHR@2026"
test_login "admin"    "admin@upower.demo"    "UniHR@2026"
test_login "hr"       "hr@upower.demo"       "UniHR@2026"
test_login "employee" "employee@upower.demo" "UniHR@2026"
test_login "viewer"   "viewer@upower.demo"   "UniHR@2026"
echo "Done."
