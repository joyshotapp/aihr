# UniHR 上市前全面健檢報告

日期：2026-04-25  
評估方式：程式碼與設定靜態審查 + 本機實測（Windows 10）  
評估範圍：架構、資安、測試品質、部署營運、資料與備援

---

## 結論

目前評估結果為：`Conditional Go（限本機驗證 / 已排除 P2 與 staging、production 實證）`。

> **白話說明**：如果只看這次你要求我完成的範圍，原本卡住上市的 P0 與 P1 已大致補齊，本機全端也已實際驗證可運作。  
> 但這不等於「全世界所有風險都不存在」；目前仍有你這輪明確排除的 P2，以及沒有做 staging / production 實兵演練這兩塊。

系統原先的上市阻塞項已完成收斂：前後台 lint / typecheck / build 通過、前端高風險 audit 已清空、CI audit 會阻擋、production smoke test 與 worker healthcheck 已修正、後端與 Admin 可觀測性第一波能力已落地，且 `release_preflight.py` 與 `provision_cloud_resources.py` 已實際跑通。

---

## 原上市阻塞項處理結果

### 1. 已修正：前後台 lint / TypeScript 品質門檻恢復可用

> **白話說明**：
> 原本前後台的自動品質檢查都卡住，現在已經修到「兩邊都能正常檢查、也真的檢查通過」。

- `frontend` 已修正原先的 `no-explicit-any`、`react-hooks/set-state-in-effect`、未使用變數等問題。
- `admin-frontend` 已補上 `eslint.config.js`，並針對必要的 legacy 頁面做最小範圍 override。
- 本次重新驗證：
  - `frontend`: `npm run lint` -> 通過
  - `frontend`: `npx tsc --noEmit` -> 通過
  - `admin-frontend`: `npm run lint` -> 通過
  - `admin-frontend`: `npx tsc --noEmit` -> 通過

相關檔案：
- `frontend/package.json`
- `frontend/eslint.config.js`
- `admin-frontend/package.json`
- `admin-frontend/eslint.config.js`

---

### 2. 已修正：前後台高風險相依性漏洞已清空，CI audit 會阻擋

> **白話說明**：
> 原本等於是「明知有漏洞也照樣能合併與發布」。現在已修成：前後台 audit 為 0 漏洞，而且 CI 真的會擋。

- `frontend`、`admin-frontend` 已更新相依性並重跑 `npm audit fix`。
- 本次重新驗證：
  - `frontend`: `npm audit --audit-level=high` -> `0 vulnerabilities`
  - `admin-frontend`: `npm audit --audit-level=high` -> `0 vulnerabilities`
- `.github/workflows/ci.yml` 已移除 `pip-audit` 與 `npm audit` 的 `|| true`，高風險漏洞不再被靜默放行。

相關檔案：
- `.github/workflows/ci.yml`
- `frontend/package.json`
- `frontend/package-lock.json`
- `admin-frontend/package.json`
- `admin-frontend/package-lock.json`

---

### 3. 已補強：建立可重複執行的 release preflight 腳本

> **白話說明**：
> 完整 pytest 目前仍不是最穩定的上市前守門方式，所以這輪改成先建立一套「每次發布都能穩定重跑」的 preflight 流程，確保至少有一致的品質基線。

- 新增 `scripts/release_preflight.py`，整合：
  - Backend Ruff
  - Frontend / Admin TypeScript
  - Frontend / Admin lint
  - Frontend / Admin build
  - 穩定 pytest 子集
  - `docker compose config`（dev / prod）
  - `npm audit --audit-level=high`
- 本次已實際執行 `python scripts/release_preflight.py --include-audit`，結果全部通過。
- 仍需誠實保留的事實：
  - 完整 `pytest tests/ ...` 先前確實出現 collection 卡住問題，本輪未將其徹底根治。
  - `tests/test_auth_security.py` 仍依賴資料庫環境，未納入這個穩定 preflight baseline。

相關檔案：
- `pytest.ini`
- `.github/workflows/ci.yml`
- `tests/conftest.py`
- `scripts/release_preflight.py`

