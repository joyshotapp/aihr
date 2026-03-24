# UniHR 對外 SaaS 生產化升級總整計畫

> 版本：v1.1  
> 日期：2026-03-23  
> 目的：整合目前系統現況，明確列出要升級到可在生產環境對外販售的 SaaS 所需補齊的工作，涵蓋產品、商業化、資安、隱私、資料治理、維運、法務與營運。  
> v1.1 更新：依實際程式碼審查結果，補入原計畫遺漏的 Refresh Token、自動回滾、DB 連線加密、SSO 落地、測試覆蓋率等缺口。

---

## 1. 結論摘要

UniHR 目前已經不是 Demo，也不是只有介面的技術展示，而是一套具備以下基礎能力的多租戶 AI SaaS 原型：

- 多租戶與角色權限
- 文件上傳、解析、切片、向量化、檢索
- Chat/RAG 問答與 SSE 串流
- 稽核日誌、用量追蹤、方案配額
- SSO、自訂域名、管理後台、基礎 CI/CD、監控

但若要升級成「可在生產環境對外販售」的 SaaS，仍有數個 P0 缺口尚未補齊。

核心判斷如下：

1. 目前可支援內部自用、單一租戶自架、少量 Design Partner 或付費 PoC。
2. 目前不建議直接開放自助註冊、自助付費、低接觸式對外販售。
3. 最大缺口不在 AI 功能，而在商業閉環、資安治理、隱私合規、資料處理責任、營運可靠性與客戶支援能力。

一句話總結：

> 這套產品已達「可導入試營運」等級，但尚未達到「可放心公開販售的標準 SaaS」等級。

---

## 2. 目標定義：什麼叫做可以對外 SaaS 販售

本文件定義的目標，不是單純服務能跑起來，而是符合以下條件：

### 2.1 商業面

- 客戶可完成註冊、驗證、邀請、重設密碼、升級與續約
- 可收費、可對帳、可提供帳單與發票
- 有基本條款、隱私權政策、DPA、客服與 Onboarding 機制

### 2.2 技術面

- 多租戶隔離可被驗證，且不能只靠應用層檢查
- 生產環境有可靠部署、監控、告警、備份、還原、回滾
- 故障時可以快速定位、通報、回復

### 2.3 資安與隱私面

- 可清楚描述資料流向、子處理者、資料保存位置與刪除流程
- 能證明存取控制、審計、管理面防護、最小權限與刪除能力
- 企業可合理相信其知識庫與內部資料不會被誤用、外洩或無法刪除

---

## 3. 目前已具備的基礎

### 3.1 產品與工程基礎

- 多租戶資料模型與租戶配額已存在
- Chat / KB / 文件處理 / SSE 已實作
- 方案矩陣與配額管理已存在
- 基本 SSO、自訂域名、前後台已實作
- 壓測腳本、SOP、CI/CD、Prometheus/Grafana 已建立

### 3.2 資安基礎

- 有 PostgreSQL RLS migration 與 rollout plan
- 有 tenant-scoped CRUD 修補與租戶隔離審查成果
- 有不可竄改稽核設計：`content_hash`、`expires_at`、trigger
- 有 Admin API IP whitelist middleware
- Nginx 正式 gateway 已包含 TLS、HSTS、CSP、X-Frame-Options

### 3.3 已存在但尚未完全落地的控制

- RLS 程式已支援，但是否強制生效取決於生產設定
- 管理面白名單能力已存在，但需確認生產環境實際啟用
- 文件刪除已涵蓋 DB / R2 / Pinecone，但尚未形成完整租戶退租資料清除 SOP
- 監控規則已存在，但主動通知尚未接通

---

## 4. 主要缺口總覽

