# UniHR 對外營運前全面性審查報告

日期：2026-04-30  
審查目的：評估 UniHR 是否已準備好對外營運、收費、承接企業客戶資料與接受商務 / 資安 / 法務審查。  
審查方式：既有文件盤點、核心程式與部署設定抽查、測試與 CI 設定抽查、前台商業化頁面與法務頁面抽查、release preflight / build / audit / E2E 實測。  
審查範圍：Backend API、Frontend、Admin Frontend、Admin API、Docker / CI / release preflight、資安控制、金流、法遵文件、營運維護文件。

---

## 一、總結論

本次審查結論為：**Conditional Go（有條件對外營運，但不可視為 release ready）**。

UniHR 已經不是早期 prototype。系統具備完整的多租戶 SaaS 骨架、AI 文件問答主流程、角色權限、稽核、配額、金流雛形、CI 品質門檻、資安啟動阻擋器與多份營運文件。從產品工程成熟度來看，已具備進入小範圍 beta / design partner / 受控試營運的條件。

但若目標是「正式公開開賣、承接真實企業內規與員工資料、對外宣稱 production ready」，目前仍不建議直接無條件 Go。主要原因不是功能缺一大塊，而是正式營運所需的證據鏈尚未完整閉環；本輪實測也確認 release preflight 目前仍無法全綠，前端 lint、production compose config、preflight 與本機 Docker Compose 指令相容性仍需修正。

建議採取的營運策略：

1. **可以開始受控試營運**：限制客戶數、限制資料敏感度、人工陪跑、逐案開通。
2. **不建議立即大規模公開收費**：正式開賣前需完成本文 P0 項目。
3. **應建立營運證據包**：每次 release 都保留 preflight、E2E、部署 smoke test、備份還原演練與資安設定檢查輸出。

整體對外營運就緒度：**7.0 / 10**

---

## 二、實測結果補充

本節為 2026-04-30 追加的實測型審查結果。測試是在本機 macOS 環境執行，未連線 staging / production，也未執行真實 NewebPay 付款或完整資料庫整合測試。

### 1. Release preflight 實測結果

執行指令：

```bash
/Users/yuchuchen/Desktop/aihr/.venv/bin/python scripts/release_preflight.py --include-audit
```

初次執行時，本機環境缺少 `ruff`、前端 `node_modules` 與測試依賴，導致 preflight 無法代表產品真實狀態。補齊 Python runtime/test dependencies、frontend dependencies、admin-frontend dependencies 後重跑，結果如下：

| 項目 | 結果 | 說明 |
|---|---|---|
| Backend Ruff | PASS | `app/` lint 通過 |
| Frontend TypeScript | PASS | `tsc --noEmit` 通過 |
| Frontend Lint | FAIL | 6 個 `@typescript-eslint/no-explicit-any` 錯誤 |
| Frontend Build | PASS | 前台 production build 通過 |
| Admin TypeScript | PASS | Admin 前端 typecheck 通過 |
| Admin Lint | PASS | Admin 前端 lint 通過 |
| Admin Build | PASS | Admin 前端 production build 通過 |
| Stable Pytest Subset | PASS | 補齊依賴後 7 passed，但有 274 個 warnings |
| Compose Dev Config | FAIL in preflight | preflight 使用 `docker compose`，但本機應使用 `docker-compose` |
| Compose Prod Config | FAIL in preflight | 同上，且 production config 另需 `.env.production` |
| Frontend Audit | PASS | `npm audit --audit-level=high` 為 0 vulnerabilities |
| Admin Audit | PASS | `npm audit --audit-level=high` 為 0 vulnerabilities |

判定：preflight 目前**不是全綠**，不能作為 release ready 證據。好消息是多數 build / typecheck / audit 已通過；壞消息是前台 lint 與 compose CLI 相容性會阻擋穩定發布流程。

### 2. Frontend lint 實測失敗細節

執行指令：

```bash
npm --prefix frontend run lint
```

結果：FAIL。

錯誤集中在：

- [frontend/src/api.ts](../frontend/src/api.ts)：5 個 `Unexpected any`。
- [frontend/src/pages/SubscriptionPage.tsx](../frontend/src/pages/SubscriptionPage.tsx)：1 個 `Unexpected any`。

