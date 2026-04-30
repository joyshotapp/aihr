#!/bin/bash
# 驗證帳號分離修復結果
set -e
BASE="http://localhost"

echo "--- 等待服務就緒 ---"
sleep 5

echo ""
echo "--- 測試平台 superuser 登入 ---"
RESP=$(curl -s -X POST "$BASE/api/v1/auth/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=platform%40unihr.internal&password=UniHR-Platform%402026%21")
TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token','FAIL'))")
if [ "$TOKEN" != "FAIL" ] && [ -n "$TOKEN" ]; then
  ME=$(curl -s "$BASE/api/v1/users/me" -H "Authorization: Bearer $TOKEN")
  IS_SU=$(echo "$ME" | python3 -c "import sys,json; print(json.load(sys.stdin).get('is_superuser'))")
  echo "  platform@unihr.internal: 登入 OK, is_superuser=$IS_SU"
else
  echo "  platform@unihr.internal: 登入失敗: $RESP"
fi

echo ""
echo "--- 測試租戶 Owner 登入（應成功，is_superuser=False）---"
RESP2=$(curl -s -X POST "$BASE/api/v1/auth/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=y.c.chen1112%40gmail.com&password=mcWzOEha0w7zKH9u53yG7Q")
TOKEN2=$(echo "$RESP2" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token','FAIL'))")
if [ "$TOKEN2" != "FAIL" ] && [ -n "$TOKEN2" ]; then
  ME2=$(curl -s "$BASE/api/v1/users/me" -H "Authorization: Bearer $TOKEN2")
  IS_SU2=$(echo "$ME2" | python3 -c "import sys,json; print(json.load(sys.stdin).get('is_superuser'))")
  ROLE2=$(echo "$ME2" | python3 -c "import sys,json; print(json.load(sys.stdin).get('role'))")
  echo "  y.c.chen1112@gmail.com: 登入 OK, is_superuser=$IS_SU2, role=$ROLE2"
else
  echo "  y.c.chen1112@gmail.com: 登入失敗: $RESP2"
fi

echo ""
echo "--- 驗證：租戶 owner 存取 /api/v1/users/me（應 OK）---"
if [ -n "$TOKEN2" ]; then
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/v1/users/me" -H "Authorization: Bearer $TOKEN2")
  echo "  GET /users/me: HTTP $CODE (預期 200)"
fi

echo ""
echo "Done."