| 工作面向 | 目前狀態 | 對外販售風險 | 優先級 |
|---|---|---|---|
| 支付 / 訂閱閉環 | 只有方案切換，無付款驗證 | 無法自助收費、無訂閱同步 | P0 |
| Email / 帳號生命週期 | 無正式寄信系統，邀請流程非 Email 化 | 無法完成註冊、驗證、重設密碼 | P0 |
| 法務與合規文件 | 缺隱私權政策、條款、DPA | 企業採購 / 法務無法過關 | P0 |
| 隱私與資料治理 | 第三方處理鏈存在，但缺治理包 | 企業不敢上傳知識庫 | P0 |
| RLS 與租戶隔離落地 | 能力已存在，但需生產實證 | 多租戶隔離敘事不完整 | P0 |
| 監控與告警通知 | 監控有，Alertmanager 未接通 | 故障時無主動通知 | P0 |
| 部署可靠性 | deploy workflow 仍有風險點 | 可能部署成功但 schema/功能失敗 | P0 |
| Refresh Token 機制 | JWT 8hr TTL，無 refresh token | 用戶每日被迫重新登入，無法做 token rotation | P0 |
| 部署自動回滾 | health check 失敗只報錯，不回滾 | 部署失敗後服務持續異常，需人工介入 | P0 |
| DB 連線加密 | 未強制 sslmode=require | 多租戶 SaaS 的 DB 傳輸未加密 | P0 |
| SSO Client 設定 | Google/Microsoft client ID 為空值 | SSO 功能無法在生產使用 | P0 |
| 自訂域名 SSL 自動化 | DNS 驗證有，SSL 自動化不足 | 企業白牌與自訂網域交付不完整 | P1 |
| 客服 / Onboarding | 尚未產品化 | 高接觸交付成本過高 | P1 |
| 2FA / 安全治理套件 | 尚未完成 | Enterprise 採購阻力高 | P1 |
| 測試覆蓋率 | CI 無 pytest-cov，覆蓋率未知 | 高風險路徑（payment webhook 等）可能無測試覆蓋 | P1 |
| 前端 E2E 測試 | 無 Playwright/Cypress | 付費關鍵路徑的前端迴歸無自動化驗證 | P1 |
| Secrets 集中管理 | API Key 存於 .env 檔案 | 企業安全問卷常見必問項 | P1 |
| 多區域 / 資料駐留 | 架構有，但未形成真實基礎設施 | 國際與大型客戶受限 | P2 |

---

## 5. 詳細工作清單

## 5.1 商業化閉環

### 必做工作

- ✅ 已整合藍新金流 (NewebPay) MPG 多功能付款閘道
- ✅ 已建立 checkout / webhook / 帳單紀錄流程
- ✅ 訂閱狀態同步到 tenant plan 與 quota
- ✅ 付款失敗會建立 failed 帳單紀錄
- ✅ 帳單歷史、PDF 發票下載
- □ 付款失敗重試通知、取消訂閱降級、續約通知（待補）

### 驗收標準

- 客戶可自行升級、續約、取消
- Webhook 可正確處理付款成功、失敗、取消
- 訂閱狀態與 tenant plan 不會不一致
- 後台可查帳單與付款紀錄

### 建議路徑

- Phase 1：✅ 已完成藍新 MPG 串接（AES-256-CBC 加解密 + SHA256 驗簽 + NotifyURL webhook）
- Phase 2：補上定期定額扣款 API + 取消/降級流程

---

## 5.2 帳號生命週期與交易型 Email

### 必做工作

- 整合 SendGrid / AWS SES / Resend
- Email 驗證流程
- 忘記密碼 / 重設密碼
- 正式 invitation flow：寄邀請信、一次性 token、首次設定密碼
- 使用者停權 / 離職 / 停用 / 回收帳號流程

### 驗收標準

- 新用戶可透過 email 完成啟用
- 忘記密碼可在時效內完成重設
- 管理員邀請用戶時不需直接設定明碼密碼
- 所有 token 皆具時效與一次性

---

## 5.3 隱私、資安與資料治理

這是知識庫 SaaS 最重要的工作流之一。

### 目前風險來源

企業上傳的知識庫內容目前會涉及以下處理鏈：

- R2 物件儲存
- Pinecone 向量資料庫
- Voyage embedding / rerank
- Gemini 回答生成
- LlamaParse 文件解析

因此，真正的問題不只是資料是否存放於本系統資料庫，而是：

- 資料是否跨境
- 第三方是否為子處理者
- 是否會被模型訓練使用
- 是否能在退租或刪除要求時全鏈路刪除
- 是否有資料分級與最小化策略

### 必做工作

#### A. 治理與法務

- 建立隱私權政策
- 建立服務條款
- 建立 DPA（Data Processing Agreement）
- 建立子處理者清單（Gemini / Voyage / Pinecone / LlamaParse / R2 等）
- 明確說明資料保存地區、跨境傳輸與刪除機制
- 明確說明供應商資料是否用於模型訓練