這不是功能阻斷 bug，但它代表目前 CI / preflight 若嚴格執行 lint，前台會阻擋 release。

### 3. Backend 穩定測試子集實測結果

執行指令：

```bash
/Users/yuchuchen/Desktop/aihr/.venv/bin/python -m pytest tests/test_feature_flags_logic.py tests/test_llm_security_guardrails.py -q -o addopts=
```

結果：PASS。

- 7 passed。
- 274 warnings。
- 主要 warnings 來自 SQLAlchemy 2.0 deprecation、Pydantic class-based config deprecation、Python 3.14 下 pytest-asyncio / event loop deprecation。

判定：穩定子集可通過，但 warning 量偏高，若未處理，未來 Python / dependency 升級時可能轉為實際失敗。

### 4. Docker Compose config 實測結果

本機容器工具設定顯示：compose CLI 應使用 `docker-compose`，不是 `docker compose`。

執行 dev config：

```bash
docker-compose -f docker-compose.yml config
```

結果：PASS，可成功解析，但出現 `version` 屬性 obsolete warning。

執行 prod config：

```bash
POSTGRES_PASSWORD=preflight-placeholder REDIS_PASSWORD=preflight-placeholder ADMIN_REDIS_PASSWORD=preflight-placeholder docker-compose -f docker-compose.prod.yml config
```

結果：FAIL。

主要原因：

- 缺少正式 `.env.production`（repo 內僅提供 [`.env.production.example`](../.env.production.example)）。
- `ADMIN_SERVICE_TOKEN` 未設定，compose 先以空字串帶入 warning。
- `version` 屬性 obsolete warning。

判定：dev compose 設定可解析；prod compose 在沒有正式 env file 的本機審查環境無法完成 config 驗證。release preflight 腳本也需改為可依本機環境選擇 `docker-compose` 或 `docker compose`。

### 5. Frontend 公開面 E2E 實測結果

先以 dev server 執行公開 E2E 時，結果為 9 passed / 1 failed。失敗項目是測試期待 production build 的 `/assets/index-*` bundle，但 Vite dev server 不會產生這種 asset；因此改以 production preview server 重跑。

執行方式：

```bash
npm --prefix frontend run preview -- --host 127.0.0.1 --port 4173
CI=1 E2E_BASE_URL=http://127.0.0.1:4173 npx --prefix frontend playwright test e2e/auth.spec.ts --project=chromium --reporter=line
```

結果：PASS。

- 10 passed。
- 公開頁、登入 / 註冊、受保護路由導向等基本公開面流程通過。

另外執行：

```bash
FRONTEND_VERIFY_BASE_URL=http://127.0.0.1:4173 npm --prefix frontend run verify:surface -- --dist-dir frontend/dist
```

結果：PASS。

驗證路由包含：`/`、`/pricing`、`/login`、`/signup`、`/welcome`、`/app/documents`、`/usage`。

### 6. 實測後調整判定

本輪實測讓判定更精準：

- 產品 build 能力比單看文件更可信：前台 build、Admin build、typecheck、audit、公部面 E2E 都能通過。
- Release gate 仍不可信：preflight 不能全綠，且 compose 指令與本機環境不相容。
- 前台 lint 是明確可修的 release blocker。
- Production compose 需要正式 `.env.production` 或專用 `.env.production.example` / preflight env 才能被穩定驗證。
- Python 3.14 下 warnings 偏多，短期不阻擋，但應納入技術債。

因此本報告維持 Conditional Go，但把「不可視為 release ready」列為明確限制。

---

## 三、核心優點

### 1. 產品定位清楚，已形成可銷售 SaaS 骨架

UniHR 的產品主軸明確：以台灣勞動法與企業內規為核心，提供多租戶 HR AI 問答、文件知識庫、管理後台與用量控管。這比單純聊天機器人更接近企業 SaaS，可支撐訂閱、權限、稽核與組織管理。

已具備的商業化能力包含：

- 公開首頁、定價頁、登入 / 註冊、使用者工作台與管理後台。
- Free / Pro / Enterprise 方案矩陣。
- 租戶用量、文件數、查詢量、token 與儲存空間限制。
- Owner / Admin / HR / Employee / Viewer 等角色分層。
- 文件上傳、解析、切片、向量化與 AI 問答流程。
- 來源引用、對話歷史、後續追問與回饋機制。