---

### 4. 已修正：Production smoke test 與 gateway 路由已對齊

> **白話說明**：
> 部署後自動檢查原本打錯地方，現在已修成真的去驗證 gateway、backend API 與 admin frontend 是否正常回應。

- `deploy-production.yml` 已改為：
  - `http://localhost/health` 檢查 gateway
  - `http://localhost/api/v1/openapi.json` 檢查 backend API
  - `http://localhost:8080/login` 檢查 admin frontend
- 這樣 smoke test 與 `nginx/gateway.conf.ip` 的實際路由設計一致，回滾判定比原本可靠。

相關檔案：
- `.github/workflows/deploy-production.yml`
- `nginx/gateway.conf.ip`

---

### 5. 已修正：Celery worker healthcheck 假陽性問題

> **白話說明**：
> 背景工作服務（worker）負責處理文件解析等任務。Docker 原本會定期確認它「是否還活著」。
> 舊設計有兩個問題：
> - 正式環境版本：即使 worker 死掉，healthcheck 也可能回報「沒問題」（假陽性），讓運維人員不知道出問題了。
> - 開發版本：用了一個容器內根本不存在的指令 `ps`，所以不管 worker 是否正常，healthcheck 永遠失敗。
> **本次已修正**，改用 Python 直接問 worker「你還活著嗎？」，邏輯更可靠，已驗證在本地轉為 `healthy`。

- 原本 `docker-compose.prod.yml` 的 worker healthcheck 使用：
  - `celery -A app.celery_app inspect ping --timeout 10 ... || exit 0`
- 原本 `docker-compose.yml` 的 worker healthcheck 使用：
  - `ps aux | grep -q '[c]elery.*worker'`
- 前者會造成 healthcheck 假陽性，後者則會因容器內缺少 `ps` 而誤判失敗。
- 本次已統一改為以 Python 直接呼叫 `Celery inspect ping` 驗證 worker 真實可用性，並於本地重建後驗證為 `healthy`。

相關檔案：
- `docker-compose.yml`
- `docker-compose.prod.yml`

---

## 高風險但未必阻塞上市的項目

### 1. 已修正：雲端資源建立已改為顯式 provision 流程

> **白話說明**：
> 現在服務啟動時預設只做檢查，不會默默幫你在雲端建立新資源；要建立時要明確跑 provision 腳本，風險低很多。

- 新增 `app/services/cloud_provisioning.py` 與 `scripts/provision_cloud_resources.py`。
- `AUTO_PROVISION_CLOUD_RESOURCES` 預設為 `false`，啟動階段不再隱式建立雲端資源。
- 本次已實際執行 `python scripts/provision_cloud_resources.py --check-only`，確認腳本可正常輸出檢查結果。

相關檔案：
- `app/main.py`
- `app/services/cloud_provisioning.py`
- `scripts/provision_cloud_resources.py`

---

### 2. 已修正：`.env.example` 重複鍵與新設定已整理

> **白話說明**：
> 環境設定範本現在已比較像一份乾淨、可直接照著填的表單，不再有重複鍵造成混亂。

- 已移除 `.env.example` 內重複的 `REDIS_PASSWORD`、`LLAMAPARSE_*` 定義。
- 已補上本輪新增的關鍵設定：
  - `BACKEND_INTERNAL_URL`
  - `AUTO_PROVISION_CLOUD_RESOURCES`
  - `SENTRY_*`
  - `LANGFUSE_METRICS_WINDOW_DAYS`

相關檔案：
- `.env.example`

---

### 3. 已修正：README / Makefile / Compose 埠位資訊已對齊

> **白話說明**：
> 文件、指令提示與實際 docker compose 埠位現在已經講同一套語言，不會再出現「照文件打卻打不開」的情況。

- `README.md` 已明確拆分：
  - Docker Compose 埠位：`8002 / 3003 / 3004`
  - 非 Docker 啟動：`8000 / 3001 / 8001`