#### B. 技術控制

- 在 production 正式啟用 RLS，並完成 canary 驗證
- 確認 app DB role 非 table owner / superuser，以免 PostgreSQL semantics 繞過 RLS
- 確認 Admin IP whitelist 在 production 實際啟用
- 補上管理員 2FA（至少 TOTP；進階可做 WebAuthn）
- 補上檔案惡意程式掃描（ClamAV 或等效方案）
- 補上安全事件告警與審計查詢流程

#### C. 資料生命週期

- 定義文件刪除、使用者刪除、租戶退租 purge 流程
- 明確列出 DB / R2 / Pinecone / cache / audit / backups 各自刪除策略
- 建立資料保留與刪除 SOP
- 建立刪除證明或操作紀錄格式

#### D. 資料最小化與分級

- 建立文件分類：一般、敏感、高敏感
- 高敏感資料預設不送外部 LLM 或需特別同意
- 針對薪資、身分、醫療類內容做遮罩或特殊路徑處理
- 提供可選的「受控模式」：限制第三方處理器使用範圍

### 驗收標準

- 能提供企業客戶可閱讀的資料流向圖
- 能回答所有子處理者與資料用途
- 能證明 tenant isolation 在 DB 層強制生效
- 能執行單文件刪除與整租戶清除
- 能提供隱私與資安問卷的標準回覆

---

## 5.4 租戶隔離與權限硬化

### 必做工作

- 將 `RLS_ENFORCEMENT_ENABLED=true` 導入 staging canary，再導入 production
- 驗證跨租戶讀取、刪除、檢索都會失敗
- 檢查 background jobs 與 superuser bypass 路徑
- 補充租戶隔離驗證腳本與證據

### 驗收標準

- 同租戶功能不受影響
- 跨租戶查詢回傳空集合或拒絕
- superuser 只在明確授權情境可跨租戶
- 驗證結果可被文件化保存

---

## 5.5 維運可靠性與部署安全

### 必做工作

- 修正 production deploy workflow，migration 失敗不能被吞掉
- 建立 staging 到 production 的完整驗證清單
- 接上 Alertmanager 至 Slack / Email
- 建立可執行的 rollback runbook
- 補上定期備份驗證與 restore drill 記錄
- 建立 SLO / SLA / incident 分級與通報流程

### 驗收標準

- 部署失敗時 workflow 必須 fail fast
- 告警觸發時值班人員會收到主動通知
- 每月至少完成一次 restore 驗證
- 有 5xx、latency、queue backlog、DB 連線數、worker 異常等關鍵告警

---

## 5.6 前台與客戶營運能力

### 必做工作

- 客服入口（如 Crisp / Intercom / Zendesk）
- 使用者操作文件 / FAQ / 管理員導入指南
- Onboarding Checklist
- 方案比較、使用量、帳單、合約狀態頁面

### 驗收標準

- 新租戶可在無人工介入下完成核心功能上手
- 客訴與問題可進入標準化支援流程
- 付費客戶能自助查看方案與使用量

---

## 5.7 效能、品質與 AI 可靠性

### 必做工作

- 執行正式 load test 並保存報告
- 補上 chat / upload / search / concurrent user 的 SLO
- 修正結構化計算與高風險法律題型
- 降低 OCR 誤判與不確定答案的錯誤自信
- 對高風險答案建立 guardrail 與免責呈現方式

### 驗收標準

- 有生產等級壓測報告
- 可量化的 p95 latency / success rate / 5xx 指標
- 計算題與高風險法律題有結構化或規則化處理
- 高不確定答案會清楚表明限制，不偽裝成確定結論

---

## 5.8 認證與 Session 安全

### 背景

目前 JWT access token TTL 為 8 小時，無 refresh token 機制。用戶每日需重新登入，且無法實作 token rotation 以降低 token 被盜用的風險。

### 必做工作

- 實作 refresh token 機制（httpOnly cookie 或安全存儲）
- refresh token 具有獨立 TTL（建議 7-30 天）與一次性使用
- 實作 token rotation：每次 refresh 時同時更新 refresh token
- 支援 token revocation（登出時、密碼變更時）
- SSO Client ID 設定完成（Google OAuth / Microsoft OAuth）