這些能力代表產品已經有可被客戶理解的價值包裝，不只是技術展示。

### 2. 多租戶隔離與權限模型已具備正式產品基礎

系統設計包含 PostgreSQL RLS、tenant context、Pinecone namespace、角色權限與後端依賴注入檢查。這些都是 B2B SaaS 面對企業客戶時不可缺少的底層能力。

正向觀察：

- [app/config.py](../app/config.py) 預設開啟 `RLS_ENFORCEMENT_ENABLED`。
- [app/db/session.py](../app/db/session.py) 具備將 tenant context 注入資料庫 session 的設計。
- [tests/test_tenant_isolation.py](../tests/test_tenant_isolation.py) 與 [tests/test_cross_tenant_pentest.py](../tests/test_cross_tenant_pentest.py) 顯示已有租戶隔離測試意識。
- API 層多處透過 `current_user.tenant_id` 查詢租戶範圍資料。

這是系統最重要的工程資產之一，應持續保護。

### 3. Production 安全阻擋器方向正確

[app/config.py](../app/config.py) 對 production / staging 有多項硬性檢查：

- 禁止弱 `SECRET_KEY`。
- 禁止預設 DB 密碼與預設超級管理員帳密。
- 禁止 wildcard CORS。
- 強制 ClamAV。
- 強制 Admin IP whitelist。
- 強制管理角色 MFA。
- 禁止正式環境使用藍新測試模式。
- 禁止 production 使用 `POSTGRES_SSL_MODE=disable`。

這類「啟動即阻擋」比單純寫在文件裡更可靠，能降低人為錯誤造成的正式環境暴露。

### 4. 認證與瀏覽器安全控制已有成熟設計

README 與程式架構顯示系統已導入：

- HttpOnly access / refresh cookie。
- CSRF double-submit token。
- OAuth / SSO redirect URI 白名單。
- 速率限制。
- 管理角色 MFA 能力。
- Admin API 網路隔離與 IP 白名單。

這些控制都符合企業 SaaS 面對帳號盜用、CSRF、token 竊取與管理面暴露時的基本要求。

### 5. AI 與文件處理能力具有產品差異化

系統不是只把文件丟進一般向量庫，而是已形成相對完整的 RAG pipeline：

- 語意搜尋 + BM25 + RRF 融合。
- Voyage rerank。
- HyDE 查詢擴展。
- 公司政策與勞動法 Core 合併回答。
- Chunk 去重與解析品質評估。
- Pinecone + pgvector fallback 架構。
- LlamaParse 與 native parser 混合策略。

對 HR / 法遵場景而言，這些能力能提升回答可追溯性與命中率，是產品價值的重要來源。

### 6. 稽核、用量與合規意識強

系統已納入：

- 操作日誌。
- 問答紀錄。
- 稽核 hash 與不可竄改設計。
- 7 年留存策略。
- 用量統計與配額。
- 匯出與分析介面。

這對企業採購非常重要，尤其 HR 場景涉及員工資料、內規文件與可能的爭議處理紀錄。

### 7. CI 與 release preflight 已形成品質門檻

[.github/workflows/ci.yml](../.github/workflows/ci.yml) 已包含：

- Backend Ruff lint / format check。
- Backend pytest。
- Frontend TypeScript / lint / build。
- Admin Frontend TypeScript / lint / build。
- Docker build check。
- pip-audit 與 npm audit。

[scripts/release_preflight.py](../scripts/release_preflight.py) 也建立了本地可重複執行的 release baseline，包含 frontend / admin build、lint、audit、compose config 與穩定 pytest 子集。

這代表團隊已經開始把「能不能發布」從人工感覺轉成可重跑的檢查流程。

### 8. 文件量充足，維運主題覆蓋廣

[docs](.) 內已有 API、部署、備份還原、DPA、資料刪除、SOP、多區、SSL、自訂網域、產品概覽、phase report、release checklist 等文件。文件密度高，表示產品不是只靠口頭知識維運。

這是好事，但也帶來一個反向風險：文件版本很多，若沒有定期淘汰與標示有效狀態，會讓 PM、RD、業務、法務與客戶看到不同故事。