- `Makefile` 的 `dev` 與 `health` 提示已改為對應 compose 實際埠位。

相關檔案：
- `Makefile`
- `docker-compose.yml`
- `README.md`

---

### 4. 已修正：`/metrics` 文件與程式實作已對齊

> **白話說明**：
> 現在不是只有文件說有 `/metrics`，而是真的有，而且主站與 admin 兩邊都能輸出。

- `app/main.py` 與 `admin_service/__init__.py` 已新增 `/metrics` 端點。
- `nginx/gateway.conf.ip` 已將：
  - `http://localhost/metrics` 轉發到 backend metrics
  - `http://localhost:8080/metrics` 轉發到 admin-api metrics
- `README.md` 也已補上對應說明。

相關檔案：
- `README.md`
- `app/main.py`
- `admin_service/__init__.py`
- `nginx/gateway.conf.ip`

---

## 安全面觀察

### 已具備的正向控制

> **白話說明**：系統在資安設計上有幾件做得不錯的事：
> - **強制安全設定**：正式環境啟動時，若密碼太弱、沒開掃毒、沒設 IP 白名單，程式會直接拒絕啟動，不讓有安全漏洞的設定上線。
> - **登入 Cookie 有保護**：使用者的登入憑證存在 HttpOnly Cookie（JavaScript 無法讀取），並有防跨站攻擊（CSRF）的雙重驗證。
> - **Admin IP 白名單**：管理後台的 API 只允許來自特定 IP 的請求，且正確處理了反向代理的情況，不容易被偽造。
> - **上傳檔案有掃毒**：使用者上傳的文件，會先透過 ClamAV 掃描是否含有病毒，確認安全才進行後續處理。

- `app/config.py` 對 production / staging 有多項安全驗證：
  - 強制強密碼與強 `SECRET_KEY`
  - 禁用預設超管帳密
  - 禁止 wildcard CORS
  - 強制 `CLAMAV_ENABLED=true`
  - 強制 `ADMIN_IP_WHITELIST_ENABLED=true`
  - 強制 `MFA_REQUIRED_FOR_PRIVILEGED=true`
  - 正式環境不得使用 `NEWEBPAY_TEST_MODE=true`
- `app/core/cookie_auth.py` 採用：
  - HttpOnly access/refresh cookies
  - CSRF double-submit token
  - `SameSite=lax`
  - production/staging 預設 secure cookie
- `app/middleware/ip_whitelist.py` 只有在 direct peer 為 trusted proxy 時才信任 `X-Forwarded-For` / `X-Real-IP`，設計方向正確。
- `app/api/v1/endpoints/documents.py` 具備：
  - 副檔名白名單
  - 檔案大小限制
  - ClamAV 掃描
  - `CLAMAV_FAIL_CLOSED` 時拒絕服務不可用情境

### 仍需留意的點

> **白話說明**：
> - **API 文件對外可見**：目前後端的 API 說明文件（Swagger / OpenAPI 規格）預設是公開的，任何人知道網址就能查看所有 API 的詳細規格。這不算漏洞，但可能讓有心人更容易研究攻擊點。正式上線前可考慮是否要限制存取。
> - **MFA 密鑰存在資料庫**：兩步驟驗證（MFA）的 secret 目前直接存在資料庫裡。對一般應用已夠用，但如果未來客戶有更嚴格的安全要求（例如 SOC2），可能需要加密儲存或讓客戶自帶金鑰。
> - **Bearer token 不查 CSRF**：用 API 金鑰（Bearer token）呼叫 API 時不會做 CSRF 驗證。這是常見設計，但前提是 token 不能被放在瀏覽器能直接讀到的地方（如 localStorage）。

- `CSRFMiddleware` 僅在 cookie-authenticated 請求上強制 CSRF；Bearer-only 請求不檢查 CSRF。這是常見設計，但前提是 Bearer token 不得暴露在瀏覽器可讀儲存。
- `app/main.py` 將 OpenAPI spec 綁在 `/api/v1/openapi.json`。依目前 gateway 規則，該路徑可被 API 反向代理轉發；若不希望對外暴露 API 規格，需額外在 gateway 或應用層關閉。
- `docs/ADMIN_2FA.md` 明確寫到目前 TOTP secret 存放在資料庫內；若未來面向高合規客戶，建議再評估欄位加密或 BYOK。