### 驗收標準

- Access token 過期後可無感刷新，用戶不中斷操作
- 登出或密碼變更後舊 refresh token 立即失效
- SSO 登入流程在 staging 與 production 可正常完成
- Token rotation 異常偵測：同一 refresh token 重複使用時撤銷整個 session family

---

## 5.9 部署自動回滾

### 背景

目前 production deploy workflow 在 health check 失敗（6 次 × 10 秒）後只會報錯讓 workflow 失敗，但不會自動回滾到前一版本。對付費 SaaS 而言，部署失敗必須能自動恢復服務。

### 必做工作

- 在 deploy-production workflow 中，health check 失敗後自動觸發 rollback step
- rollback step 使用先前成功版本的 image tag 重新部署
- 加入 migration dry-run（`alembic upgrade --sql`）於 staging pipeline，提前發現 schema 問題
- 建立 rollback 歷史紀錄（哪個版本、什麼原因、何時回滾）

### 驗收標準

- 模擬部署失敗時，系統可在 3 分鐘內自動回滾至前一版本
- 回滾過程不需人工 SSH 操作
- 每次回滾事件都有 Slack / Email 通知

---

## 5.10 資料庫連線安全與 Secrets 管理

### 背景

目前 DB 連線未強制 SSL（`sslmode` 未出現在 config 中），在多租戶 SaaS 中，DB 傳輸加密為基本要求。同時，所有 API Key（Gemini / Voyage / R2 / LlamaParse）皆存放於 `.env` 檔案，未使用集中式 secrets 管理。

### 必做工作

- 在 `app/config.py` 與 DB 連線字串中加入 `sslmode=require`
- 確認 PostgreSQL server 端已啟用 SSL 並使用有效憑證
- 規劃 secrets 遷移至 AWS Secrets Manager 或 HashiCorp Vault
- 建立 API Key rotation SOP（至少每季輪換一次）

### 驗收標準

- DB 連線在非 SSL 模式下拒絕連接
- 生產環境無明文 secrets 存放於檔案系統（`.env` 僅用於開發）
- 有文件記錄的 key rotation 操作流程

---

## 5.11 測試覆蓋率與前端 E2E 測試

### 背景

目前 CI pipeline 未整合 `pytest-cov`，測試覆蓋率未知。前端無 E2E 測試框架，付費關鍵路徑（登入 → 上傳 → 問答 → 查帳單）的前端迴歸無自動化驗證。

### 必做工作

- CI 加入 `pytest-cov`，設定覆蓋率門檻 ≥ 70%
- 對 payment webhook handler、tenant purge、RLS enforcement 等高風險路徑補充測試
- 整合 Playwright 或 Cypress 作為前端 E2E 測試框架
- 至少覆蓋以下關鍵路徑：登入 → 上傳文件 → Chat 問答 → 查看使用量

### 驗收標準

- CI pipeline 中覆蓋率報告自動生成，低於門檻值時 build 失敗
- 前端 E2E 測試在 CI 中可自動執行
- 高風險路徑測試覆蓋率 ≥ 90%

---

## 6. 依優先級分類的執行清單

## 6.1 P0：對外販售前必須完成

- 支付 / 訂閱閉環最小可行方案
- Email 系統
- 忘記密碼 / invitation flow
- 隱私權政策 / 條款 / DPA / 子處理者清單
- RLS 正式啟用與驗證
- Admin IP whitelist 生產確認
- Alertmanager 主動通知
- 修正 deployment workflow fail-fast
- 文件惡意程式掃描
- 資料流向圖與資料刪除 SOP
- **Refresh Token 機制（含 token rotation）**
- **部署失敗自動回滾（health check fail → auto rollback）**
- **DB 連線強制 SSL（sslmode=require）**
- **SSO Client ID 設定完成（Google / Microsoft OAuth）**

## 6.2 P1：第一批付費客戶前後應完成

- 自訂域名 SSL 自動申請與續期
- 管理員 2FA
- 客服入口與 Help Center
- Onboarding 流程
- 帳單頁、發票資訊欄位
- 安全白皮書 / 企業問卷模板
- **CI 加入 pytest-cov，設定覆蓋率門檻 ≥ 70%**
- **前端 E2E 測試（至少覆蓋 login → upload → chat → billing）**
- **Secrets 遷移至 AWS Secrets Manager 或 Vault**
- **API rate limit 的租戶自訂調整能力**