---

## 四、主要缺點與風險

### P0-1：正式營運證據鏈不足

目前 repo 有許多「設計上具備」的安全與營運能力，但正式對外營運需要的是「已套用、已驗證、可追溯」的證據。

仍需補齊的證據包含：

- production-like staging 部署驗證紀錄。
- HTTPS / Secure cookie / HSTS / CORS / Admin IP whitelist 實際設定輸出。
- 管理角色 MFA 強制啟用截圖或自動檢查結果。
- DB SSL 模式與備份加密證據。
- ClamAV 實際掃描流程測試。
- 付款成功、失敗、取消、重複 webhook、退款 / 對帳紀錄。
- 備份還原演練結果。
- 事故通報演練與 rollback 演練結果。

風險：若客戶或資安審查要求提供證據，目前可能只能提供程式碼與文件，缺少實際運行紀錄。

### P0-2：Production worker healthcheck 仍疑似有假陽性

[docker-compose.prod.yml](../docker-compose.prod.yml) 的 worker healthcheck 目前仍可見：

```yaml
celery -A app.celery_app inspect ping --timeout 10 2>/dev/null | grep -q OK || exit 0
```

`|| exit 0` 代表即使 `celery inspect ping` 失敗，healthcheck 仍可能回報成功。這與 [docs/PRODUCTION_HEALTHCHECK_2026-04-25.md](PRODUCTION_HEALTHCHECK_2026-04-25.md) 中「已修正假陽性」的敘述不一致。

風險：正式環境文件解析、向量化或背景任務停止時，Docker / 維運監控可能仍判定 worker healthy，導致問題延遲發現。

建議：正式營運前必須移除 `|| exit 0`，改成失敗即 unhealthy，並以實際停止 worker 或斷 Redis 的方式做負向測試。

### P0-3：法務頁面仍缺正式營運主體

[frontend/src/pages/PrivacyPage.tsx](../frontend/src/pages/PrivacyPage.tsx) 與 [frontend/src/pages/TermsPage.tsx](../frontend/src/pages/TermsPage.tsx) 已比先前 placeholder 進步，聯絡信箱改為 `aihr.app` 網域，也包含個資法、子處理者、付款、資料處理與責任限制。

但仍存在正式商業化缺口：

- 隱私權政策寫「UniHR（運營公司名稱依營業登記為準）」，尚未填入正式公司法定名稱。
- 條款未列統一編號、登記地址、正式通知方式、企業合約優先順序。
- DPA 仍偏模板，尚未確認可直接簽署。
- SLA、資安附錄、子處理者異動通知機制尚未形成正式客戶包。

風險：企業客戶法務審查時會卡關，尤其處理員工資料與企業內規文件時，營運主體不能模糊。

### P0-4：金流主線仍有分叉與未完整驗證風險

目前主要付款 API 是 [app/api/v1/endpoints/payment.py](../app/api/v1/endpoints/payment.py)，訂閱升級 API 是 [app/api/v1/endpoints/subscription.py](../app/api/v1/endpoints/subscription.py)。兩者都處理升級語意，但責任邊界不同：

- `/payment/checkout` 建立藍新 MPG 付款資料。
- `/payment/notify` 處理 webhook 並升級租戶方案。
- `/subscription/upgrade` 對非 superuser 回傳導向訂閱頁或聯絡方式，superuser 可直接升級。

這個設計不是不可行，但正式營運前需要更清楚定義：哪個 API 是唯一付款入口、哪個只是內部狀態查詢 / 導流入口。

另有文件仍提及 Stripe，例如 [docs/PRODUCT_OVERVIEW.md](PRODUCT_OVERVIEW.md) 顯示「藍新金流與 Stripe」，但目前正式主線看起來是 NewebPay。文件敘事若不收斂，會造成業務、客服、法務與 RD 對付款能力理解不一致。

風險：付款成功但方案未啟用、重複 webhook 造成重複帳務、客服不知道正式付款入口、客戶看到不支援的付款方式。

### P0-5：公開商業頁仍有對外聯絡 placeholder

[frontend/src/pages/PricingPage.tsx](../frontend/src/pages/PricingPage.tsx) 的 Enterprise CTA 仍使用：

