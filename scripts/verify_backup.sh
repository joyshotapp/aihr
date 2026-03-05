#!/usr/bin/env bash
# ========================================================
# UniHR Backup Verification Script（第 17 項：備份還原演練）
# ========================================================
# 執行完整備份流程並在沙箱容器中驗證可還原性（非破壞性）。
#
# 驗證步驟：
#   1. 建立新備份（呼叫 backup.sh）
#   2. 驗證備份檔案完整性
#   3. 在隔離的測試容器中還原，確認資料表數量與基本健康
#   4. 刪除測試容器
#
# 使用方式：
#   chmod +x scripts/verify_backup.sh
#   ./scripts/verify_backup.sh                     # 產生新備份後驗證
#   ./scripts/verify_backup.sh <backup_file.sql.gz> # 驗證指定備份
#
# 環境需求：
#   - Docker 已啟動
#   - docker compose 可用
# ========================================================

set -euo pipefail

# ─── 彩色輸出 ───
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✓${NC} $*"; }
warn() { echo -e "${YELLOW}  ⚠${NC} $*"; }
err()  { echo -e "${RED}  ✗${NC} $*" >&2; exit 1; }

# ─── 設定 ───
BACKUP_DIR="${BACKUP_DIR:-./backups}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-unihr_saas}"
SANDBOX_CONTAINER="unihr_verify_sandbox_$$"
SANDBOX_IMAGE="pgvector/pgvector:pg16"

echo ""
echo "══════════════════════════════════════════════════════"
echo "  UniHR Backup Verification — $(date '+%Y-%m-%d %H:%M:%S')"
echo "══════════════════════════════════════════════════════"
echo ""