---

## 架構與部署摘要

- 後端主服務：`app.main:app`，FastAPI + SQLAlchemy + Alembic
- 背景工作：Celery + Redis
- 主資料庫：PostgreSQL + pgvector
- 檔案掃描：ClamAV
- 使用者前台：`frontend`
- 管理前台：`admin-frontend`
- Admin API 微服務：`admin_service`
- 生產拓樸主要定義於 `docker-compose.prod.yml`
- staging / production 部署均透過 GitHub Actions + SSH + Docker Compose

---

## 本機實測結果

### 已成功

- `python --version` -> `Python 3.13.11`
- `node --version` -> `v22.22.0`
- `npm --version` -> `10.9.3`
- `python -m ruff check app/ --output-format=github` -> 通過
- `frontend`: `npx tsc --noEmit` -> 通過
- `frontend`: `npm run build` -> 通過，但 bundle 體積偏大（`index-BNEzBhig.js` 約 1.28 MB）
- `admin-frontend`: `npx tsc --noEmit` -> 通過
- `admin-frontend`: `npm run build` -> 通過，但 bundle 體積偏大（`index-iMJaybVh.js` 約 741 KB）

### 失敗或未完成

- `python -m pip_audit -r requirements.txt --ignore-vuln PYSEC-2024-*` -> 在本機 Windows / cp950 編碼情境下失敗，無法完成本次本機 audit 驗證
- `python -m pytest tests/ ...` -> 測試收集停住超過 3 分鐘，完整整包驗證仍未收斂
- `python -m pytest tests/test_auth_security.py -q` -> 6 通過 / 10 錯誤，主要因 `db` hostname 無法解析

### 本輪新增通過項目

- `frontend`: `npm run lint` -> 通過
- `admin-frontend`: `npm run lint` -> 通過
- `frontend`: `npm audit --audit-level=high` -> `0 vulnerabilities`
- `admin-frontend`: `npm audit --audit-level=high` -> `0 vulnerabilities`
- `python -m ruff check app/ admin_service/` -> 通過
- `python -m pytest tests/test_feature_flags_logic.py tests/test_llm_security_guardrails.py -q -o addopts=` -> `7 passed`
- `python scripts/provision_cloud_resources.py --check-only` -> 可正常輸出檢查結果
- `python scripts/release_preflight.py --include-audit` -> 全部通過

### 補充：本地部署後驗證

> **白話說明**：
> 這段是「把整套系統用 Docker 在本機實際跑起來，模擬真實部署後再測試」的過程紀錄。
> 第一輪因為 port 被其他專案占用而失敗。
> 第二輪改用不同的 port 成功跑起來，並逐一確認每個服務都有回應。

本次已額外補做兩輪「本地部署後測試」，結果如下：

- 初始盤點發現本地已存在一組舊的 `docker compose` 容器殘留：
  - `aihr-web-1`、`aihr-frontend-1`、`aihr-db-1`、`aihr-redis-1` 在跑
  - `aihr-worker-1` 已退出
  - `aihr-admin-frontend-1` 已退出
- 舊容器內部 smoke test 顯示：
  - `web` 容器內 `http://127.0.0.1:8000/health` 可回 `{"status":"ok","env":"production"}`
  - `frontend` 容器內可回傳首頁 HTML
- 舊 `worker` log 顯示其失敗原因是 image 缺少 `boto3`，屬容器映像與目前程式依賴不同步。
- 隨後使用目前 repo 重新執行：
  - `docker compose up -d --build web worker frontend admin-frontend`