## 6.3 P2：Enterprise 與規模化階段

- 多區域真實基礎設施
- 資料駐留策略
- BYOK / 欄位級加密 / 進階 KMS
- WebAuthn / SSO 深化 / SCIM
- SOC 2 / ISO 27001 / 外部滲透測試
- 狀態頁與公開 SLA

---

## 7. 建議分階段路線圖

## Phase 1：2-4 週，達到「可收費企業 Beta」

目標：可服務少量付費客戶，但仍允許部分流程人工介入。

### 本階段交付

- Email 系統
- 忘記密碼 / invitation flow
- Alertmanager
- production deploy fail-fast 修正
- **部署失敗自動回滾機制**
- RLS canary → production 啟用
- 隱私權政策 / 服務條款 / DPA 初版
- 子處理者清單與資料流向圖
- 文件刪除與退租 purge SOP
- 負載測試與 restore drill
- **Refresh Token 機制與 token rotation**
- **DB 連線強制 SSL**
- **SSO Client ID 設定完成（Google / Microsoft）**

### 商業模式

- 可先採人工開票或 Payment Link
- 適合 1-5 家設計夥伴 / 早期企業客戶

---

## Phase 2：4-8 週，達到「標準 SaaS 可販售」

目標：降低人工營運成本，開始支持較標準的對外販售流程。

### 本階段交付

- 正式金流 / 訂閱 lifecycle
- 帳單與發票資訊
- 自訂域名 SSL 自動化
- 客服入口 / Onboarding / FAQ
- 管理員 2FA
- 安全白皮書 / 標準法務包
- **CI 測試覆蓋率門檻 ≥ 70%**
- **前端 E2E 測試（Playwright / Cypress）**
- **Secrets 遷移至集中式管理（Vault / Secrets Manager）**

---

## Phase 3：2-6 個月，達到「Enterprise Ready」

目標：提升大型客戶採購與續約成功率。

### 本階段交付

- 多區域與資料駐留
- 外部滲透測試
- SOC 2 / ISO 27001 規劃
- 高敏模式與資料分級路由
- 進階 IAM / WebAuthn / SCIM

---

## 8. Go / No-Go 檢查清單

以下條件未滿足時，不建議直接開放自助式對外販售：

- [ ] 付款與訂閱狀態可自動同步
- [ ] 可正常寄送驗證信、邀請信、重設密碼信
- [ ] 有隱私權政策、服務條款、DPA、子處理者清單
- [ ] production 的 RLS 已啟用並驗證
- [ ] 管理面網路限制已啟用
- [ ] 文件上傳已整合惡意程式掃描
- [ ] 告警能主動通知值班人員
- [ ] 部署流程不會吞 migration 失敗
- [ ] 文件與租戶的資料刪除流程可執行
- [ ] 已完成正式 load test 與 restore drill
- [ ] 客服與 Onboarding 有基本產品化能力
- [ ] **Refresh token 機制已實作並支援 token rotation**
- [ ] **部署失敗可自動回滾，無需人工 SSH**
- [ ] **DB 連線已強制 SSL 加密**
- [ ] **SSO（Google / Microsoft）可在生產環境正常登入**

若上述條件尚未完成，建議維持下列銷售模式：

- 企業導入型銷售
- 設計夥伴 / 試點客戶
- 人工支援較高的付費 PoC

---

## 9. 對外銷售時的定位建議

在所有 P0 工作完成前，建議對外定位為：

- 「企業 AI 知識助理 Beta」
- 「受邀試用 / 顧問導入」
- 「限量設計夥伴方案」

不建議定位為：

- 完整自助式 SaaS
- 零接觸註冊即用產品
- 可直接承諾高等級企業合規能力的成熟平台

---

## 10. 建議立刻啟動的第一批工作

若只選最有商業價值的第一批工作，建議依序執行：

1. Email 系統 + 忘記密碼 + invitation flow
2. **Refresh Token + DB SSL + SSO Client ID 設定**（可與 #1 平行）
3. RLS 啟用與驗證
4. 隱私權政策 + 條款 + DPA + 子處理者清單
5. Alertmanager + deploy fail-fast + **自動回滾** + restore drill
6. 資料流向圖 + 刪除 SOP + 病毒掃描
7. Payment Link / 最小可行收費流程