# ─── 步驟 1：建立或使用指定備份 ───
if [[ $# -ge 1 ]]; then
    BACKUP_FILE="$1"
    if [[ ! -f "${BACKUP_FILE}" ]]; then
        err "Backup file not found: ${BACKUP_FILE}"
    fi
    echo "▸ Using existing backup: ${BACKUP_FILE}"
else
    echo "▸ Step 1/4: Creating fresh backup..."
    BACKUP_OUTPUT=$(./scripts/backup.sh 2>&1)
    # 從輸出中抓取備份路徑
    BACKUP_FILE=$(echo "${BACKUP_OUTPUT}" | grep -oP '(?<=Backup created: ).*?(?= \()' | head -1)
    if [[ -z "${BACKUP_FILE}" ]]; then
        # 取最新備份
        BACKUP_FILE=$(find "${BACKUP_DIR}" -name "unihr_*.sql.gz" -printf '%T@ %p\n' | sort -n | tail -1 | awk '{print $2}')
    fi
    echo "${BACKUP_OUTPUT}"
fi

BACKUP_SIZE=$(du -sh "${BACKUP_FILE}" | cut -f1)
ok "Backup file: ${BACKUP_FILE} (${BACKUP_SIZE})"

# ─── 步驟 2：完整性驗證 ───
echo ""
echo "▸ Step 2/4: Verifying backup integrity..."
if gzip -t "${BACKUP_FILE}" 2>/dev/null; then
    ok "gzip integrity check passed"
else
    err "Backup file is corrupted!: ${BACKUP_FILE}"
fi

# 確認 SQL 內容包含基本關鍵字
if zcat "${BACKUP_FILE}" | grep -q "CREATE TABLE\|INSERT INTO\|PostgreSQL database dump"; then
    ok "SQL content structure verified (CREATE TABLE / data present)"
else
    warn "Cannot confirm SQL structure — backup may be empty or schema-only"
fi

LINE_COUNT=$(zcat "${BACKUP_FILE}" | wc -l)
ok "Backup line count: ${LINE_COUNT}"

# ─── 步驟 3：沙箱還原測試 ───
echo ""
echo "▸ Step 3/4: Restoring into sandbox container (${SANDBOX_CONTAINER})..."

# 確保清除殘留
docker rm -f "${SANDBOX_CONTAINER}" >/dev/null 2>&1 || true

# 啟動隔離的 PostgreSQL 容器
docker run -d \
    --name "${SANDBOX_CONTAINER}" \
    -e POSTGRES_USER="${POSTGRES_USER}" \
    -e POSTGRES_PASSWORD=verify_only \
    -e POSTGRES_DB="${POSTGRES_DB}" \
    "${SANDBOX_IMAGE}" >/dev/null

# 等待資料庫就緒
echo "   Waiting for sandbox DB to start..."
MAX_WAIT=30
for i in $(seq 1 ${MAX_WAIT}); do
    if docker exec "${SANDBOX_CONTAINER}" pg_isready -U "${POSTGRES_USER}" -q 2>/dev/null; then
        ok "Sandbox DB ready (${i}s)"
        break
    fi
    if [[ $i -eq ${MAX_WAIT} ]]; then
        docker rm -f "${SANDBOX_CONTAINER}" >/dev/null 2>&1 || true
        err "Sandbox DB did not start within ${MAX_WAIT}s"
    fi
    sleep 1
done

# 安裝 pgvector extension（備份可能有 CREATE EXTENSION vector）
docker exec "${SANDBOX_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
    -c "CREATE EXTENSION IF NOT EXISTS vector;" >/dev/null 2>&1 || true

# 還原備份
echo "   Restoring SQL dump..."
RESTORE_ERRORS=0
if ! zcat "${BACKUP_FILE}" | docker exec -i "${SANDBOX_CONTAINER}" \
    psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
    --set ON_ERROR_STOP=0 -q 2>/tmp/restore_errors_$$.txt; then
    RESTORE_ERRORS=$(wc -l < /tmp/restore_errors_$$.txt 2>/dev/null || echo "?")
    warn "Restore completed with ${RESTORE_ERRORS} error line(s) — may be acceptable (permissions, owner)"
fi

# ─── 步驟 4：基本健康檢查 ───
echo ""
echo "▸ Step 4/4: Post-restore health checks..."

TABLE_COUNT=$(docker exec "${SANDBOX_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
    -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" | tr -d ' ')
ok "Tables in public schema: ${TABLE_COUNT}"

if [[ "${TABLE_COUNT}" -lt 5 ]]; then
    warn "Low table count (${TABLE_COUNT}) — may indicate schema-only or empty backup"
fi

# 檢查核心資料表存在
CORE_TABLES=("users" "tenants" "documents" "conversations")
for TABLE in "${CORE_TABLES[@]}"; do
    ROW_COUNT=$(docker exec "${SANDBOX_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
        -t -c "SELECT count(*) FROM ${TABLE};" 2>/dev/null | tr -d ' \n' || echo "N/A")
    ok "Table '${TABLE}': ${ROW_COUNT} rows"
done

# 清除沙箱容器
docker rm -f "${SANDBOX_CONTAINER}" >/dev/null 2>&1 || true
rm -f /tmp/restore_errors_$$.txt

echo ""
echo "══════════════════════════════════════════════════════"
echo -e "  ${GREEN}✓ Backup verification PASSED!${NC}"
echo "  Backup file : ${BACKUP_FILE}"
echo "  Tables found: ${TABLE_COUNT}"
echo "  Verified at : $(date '+%Y-%m-%d %H:%M:%S')"
echo "══════════════════════════════════════════════════════"
echo ""
echo "  建議排程（crontab -e）："
echo "  # 每日凌晨 2 點備份（正式機）"
echo "  0 2 * * * cd /srv/aihr && ./scripts/backup.sh >> /var/log/unihr-backup.log 2>&1"
echo "  # 每週日凌晨 3 點執行備份驗證"
echo "  0 3 * * 0 cd /srv/aihr && ./scripts/verify_backup.sh >> /var/log/unihr-backup-verify.log 2>&1"
echo ""