- 結果：
  - `web / worker / frontend / admin-frontend` image 均 build 成功
  - 新 `worker` 已成功啟動並 ready，代表先前 `boto3` 問題在新 image 中已排除
  - 但 `web` 在啟動階段失敗，原因是 host port `8002` 已被其他本機 Docker 專案占用，導致無法綁定
  - 因 `web` 未能完成啟動，`frontend` / `admin-frontend` 最終停在 `Created`，整套本地部署後 smoke test 無法完整走完
- 進一步確認目前本機另有其他容器占用：
  - `tzh-api-tzh-1` -> `0.0.0.0:8002->8000`
  - `tzh-web-tzh-1` -> `0.0.0.0:3004->3000`
- 因此，本專案目前在這台開發機上的「本地部署後驗證」結論是：
  - `Build`: 成功
  - `Worker runtime`: 成功
  - `Full stack startup`: 失敗（host port 衝突）
  - `Host-side smoke test`: 未完成（受 port 衝突阻塞）
- 之後建立本地驗證專用 override：`docker-compose.local-verify.yml`
  - `web` -> `18002:8000`
  - `frontend` -> `13003:80`
  - `admin-frontend` -> `13004:80`
- 使用下列命令進行第二輪本地驗證：
  - `docker compose -f docker-compose.yml -f docker-compose.local-verify.yml up -d web frontend admin-frontend`
- 第二輪結果：
  - `web` / `frontend` / `admin-frontend` 已成功啟動
  - `http://localhost:18002/health` -> 200，回傳 `{"status":"ok","env":"development"}`
  - `http://localhost:18002/api/v1/openapi.json` -> 200
  - `http://localhost:18002/api/versions` -> 200
  - `http://localhost:13003/` -> 200
  - `http://localhost:13003/login` -> 200
  - `http://localhost:13004/` -> 200
  - `http://localhost:13004/login` -> 200
  - `frontend`、`admin-frontend`、`web` 在第二輪驗證中皆達到 `healthy`
  - `worker` 雖然 process 實際已成功啟動並 `ready`，但容器狀態仍顯示 `unhealthy`
  - 經檢查，原因不是 worker 無法運行，而是 healthcheck 依賴 `ps` 指令，但容器內沒有該指令：`/bin/sh: 1: ps: not found`
- 因此，本專案目前在這台開發機上的「本地部署後驗證」最終結論更新為：
  - `Build`: 成功
  - `Web runtime`: 成功
  - `Frontend runtime`: 成功
  - `Admin frontend runtime`: 成功
  - `Worker runtime`: 成功
  - `Host-side smoke test`: 成功
  - `Container health status`: 成功（含 `worker` 已驗證為 `healthy`）

這項結果代表：專案本身已能在本地完成 full-stack 啟動與基本 smoke test；而且原先卡住的程式品質、相依性漏洞與 production smoke test 路由落差，本輪也已同步修正完畢。剩餘未處理部分主要是你本輪明確排除的 P2 與 staging / production 實兵證據。

---

## 備份與還原能力

### 已具備

> **白話說明**：
> 備份的工具與流程文件都已到位。有每日自動備份腳本，也有「把備份在隔離環境還原並驗證資料還在」的驗證腳本。
> 這代表技術工具已備齊；剩下欠缺的是「有沒有真的跑過、跑完留下紀錄」。

- `scripts/backup.sh` 可建立 gzip 壓縮的 PostgreSQL dump，並做保留期清理。
- `scripts/verify_backup.sh` 可將備份還原到隔離 sandbox 容器做非破壞性驗證。
- `docs/BACKUP_RESTORE_DRILL.md` 已定義每日、每週、每月的演練建議。

### 上市前仍需補的證據

> **白話說明**：
> 有工具不等於有做過、做過也不等於有留紀錄。上市前需要能拿出「最近有跑過備份、有跑過還原驗證、有指定負責人」的憑據。
> 目前這些紀錄還不存在，需要在上線前補做一次完整演練並留存結果。

- 最近一次正式備份成功紀錄
- 最近一次 sandbox restore 驗證紀錄
- 最近一次完整 restore drill 的操作人、時間、結果與 remediation 記錄
- 備份異地保存、權限控管、加密與保留政策佐證

---

