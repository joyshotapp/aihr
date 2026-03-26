#!/bin/bash
# ========================================================
# UniHR SaaS ???�署驗�??�本
# ========================================================
# 檢查?�?��??�是?�正常�?�?# ========================================================

set -e

IP="172.237.11.179"
DOMAIN="172-237-11-179.sslip.io"
PROTOCOL="http"  # ?�次?�署使用 HTTP，�?�?SSL 後改??https

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================="
echo "UniHR SaaS - ?�署驗�?"
echo "========================================="
echo ""

# 計數??PASS=0
FAIL=0

# 檢查?�數
check_service() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "檢查 ${name}... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${url}" 2>&1 || echo "000")
    
    if [ "$response" -eq "$expected_code" ]; then
        echo -e "${GREEN}??OK (${response})${NC}"
        ((PASS++))
    else
        echo -e "${RED}??FAIL (${response})${NC}"
        ((FAIL++))
    fi
}

# 1. Docker ?��??�??echo -e "${YELLOW}[1/3] Docker ?��??�??{NC}"
echo "---------------------------------------"
cd /opt/aihr
docker compose -f docker-compose.prod.yml ps
echo ""

# 2. ?�康檢查端�?
echo -e "${YELLOW}[2/3] API ?�康檢查${NC}"
echo "---------------------------------------"
check_service "Backend API Health" "${PROTOCOL}://api.${DOMAIN}/health"
check_service "Backend API Docs" "${PROTOCOL}://api.${DOMAIN}/docs"
echo ""

# 3. ?�端介面
echo -e "${YELLOW}[3/3] ?�端介面${NC}"
echo "---------------------------------------"
check_service "使用?��???(app)" "${PROTOCOL}://app.${DOMAIN}"
check_service "系統?��???(admin)" "${PROTOCOL}://admin.${DOMAIN}"
echo ""

# 4. DNS �??檢查
echo -e "${YELLOW}[額�?] DNS �??檢查${NC}"
echo "---------------------------------------"
for subdomain in app admin api admin-api; do
    echo -n "檢查 ${subdomain}.${DOMAIN}... "
    result=$(dig +short ${subdomain}.${DOMAIN} | tail -n1)
    if [ "$result" = "$IP" ]; then
        echo -e "${GREEN}??${result}${NC}"
    else
        echo -e "${RED}??${result} (?��?: ${IP})${NC}"
    fi
done
echo ""

# 5. 資�?庫�??檢查
echo -e "${YELLOW}[額�?] 資�?庫�??${NC}"
echo "---------------------------------------"
echo -n "PostgreSQL... "
if docker compose -f docker-compose.prod.yml exec -T postgres pg_isready -q; then
    echo -e "${GREEN}??OK${NC}"
else
    echo -e "${RED}??FAIL${NC}"
fi

echo -n "Redis... "
REDIS_PASSWORD=$(grep REDIS_PASSWORD= .env.production | cut -d '=' -f2)
if docker compose -f docker-compose.prod.yml exec -T redis redis-cli -a "$REDIS_PASSWORD" ping | grep -q PONG; then
    echo -e "${GREEN}??OK${NC}"
else
    echo -e "${RED}??FAIL${NC}"
fi
echo ""

# 總�?
echo "========================================="
if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}???�?�檢?�通�?�?${PASS}/${PASS})${NC}"
    echo -e "${GREEN}?�署完全�?���?{NC}"
else
    echo -e "${RED}???��?檢查失�? (${PASS} ?��? / ${FAIL} 失�?)${NC}"
    echo -e "${YELLOW}請檢?��?${NC}"
    echo "  1. docker compose -f docker-compose.prod.yml logs"
    echo "  2. ?�火?�設定�?ufw status�?
    echo "  3. .env.production ?�置?�否�?��"
fi
echo "========================================="
echo ""

# 使用?��?
echo -e "${YELLOW}存�?網�?�?{NC}"
echo "  使用?��??? ${PROTOCOL}://app.${DOMAIN}"
echo "  系統?��??? ${PROTOCOL}://admin.${DOMAIN}"
echo "  API ?�件: ${PROTOCOL}://api.${DOMAIN}/docs"
echo "  �ʱ�����: ${PROTOCOL}://�ʱ�����.${DOMAIN}"
echo ""
echo -e "${YELLOW}?�入資�?�?{NC}"
echo "  超�?管�??? $(grep FIRST_SUPERUSER_EMAIL= .env.production | cut -d '=' -f2)"
echo "  密碼: �?.env.production"
echo ""
echo -e "${YELLOW}�ʱ����� ?�入�?{NC}"
echo "  帳�?: admin"
echo "  密碼: $(grep �ʱ�����_PASSWORD= .env.production | cut -d '=' -f2)"
echo ""