```tsx
href="mailto:sales@example.com"
```

這是對外營運前必須修正的小但明顯缺口。它會直接影響 Enterprise lead 轉換，也會讓客戶覺得產品尚未正式準備好。

建議：改為正式業務信箱，例如 `sales@aihr.app`，並同步確認 [app/config.py](../app/config.py) 的 `BILLING_CONTACT_URL`、前台 CTA、文件與客服信箱一致。

### P1-1：測試覆蓋已進步，但 release gate 還不夠完整

目前測試資產不少：

- [tests/test_auth_security.py](../tests/test_auth_security.py)
- [tests/test_sso_security.py](../tests/test_sso_security.py)
- [tests/test_tenant_isolation.py](../tests/test_tenant_isolation.py)
- [tests/test_cross_tenant_pentest.py](../tests/test_cross_tenant_pentest.py)
- [tests/test_newebpay.py](../tests/test_newebpay.py)
- [frontend/e2e/critical-flows.spec.ts](../frontend/e2e/critical-flows.spec.ts)

但 [frontend/e2e/critical-flows.spec.ts](../frontend/e2e/critical-flows.spec.ts) 中多數登入後測試會在缺少環境變數時 `test.skip`。這適合作為可選 E2E，不適合作為正式 release gate 的唯一證據。

風險：CI 綠燈不代表真實付款、邀請、權限、文件上傳、Email、租戶隔離等路徑在 staging / production 可用。

補充判定：這一項**主要影響發布品質與整體可靠性，不是直接的效能瓶頸**。它本身不太會讓系統變慢，但會增加缺陷帶著上線、並在真實流量或真實租戶場景下才暴露的機率，間接影響穩定性。

建議：建立至少一套 production-like staging E2E，使用固定測試租戶與測試帳號，將以下流程納入硬性 gate：

- 註冊 / 邀請接受。
- 登入 / 登出 / refresh token。
- 忘記密碼與重設密碼。
- 管理角色 MFA。
- 文件上傳、解析成功、可檢索。
- AI 問答含來源引用。
- Owner 升級方案到藍新測試金流。
- Member 無法進入 owner-only 頁面。
- 跨租戶資料不可見。

### P1-2：CI 與 preflight 之間仍有落差

[.github/workflows/ci.yml](../.github/workflows/ci.yml) 會跑完整 backend tests，而 [scripts/release_preflight.py](../scripts/release_preflight.py) 預設只跑穩定 pytest 子集。這種分層可以理解，但需要明確定義：

- 哪一套是 PR gate。
- 哪一套是 release candidate gate。
- 哪一套是部署後 smoke test。
- 哪一套失敗會阻擋上線。

若沒有定義，團隊可能在趕上線時只跑較短的 preflight，卻以為等同完整測試。

### P1-3：文件與現況存在版本漂移

已觀察到的漂移包含：

- [docs/PRODUCTION_HEALTHCHECK_2026-04-25.md](PRODUCTION_HEALTHCHECK_2026-04-25.md) 說 worker healthcheck 已修正，但 [docker-compose.prod.yml](../docker-compose.prod.yml) 仍疑似 fail-open。
- [docs/PRODUCT_OVERVIEW.md](PRODUCT_OVERVIEW.md) 提及 Stripe，但目前主線為 NewebPay。
- 部分較早文件仍有亂碼或過期商業化敘述，例如 [docs/COMMERCIALIZATION_GAP_ANALYSIS.md](COMMERCIALIZATION_GAP_ANALYSIS.md)。
- README 中曾有 live IP / 入口資訊，需確認對外版本是否已移除或改為內部文件。

風險：客戶、投資人、法務、維運或新 RD 看到不同版本，會降低信任，也會導致錯誤操作。

建議：建立文件狀態標籤：`current`、`superseded`、`draft`、`internal-only`、`customer-facing`。

### P1-4：正式部署目前仍偏單機 Compose 架構

[docker-compose.prod.yml](../docker-compose.prod.yml) 已有 web、worker、db、redis、admin-api、admin-redis、frontend、admin-frontend、clamav、gateway，對早期營運足夠。

但若開始承接正式企業資料，需注意：