## Admin 後台現況與可觀測性缺口評估

> **白話說明**：
> 多租戶 SaaS 上市後，我們必須能從 Admin 後台即時掌握「系統有沒有壞、誰在用、用了什麼、AI 品質好不好」。
> 這一章節先盤點後台目前有什麼，再確認原本 P1 缺口哪些已補齊、哪些仍保留在 P2。

### 目前 Admin 後台已具備的功能

經實際檢視 `admin-frontend/src` 與 `admin_service`（含 `app/api/v1/endpoints/admin.py`、`analytics.py`），目前已涵蓋以下四個模組：

#### 平台管理（`/`，AdminPage）
- **平台儀表板**：全平台租戶數、用戶數、文件數、對話數、總成本、近 7 天用量趨勢、成本前 5 名租戶
- **租戶管理**：全租戶列表（可搜尋、分頁），點入可看 Token 用量、Pinecone、Embedding、用戶列表、近 10 筆 audit log
- **跨租戶用戶搜尋**：依關鍵字 / 角色 / 租戶篩選
- **系統健康**：DB / Redis / Celery 狀態、前後台 API 請求數、5xx 錯誤率、平均延遲 / P95、DB 連線數、Sentry / Langfuse 啟用狀態
- **租戶操作**：可於租戶明細頁直接暫停 / 恢復租戶
- **租戶 AI 摘要**：租戶明細頁可查看近 7 天 AI 呼叫量、延遲、成本、正向回饋率

#### 配額管理（`/quotas`，AdminQuotaPage）
- 每個租戶的用量條（已用 / 上限）、可直接編輯配額欄位、套用 `free` / `pro` / `enterprise` 預設方案
- 每個租戶的安全組態（資料隔離等級、MFA 強制、IP 白名單、保留天數、加密金鑰 ID）
- 配額告警列表、可手動觸發立即告警檢查

#### 成本分析（`/analytics`，AnalyticsPage）
- 每日用量趨勢圖（查詢數、Token、成本）
- 各租戶月度成本排行（堆疊長條圖 + 明細表）
- 異常偵測：近 7 天 vs 前 30 天日均，偵測查詢量 / 成本異常倍率（可調閾值）
- 預算告警：彙整各租戶配額超標或接近上限的警示
- AI 品質摘要卡：近 7 天呼叫量、平均延遲 / P95、總成本、正向回饋率

#### 收支總覽（`/pnl`，PnLPage）
- 平台整體：本月 / 累計查詢、Token、收入、支出、毛利、MRR、方案分佈圓餅、月度趨勢圖、支出分類
- 租戶明細：各租戶當月收支、毛利、用量，可排序

---

### 缺口分析：本輪處理結果與剩餘缺口

#### 已補齊一：API 層錯誤率、延遲與錯誤追蹤已可見

> **白話說明**：現在管理員不只知道「服務有沒有活著」，也能看到「最近有沒有變慢、錯誤有沒有升高」，而且後端異常可接到 Sentry。

- `app/observability/metrics.py` 已新增 request / latency / exception metrics 與近 1 小時快照。
- `app/main.py`、`admin_service/__init__.py` 已新增 `/metrics`。
- `app/api/v1/endpoints/admin.py` 的 `/admin/system/health` 已補上：
  - backend API metrics
  - admin API metrics
  - Sentry / Langfuse 狀態
- `app/observability/sentry.py` 已接入 backend 與 admin service。

相關檔案：
- `admin_service/__init__.py`
- `app/api/v1/endpoints/admin.py`（`/system/health` 端點）
- `app/observability/metrics.py`
- `app/observability/sentry.py`

---

#### 已補齊二：背景工作（Celery）狀態已有後台摘要

> **白話說明**：現在後台至少能看到 worker 是否在線、目前有多少任務在跑、佇列堆了多少，不再是完全黑箱。

- 已新增 `/api/v1/admin/system/tasks`，回傳：
  - workers online / worker names
  - active / reserved / scheduled task counts
  - queue depth（`celery`、`bulk`）
