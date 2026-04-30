#!/bin/bash
BASE="http://localhost"

echo "=== 測試 owner 登入 ==="
RESP=$(curl -s -X POST "$BASE/api/v1/auth/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=y.c.chen1112@gmail.com" \
  --data-urlencode "password=mcWzOEha0w7zKH9u53yG7Q")
echo "Login response: $RESP" | head -c 300

TOKEN=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)
if [ -z "$TOKEN" ]; then
  echo "ERROR: no token"
  exit 1
fi
echo ""
echo "Token: ${TOKEN:0:40}..."

echo ""
echo "=== GET /users/me ==="
ME_RESP=$(curl -sv "$BASE/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN" 2>&1)
echo "$ME_RESP" | grep -E "< HTTP|{|}"

echo ""
echo "=== GET /api/v1/users/me (from nginx) ==="
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN")
echo "HTTP $CODE"
BODY=$(curl -s "$BASE/api/v1/users/me" -H "Authorization: Bearer $TOKEN")
echo "Body: $BODY"