- PostgreSQL 與 Redis 仍在 Compose 內，需確認備份、監控、磁碟、升級與故障恢復策略。
- Gateway 只暴露 80 / 8080，需搭配外層 TLS / reverse proxy / load balancer 設定證據。
- ClamAV resource limit 與文件上傳尖峰需壓測。
- Celery worker concurrency / memory / task timeout 需依真實文件大小調整。
- 缺少明確的 zero-downtime migration / rollback 流程證據。

風險：小流量可用，但遇到企業大量文件匯入、模型 API 延遲、Redis / worker 異常時，恢復能力可能不足。

### P1-5：AI 正確性與法務風險需要產品化處理

UniHR 處理的是 HR、勞動法與企業內規，AI 回覆錯誤可能造成實際管理決策風險。系統已有 guardrail、來源引用與「非法律意見」條款，方向正確，但正式營運前仍需要：

- 回答信心分數或資料不足提示策略。
- 高風險主題升級人工審核或建議諮詢專業人士。
- 回答引用來源必填與可追溯保存。
- 法規版本與公司內規版本顯示。
- 回答品質抽樣評估流程。
- 客戶 onboarding 時的免責與使用邊界教育。

風險：即使系統技術可用，錯誤建議仍可能造成客訴或法律爭議。

### P2-1：前端法務與公開頁視覺可用，但設計成熟度仍可再提升

前台頁面已能支撐公開使用，但部分頁面仍有強烈模板感，例如法律頁使用大面積卡片式段落、定價頁 FAQ 仍有供應商地區敘述需核對。正式商業化時，建議統一品牌語氣、正式聯絡資訊、產品截圖、信任訊號與客戶導向文案。

### P2-2：營運指標與客戶成功流程需補強

系統已有 usage / analytics 基礎，但對外營運還需要更明確的客戶成功資料：

- Trial 轉付費漏斗。
- 問答成功率 / 無答案率。
- 文件解析失敗率。
- 平均回答延遲。
- 每租戶 token 成本。
- 客戶活躍度與流失預警。
- 支援 ticket 分類與 SLA 達成率。

### 影響分類矩陣

下表將本報告中主要「不 OK」項目，依其對效能、穩定性、發布品質與商業 / 法遵的影響做分類：

| 項目 | 效能影響 | 穩定性影響 | 發布品質影響 | 商業 / 法遵影響 | 說明 |
|---|---|---|---|---|---|
| P0-1 正式營運證據鏈不足 | 低 | 中 | 高 | 高 | 不一定讓系統變慢，但會讓正式上線判定缺少可信證據，也提高部署錯誤未被發現的風險。 |
| P0-2 Worker healthcheck 假陽性 | 低 | 高 | 高 | 中 | 背景任務異常時仍可能被判定 healthy，會直接傷害維運監控與穩定性。 |
| P0-3 法務頁缺正式營運主體 | 低 | 低 | 中 | 高 | 幾乎不影響 runtime，但會卡法務審查、簽約與企業採購。 |
| P0-4 金流主線分叉 / 驗證不足 | 低 | 中 | 高 | 高 | 更偏商業流程穩定性，可能導致付款成功但方案未生效或客服判斷混亂。 |
| P0-5 Pricing CTA placeholder | 低 | 低 | 中 | 高 | 不影響系統執行，但直接影響商機轉換與對外可信度。 |
| P1-1 測試覆蓋不足 / release gate 不完整 | 低 | 中 | 高 | 中 | 主因是缺陷較容易帶著上線，屬於可靠性與發布品質風險，非直接效能問題。 |
| P1-2 CI 與 preflight 落差 | 低 | 中 | 高 | 低 | 會讓團隊誤判哪些檢查真的阻擋上線，屬於 release process 風險。 |
| P1-3 文件與現況漂移 | 低 | 低 | 中 | 高 | 不影響效能，但會造成錯誤操作、誤售與審查信任問題。 |
| P1-4 單機 Compose 正式部署 | 中 | 高 | 中 | 中 | 平時不一定慢，但在高負載、故障恢復、擴展性與韌性上會暴露問題。 |
| P1-5 AI 正確性與法務風險 | 低 | 低 | 中 | 高 | 主要是回答品質、客訴與責任風險，不是基礎設施效能問題。 |
| Frontend lint `any` 問題 | 低 | 低 | 高 | 低 | 幾乎不影響 runtime，但會阻擋 lint gate，屬於工程品質與發布品質問題。 |
| Preflight compose CLI 不相容 | 低 | 低 | 高 | 低 | 不影響線上效能，但會讓 release preflight 失真，削弱發布信心。 |
| Prod compose 缺正式 env 驗證 | 低 | 中 | 高 | 中 | 本身不是效能議題，但會提高錯誤設定帶入正式環境的機率。 |
| Python 3.14 deprecation warnings 偏多 | 低 | 中 | 中 | 低 | 短期多半不影響效能，但在版本升級時可能轉成測試失敗或執行相容性問題。 |