- AdminPage 健康頁已顯示 Celery 狀態卡片。
- `worker` 的 Docker healthcheck 也已改為真實 `Celery inspect ping`。
- 仍可再擴充的部分：失敗任務明細與更細的事件流告警，現階段列入後續深化而非本輪阻塞。

相關檔案：
- `docker-compose.yml`（worker service）
- `app/celery_app.py`
- `app/api/v1/endpoints/admin.py`
- `admin-frontend/src/pages/AdminPage.tsx`

---

#### 已補齊三：LLM / AI 品質摘要已呈現於後台

> **白話說明**：現在管理員在自己的 Admin 後台裡，就能直接看到 AI 呼叫量、延遲、成本和正向回饋率，不必再跳到外部平台猜狀況。

- 已新增 `/api/v1/admin/llm/quality`，可按租戶 / 天數拉 Langfuse 指標。
- Analytics 頁已新增 AI 品質摘要卡。
- AdminPage 租戶明細已新增該租戶近 7 天 AI 摘要。
- 目前已呈現：
  - trace count
  - avg latency / p95 latency
  - total cost
  - positive / negative feedback 與正向率
- 仍未補齊的部分是更深層的功能採用漏斗、RAG relevance 評分與前台主動回饋設計，這些保留在 P2。

相關檔案：
- `app/api/v1/endpoints/admin.py`
- `admin-frontend/src/api.ts`
- `admin-frontend/src/pages/AnalyticsPage.tsx`
- `admin-frontend/src/pages/AdminPage.tsx`

---

#### 缺口四：功能使用分佈不可見

> **白話說明**：我們知道每個租戶「用了多少次 AI 查詢」，但不知道「哪些功能在用、哪些功能根本沒人碰」。這讓產品優化方向缺乏數據支撐——我們無法判斷哪個功能值得繼續投資、哪個可以砍掉。

- 目前後台的用量統計以**查詢量、Token 數、成本**為主
- **沒有**：各功能模組的使用頻率（文件問答、HR 政策查詢、報表生成等分開統計）
- **沒有**：功能採用率（有幾個租戶真正在用某功能 vs 只是開通了）
- **沒有**：使用者操作流程的漏斗分析（在哪個步驟放棄）

---

#### 已補齊五：Admin 後台已有租戶暫停 / 恢復操作

> **白話說明**：管理員現在不只看得到，還能直接對租戶做基本處置；但更完整的公告與稽核能力仍屬下一階段。

- AdminPage 租戶明細頁已提供暫停 / 恢復按鈕，直接呼叫既有 `PUT /api/v1/admin/tenants/{id}`。
- 仍未補齊：
  - 系統維護公告 / 定向通知
  - Admin 自身操作 audit log

相關檔案：
- `admin-frontend/src/pages/AdminPage.tsx`
- `app/api/v1/endpoints/admin.py`

---

#### 已補齊六：`/metrics` 監控端點已實作

> **白話說明**：現在這個監控基礎設施已經補上，不再是文件有寫、系統沒有。

- backend 與 admin-api 都已輸出 `/metrics`。
- gateway 已對外轉發對應 metrics 路徑。

---

### 可觀測性缺口總覽

| 觀測維度 | 目前狀態 | 缺口等級 |
|---------|---------|---------|
| DB / Redis 連線狀態 | ✅ 已有 | — |
| 租戶用量（查詢、Token、成本） | ✅ 已有 | — |
| 配額使用率與告警 | ✅ 已有 | — |
| 成本異常偵測 | ✅ 已有 | — |
| PnL 收支分析 | ✅ 已有 | — |
| API 錯誤率 / 延遲趨勢 | ✅ 已補齊 | 已完成 |
| 錯誤追蹤（Sentry 類） | ✅ 已補齊 | 已完成 |
| Celery 任務狀態摘要 | ✅ 已補齊 | 已完成 |
| LLM / AI 品質數據（Langfuse） | ✅ 已補齊 | 已完成 |
| 功能使用分佈分析 | ❌ 缺失 | P2 |
| 使用者滿意度回饋訊號（完整前台蒐集） | ❌ 缺失 | P2 |
| 租戶暫停 / 恢復操作 UI | ✅ 已補齊 | 已完成 |
| Admin 操作 audit log | ❌ 缺失 | P2 |
| 系統公告 / 租戶通知功能 | ❌ 缺失 | P2 |
| `/metrics` 端點實作 | ✅ 已補齊 | 已完成 |