---

## 11. 最終判斷

UniHR 已具備成為對外 SaaS 的技術核心，但要進入真正可持續販售的生產階段，還必須將以下三件事產品化：

1. 商業閉環
2. 隱私與資安治理
3. 維運與交付可靠性

真正決定這產品能不能賣，不是「模型會不會回答」，而是：

- 客戶敢不敢把內部知識庫放進來
- 系統壞掉時你們能不能快速知道並處理
- 資料要刪時你們能不能證明真的刪掉
- 法務與採購問到資料流向時，你們能不能拿出完整答案

當以上能力補齊後，UniHR 才能從「可用的 AI 多租戶原型」升級為「可在生產環境對外販售的 SaaS 產品」。

---

## 12. 文件處理大量吞吐量強化（已實作）

### 背景

企業客戶可能一次上傳數百至上千份 HR 文件（規章、辦法、表單），原架構為單檔上傳 + 單體 Celery task，在大量場景下成為瓶頸。

### 已完成改進

#### P0：核心吞吐量

| 項目 | 改進前 | 改進後 |
|------|--------|--------|
| 上傳方式 | 單檔 `POST /documents/upload` | 新增批量 `POST /documents/batch-upload`（最多 100 檔 / ZIP） |
| Worker 並行數 | 2 | 8（可透過環境變數調整） |
| 任務架構 | 單體 task（parse+embed+store） | 三階段 chain：`parse → embed → store` |
| Worker 記憶體 | 512 MB per child | 1 GB per child |

#### P1：穩定性與可觀測性

| 項目 | 說明 |
|------|------|
| Circuit Breaker | Voyage / Pinecone API 呼叫已整合斷路器 |
| 批量進度 API | `POST /documents/batch-progress`（輪詢文件處理狀態） |
| Prometheus 指標 | `document_parse_duration_seconds`、`document_embed_duration_seconds`、`document_store_duration_seconds`、`celery_document_tasks_total`、`celery_document_tasks_active` |
| 容器限制 | Docker worker 容器 mem_limit 提升至 2 GB |

#### P2：進階優化

| 項目 | 說明 |
|------|------|
| 優先佇列 | `celery` 一般佇列 + `bulk` 大檔佇列（>5MB 自動路由） |
| 並行寫入 | Pinecone upsert 透過 ThreadPoolExecutor 並行（最多 4 執行緒） |
| Docker 全面更新 | dev / staging / production / region 四套 docker-compose 已同步更新 |

### 預估吞吐量

| 規模 | 預估時間 |
|------|----------|
| 100 份文件 | ~5-15 分鐘 |
| 500 份文件 | ~15-40 分鐘 |
| 1000 份文件 | ~30-60 分鐘 |

*（以上基於 concurrency=8、Voyage API 不限流的理想估計）*

---

## 附錄 A：v1.1 新增缺口對照表

以下為 v1.1 依實際程式碼審查後新增的項目，原計畫未涵蓋：

| 新增項目 | 原因 | 優先級 | 歸入章節 |
|---|---|---|---|
| Refresh Token 機制 | JWT 8hr TTL 無 refresh，用戶體驗差且無法做 token rotation | P0 | 5.8 |
| 部署自動回滾 | health check fail 後無自動恢復，付費 SaaS 不可接受 | P0 | 5.9 |
| DB 連線強制 SSL | 多租戶 SaaS 的 DB 傳輸加密為基本要求 | P0 | 5.10 |
| SSO Client ID 空值 | Google/Microsoft OAuth client ID 未填，SSO 無法使用 | P0 | 5.8 |
| 測試覆蓋率報告 | CI 無 pytest-cov，高風險路徑覆蓋率未知 | P1 | 5.11 |
| 前端 E2E 測試 | 付費關鍵路徑無自動化前端驗證 | P1 | 5.11 |
| Secrets 集中管理 | API Key 存於 .env，企業安全問卷常見必問 | P1 | 5.10 |
| 租戶自訂 Rate Limit | 不同方案的企業客戶可能需要調整配額上限 | P1 | 6.2 |