---

## 五、面向評分

| 面向 | 分數 | 說明 |
|---|---:|---|
| 產品功能完整度 | 8.0 / 10 | 多租戶、AI 問答、文件、權限、稽核、方案頁已成形 |
| 後端架構成熟度 | 7.5 / 10 | FastAPI + Celery + RLS + pgvector/Pinecone 架構合理 |
| 多租戶與資安設計 | 7.5 / 10 | 安全阻擋器、RLS、CSRF、MFA、IP whitelist 設計到位，但需正式實證 |
| AI / RAG 能力 | 8.0 / 10 | 混合檢索、rerank、HyDE、fallback 與來源引用具競爭力 |
| 測試與 CI | 6.5 / 10 | build/typecheck/audit/E2E 有通過項，但 preflight 仍不全綠，frontend lint 失敗 |
| 部署與維運 | 6.3 / 10 | dev compose 可解析；prod compose 缺 env 無法本機驗證，healthcheck、TLS、備援證據需補 |
| 金流與商業化 | 6.2 / 10 | NewebPay 主線存在，但端到端驗證與文件一致性需補 |
| 法遵與對外文件 | 6.0 / 10 | 條款與隱私權已有內容，但正式公司資訊與 DPA/SLA 未定稿 |
| 可觀測性與支援 | 6.8 / 10 | metrics / Sentry / Langfuse 能力存在，仍需正式儀表板與告警證據 |

整體：**7.0 / 10**

---

## 六、Go / No-Go 建議

### 可 Go 的範圍

可以進入以下形式的對外營運：

- 受控 beta。
- Design partner 試用。
- 少量客戶人工開通。
- 非高度敏感資料的試營運。
- 有明確免責與人工陪跑的付費 pilot。

條件：

- 客戶資料需可刪除與匯出。
- 每個客戶上線前由內部檢查租戶設定。
- 付款可先採人工確認或小規模藍新測試轉正式。
- 客服與工程保持高接觸度。

### 不建議 Go 的範圍

暫不建議：

- 大規模自助註冊與自助付費。
- 對外宣稱 fully production ready。
- 承接高敏感員工爭議、薪資、醫療、懲戒等資料作為首波客戶場景。
- 未簽 DPA / SLA 即承接大型企業正式資料。
- 未補齊實證即進行資安問卷或投標。

---

## 七、上線前必做清單

### P0：正式開賣前必須完成

1. 修正 [docker-compose.prod.yml](../docker-compose.prod.yml) worker healthcheck，移除 fail-open 行為並做負向測試。
2. 將 [frontend/src/pages/PricingPage.tsx](../frontend/src/pages/PricingPage.tsx) 的 `sales@example.com` 改為正式業務信箱。
3. 修正 frontend lint：移除 [frontend/src/api.ts](../frontend/src/api.ts) 與 [frontend/src/pages/SubscriptionPage.tsx](../frontend/src/pages/SubscriptionPage.tsx) 的 `any` lint violation。
4. 讓 [scripts/release_preflight.py](../scripts/release_preflight.py) 支援本機正確 compose CLI，或改用環境偵測選擇 `docker-compose` / `docker compose`。
5. 補 `.env.production.example` 或 preflight 專用 env，讓 production compose config 可在不暴露 secrets 的情況下驗證。
6. 法務頁補上正式營運公司名稱、統編、地址、通知方式與正式聯絡窗口。
7. 明確定義付款唯一主線，整理 `/payment` 與 `/subscription` 的責任邊界。
8. 補一份 NewebPay 端到端測試紀錄：成功、失敗、重複通知、金額錯誤、方案升級、對帳。
9. 建立 production-like staging 驗證紀錄，包含 HTTPS、Secure cookie、MFA、Admin IP whitelist、DB SSL、ClamAV。
10. 確認 README 與 customer-facing 文件不暴露管理入口、預設帳密、內部 IP 或過期部署資訊。
11. 產出 release candidate 驗收包：preflight、CI、E2E、smoke test、備份還原演練、rollback 演練。