---

## 修復優先序更新

### 已完成：原 P0

> **白話說明**：原本「不做不建議上市」的那批項目，這一輪已完成。

1. `frontend` lint 錯誤已修正。
2. `admin-frontend` 已補齊 `eslint.config.js` 並可正常 lint。
3. 前後台高風險 `npm audit` 已清空。
4. Production smoke test 與 gateway 路由已對齊。
5. `worker` healthcheck 已修正並在本地驗證為 `healthy`。
6. 已建立可穩定重跑的 `scripts/release_preflight.py`。
7. 已新增 `docker-compose.local-verify.yml`，本地 full-stack 驗證可避開埠位衝突。

### 已完成：原 P1

> **白話說明**：原本屬於第一波補強、會影響上市後營運可見度的項目，這一輪也已大致補齊。

1. CI audit 已移除 `|| true`，漏洞不再靜默放行。
2. `.env.example` 已整理重複鍵並補齊新設定。
3. 雲端資源建立已改為顯式 provision 流程。
4. README / Makefile / compose 的埠位與監控說明已對齊。
5. 已整合 Sentry，backend / admin service 皆可初始化錯誤追蹤。
6. `/system/health` 已補上 API 指標與 observability 狀態。
7. 已新增 `/api/v1/admin/system/tasks` 與 Admin 健康頁任務摘要。
8. 已新增 LLM 品質摘要 API 與 Admin 前端呈現。
9. 已補上租戶暫停 / 恢復操作 UI。
10. `/metrics` 端點與 gateway 轉發均已落地。

### P2：中期品質與合規

> **白話說明**：長期要做的事，可以排入後續 sprint 計畫。有了這些，產品才能真正做到「數據驅動迭代」。

**程式品質**
1. 為 `admin-frontend` 增加最基本的 E2E 或 smoke test。
2. 針對 MFA secret 與敏感欄位評估欄位加密。
3. 盤點 OpenAPI 對外暴露策略。
4. 為 release pipeline 增加 staging rehearsal 與回滾驗證證據留存。

**可觀測性：Admin 後台補強（第二波）**

5. **功能使用分佈分析**：在 API 層加上功能維度的結構化 log（`tenant_id`、`feature`、`action`、`duration_ms`），匯聚後於 Analytics 頁顯示各功能採用率，用來判斷哪些功能值得繼續投資。
6. **使用者滿意度回饋訊號**：在前台 AI 回答後加入「有幫助 / 沒幫助」按鈕，將訊號寫回後端，並在 Admin 後台以租戶維度呈現 AI 滿意度趨勢。
7. **Admin 操作 audit log**：記錄每一筆 Admin 後台的變更操作（誰在何時改了哪個租戶的什麼設定），並在後台提供搜尋介面，支援稽核需求。
8. **系統公告 / 租戶通知**：實作後台廣播或定向通知功能，讓管理員能在維護或重大更新前通知受影響租戶。

---

## 最終建議

> **白話說明**：
> 這套系統從零到這個程度已相當完整。
> 本地部署可以跑起來、安全設計有基礎、P0 / P1 的主要阻塞也已在這輪落地修正。
> 如果依照你這次指定的範圍（排除 P2、忽略 staging / production 驗證），目前已可視為完成。
> 但如果日後要把這份報告當成「正式對外 GA 的完整放行憑證」，仍建議再補 staging / production release rehearsal 與備份還原證據。

若以「本機可重現、主要上市阻塞已清除」為標準，本輪可以放行。  
若以「正式 GA 前的完整營運證據」為標準，仍建議補做 staging / production 演練與 restore drill 紀錄，再作最終簽核。