### P1：第一批付費客戶前強烈建議完成

1. 將登入、邀請、重設密碼、文件上傳、AI 問答、付款、RBAC、跨租戶隔離納入 staging E2E gate。
2. 建立文件狀態標籤與過期文件歸檔流程。
3. 建立正式 SLA、DPA、資安白皮書與 Security Questionnaire 回覆包。
4. 建立備份還原 SOP 的實際演練紀錄。
5. 建立事故分級、通報模板與客服處理流程。
6. 建立 AI 回答品質抽樣與高風險回答處理流程。
7. 建立客戶 onboarding checklist，明確說明可上傳與不建議上傳的資料類型。

### P2：營運後一至兩個版本內完成

1. 將 PostgreSQL / Redis 備援策略提升到 managed service 或明確 HA 設計。
2. 建立成本儀表板，追蹤 LLM、embedding、parser、storage 與每租戶毛利。
3. 建立客戶成功儀表板與流失預警。
4. 整理前台品牌與法務頁設計，降低模板感。
5. 補齊管理後台操作手冊與客服 playbook。

---

## 八、營運亮點可對外包裝

在完成 P0 後，可優先對外強調以下賣點：

- 專為台灣 HR 與勞動法情境設計。
- 企業內規 + 勞動法雙來源回答。
- 每家公司獨立租戶與知識庫。
- AI 回答附來源引用，降低黑箱感。
- 文件解析與品質報告。
- 權限、稽核、配額與用量管理。
- 支援 SSO、MFA、Admin IP whitelist 等企業安全需求。
- 支援 DPA、資料刪除與稽核留存流程。

但在完成正式法務與測試證據前，避免使用以下過強字眼：

- 「完全 production ready」
- 「保證法律正確」
- 「零資料外洩風險」
- 「完全取代法務 / HR 專家」
- 「企業級 SLA 已完整落地」

---

## 九、建議的 14 天修復節奏

### Day 1-2：快速修補明顯對外缺口

- 修正 pricing CTA 信箱。
- 修正 worker healthcheck。
- 修正 frontend lint。
- 修正 release preflight compose CLI 偵測。
- 標記過期文件。
- 移除或內部化 live IP / 管理入口 / 預設帳密敘述。

### Day 3-5：金流與法務收斂

- 定義唯一付款主線。
- 補 NewebPay E2E 測試紀錄。
- 法務頁填入正式營運主體。
- DPA / SLA / 子處理者清單定稿。

### Day 6-9：staging 驗證與 release gate

- 建立 production-like staging。
- 啟用 HTTPS、Secure cookie、MFA、Admin IP whitelist、DB SSL。
- 跑 staging critical E2E。
- 保留截圖、log、測試報告。

### Day 10-12：備援與事故演練

- 備份還原演練。
- rollback 演練。
- worker / Redis / DB 異常演練。
- 通知與客服模板演練。

### Day 13-14：營運決策

- 彙整 release candidate evidence pack。
- 召開 Go / No-Go review。
- 決定受控試營運名單與資料使用限制。

---

## 十、最終判定

UniHR 已經具備對外營運的產品雛形與工程基礎，優點明確：定位清楚、多租戶能力完整、AI/RAG 設計有深度、資安控制方向正確，且本輪實測確認前後台 build、typecheck、audit、公開面 E2E 與 frontend surface verification 具備可運作基礎。

目前最大的問題不在「做不出來」，而在「release gate 與正式營運證據還沒有完全收口」。只要補齊 P0，尤其是 frontend lint、preflight compose CLI、production compose env 驗證、worker healthcheck、法務主體與金流 E2E，系統即可從 Conditional Go 提升到 Go for controlled launch；若再完成 P1，才適合更大規模公開收費與企業客戶正式導入。

**建議決策：可啟動受控試營運，但正式公開開賣前必須完成 P0。**