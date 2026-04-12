# UniHR 正式上線前最終審查報告

日期：2026-04-12

## 結論

本次審查結論為：**No-Go（不建議直接正式上線或對外開賣）**。

理由不是單一功能缺失，而是多個會直接影響正式營運、法遵可信度、支付可用性與資安暴露面的阻斷項同時存在。產品本身已具備相當完整的 SaaS 骨架與多租戶能力，但距離「可放心正式收費、承接真實企業資料、對外宣稱 production ready」仍有明顯落差。

本次判定依據包含：既有專案文件、核心程式碼抽查、部署設定抽查、測試覆蓋盤點、前端公開面檢視與 Git 追蹤狀態確認。

## Go/No-Go 判定

- 決策：**No-Go**
- 建議狀態：先完成 P0 阻斷項，再進行一次 48-72 小時的 release candidate 驗證
- 可轉為 Go 的前提：支付路徑可用、法遵文件可對外、公開憑證暴露清除、上線安全基線與關鍵流程測試完成

## P0 阻斷項

### 1. 公開文件仍暴露管理入口與預設帳密資訊

- [README.md](README.md#L41-L47) 直接揭露正式站點 IP、管理後台入口，並保留管理員預設帳密描述。
- 這不是內部工程備忘錄等級的問題，而是任何接觸 repo 或部署文件的人都能取得高價值攻擊資訊。
- 即使實際密碼已變更，只要公開文件仍保留此內容，對外審計時也會被視為重大治理失誤。

**判定**：正式開賣前必須移除。

### 2. 金流主線雖已接藍新，但升級入口分叉且存在未清理的 Stripe 遺留實作

- 目前正式金流主線是 NewebPay，主 checkout 與 webhook 入口分別在 [app/api/v1/endpoints/payment.py](app/api/v1/endpoints/payment.py#L53-L143) 與 [app/services/newebpay.py](app/services/newebpay.py#L108-L233)。
- 但系統同時保留另一套升級邏輯於 [app/api/v1/endpoints/subscription.py](app/api/v1/endpoints/subscription.py#L188-L223)，而前端實際走的是 [frontend/src/pages/SubscriptionPage.tsx](frontend/src/pages/SubscriptionPage.tsx#L55-L76) 直接呼叫 `/payment/checkout`。
- 這代表付款主線與升級 API 已經分叉，未來在權限、訊息文案、例外處理與測試上容易失真。
- 專案內另有 [app/api/v1/endpoints/stripe_webhook.py](app/api/v1/endpoints/stripe_webhook.py) 遺留實作，但目前未掛入主 API router，不應視為正式啟用功能；它更像未清理的半接線程式，會增加維運與審查時的混淆成本。

**判定**：正式開賣前，至少要先收斂成單一付款主線，並明確標示或移除未啟用的 Stripe 遺留程式。

### 3. 法律頁面已存在，但仍是 placeholder 等級，不足以支撐正式商業化

- [frontend/src/pages/PrivacyPage.tsx](frontend/src/pages/PrivacyPage.tsx) 與 [frontend/src/pages/TermsPage.tsx](frontend/src/pages/TermsPage.tsx) 已有頁面。
- 但頁面內容仍使用 `privacy@example.com`、`support@example.com`、`legal@example.com` 等 placeholder 聯絡資訊。
- 條款雖有結構，但目前仍欠缺可驗證的營運主體資訊、正式聯絡窗口、SLA/DPA 對接方式與法務定稿痕跡。
- [docs/DPA_TEMPLATE.md](docs/DPA_TEMPLATE.md) 僅是模板，尚不能視為對外可簽署文件。

**判定**：可以當草稿，不可以當正式對外法遵文件。

### 4. 正式環境安全基線與實際部署狀態存在落差

- [app/config.py](app/config.py#L267-L300) 有 production/staging 啟動阻擋器，方向是對的。
- 但部署筆記顯示實際環境曾使用 HTTP-only cookie 與非強制 DB SSL，代表「文件中的安全基線」與「實際部署事實」可能不一致。
- [app/config.py](app/config.py#L163) 預設 `MFA_REQUIRED_FOR_PRIVILEGED=False`。
- [app/api/deps_permissions.py](app/api/deps_permissions.py#L16-L28) 只有在該旗標開啟時才會真正對管理角色強制 2FA。
- [app/middleware/rate_limit.py](app/middleware/rate_limit.py#L65-L89) 在 Redis 不可用時採 fail-open，會直接放行請求。

**判定**：在正式商業環境中，這些控制不能只存在於程式碼，必須有已套用且已驗證的證據。

### 5. 關鍵商業流程測試證據不足

- 前端 E2E 目前只有 [frontend/e2e/auth.spec.ts](frontend/e2e/auth.spec.ts) 與 [frontend/e2e/app.spec.ts](frontend/e2e/app.spec.ts) 兩個 spec。
- [frontend/e2e/app.spec.ts](frontend/e2e/app.spec.ts#L13) 與 [frontend/e2e/app.spec.ts](frontend/e2e/app.spec.ts#L30) 的登入後流程在未提供環境變數時會直接 skip。
- 測試目錄中看得到 NewebPay provider 單元測試 [tests/test_newebpay.py](tests/test_newebpay.py)，但沒有找到藍新實際付款主線、密碼重設、驗證信、重新寄信、接受邀請等關鍵路徑的完整測試證據。

**判定**：不能用目前測試覆蓋作為正式收費前的品質保證。

## 高風險項

### 1. 多租戶安全仍高度依賴應用層自律

- [app/db/session.py](app/db/session.py#L112-L140) 確實有 RLS context 注入能力，這是正向設計。
- 但同時存在明確警告開發者「不要直接用無 tenant filter API」的程式，例如 [app/crud/crud_chat.py](app/crud/crud_chat.py#L10-L23) 與 [app/crud/crud_document.py](app/crud/crud_document.py#L10-L26)。
- 這種設計代表：RLS 與租戶隔離雖然存在，但仍不是完全防呆；一旦有新功能漏套 tenant 條件或未正確套用 session context，就可能出現跨租戶暴露。

**風險判定**：高。

### 2. 預設值治理仍然偏開發友善，不夠商業化穩健

- [app/config.py](app/config.py#L15-L38) 仍保留預設 `SECRET_KEY`、初始管理員密碼與資料庫密碼（含 `POSTGRES_PASSWORD`）。
- 雖然 [app/config.py](app/config.py#L267-L300) 已阻擋 production/staging 使用不安全預設值，但這種設計仍會讓新環境、腳本、臨時部署或人為操作更容易踩到錯誤配置。
- 這不是立即 exploitable 的 production bug，但對正式商業化來說，屬於治理品質不足。

**風險判定**：高。

### 3. README、文件與實際能力仍有敘事過度的問題

- README 與多份文件對「已完成」「production ready」「安全完成」的表述偏強。
- 但實際抽查顯示支付、法遵、部署證據、關鍵 E2E 與正式安全控制仍未完全閉環。
- 這種落差在對外銷售、投標、法務審查與客戶 security questionnaire 階段會成為信任風險。

**風險判定**：高。

## 中風險項

### 1. Rate limiting 採 Redis fail-open

- [app/middleware/rate_limit.py](app/middleware/rate_limit.py#L65-L89) 在 Redis 無法使用時會直接允許請求。
- **✅ 已修復（2026-04-12）**：登入、忘記密碼、重設密碼、驗證信、付款 checkout、付款 webhook、邀請接受等高風險路徑已改為 `fail_closed=True`，Redis 失效時回傳 `503 Service Unavailable`；一般路徑保持 fail-open 以維持可用性。高風險路徑同時套用更嚴格的每分鐘 10 次限流（可透過 `RATE_LIMIT_HIGH_RISK` 環境變數覆蓋）。

### 2. 管理角色 2FA 是能力存在，不是預設落地

- [app/api/v1/endpoints/auth.py](app/api/v1/endpoints/auth.py#L182-L186) 只有已啟用 2FA 的管理用戶才會走 MFA challenge。
- 若部署未將 `MFA_REQUIRED_FOR_PRIVILEGED` 打開，則管理角色仍可能在無 2FA 的情況下操作高權限功能。

### 3. 公開法務頁面已上線，但缺少正式營運資訊

- [frontend/src/pages/PrivacyPage.tsx](frontend/src/pages/PrivacyPage.tsx) 與 [frontend/src/pages/TermsPage.tsx](frontend/src/pages/TermsPage.tsx) 的結構合理。
- 問題不是「沒有頁面」，而是內容仍偏模板化，尚未達到可直接面向企業客戶簽約或接受法務檢視的成熟度。

### 4. E2E 更像 smoke test，不是 release gate

- [frontend/e2e/auth.spec.ts](frontend/e2e/auth.spec.ts) 主要覆蓋公開頁、跳轉與未登入保護。
- [frontend/e2e/app.spec.ts](frontend/e2e/app.spec.ts) 僅覆蓋登入後能否看到文件頁與聊天輸入框。
- 尚未覆蓋文件上傳、付款、邀請註冊、驗證信、角色權限矩陣、租戶間隔離回歸等正式上線前必測流程。

### 5. 帳單欄位 `amount_usd` 命名與實際幣別不符

- [app/models/billing.py](app/models/billing.py#L23) 的 `BillingRecord` 模型中，欄位命名為 `amount_usd`，但藍新金流實際儲存的幣別為 **TWD**。
- 此欄位命名在對帳、稽核紀錄、外部財務報表及 API 回傳時，會直接造成幣別誤判；若未來接入多幣別計費或通過外部財務稽核，此欄位將成為資料正確性爭議點。
- 建議透過 Alembic migration 重命名為 `amount` 或 `amount_twd`，並同步更新所有 ORM 引用與 API schema。

## 正向觀察

以下是本產品已具備、且值得保留的基礎：

- [app/config.py](app/config.py#L267-L300) 的 production/staging 啟動安全阻擋器是正確方向。
- [app/db/session.py](app/db/session.py#L112-L140) 已有 RLS session context 設計。
- [app/services/chat_orchestrator.py](app/services/chat_orchestrator.py#L714-L819) 顯示 LLM guardrail 與敏感資訊過濾並非只寫在文件裡。
- [tests/test_newebpay.py](tests/test_newebpay.py) 顯示支付 provider 至少有基礎單元測試。
- [frontend/src/App.tsx](frontend/src/App.tsx#L58-L71) 的公開站、受保護工作台、舊路由轉址整理得相對清楚。

換句話說，這不是「產品做不起來」，而是「已經有骨架，但最後一哩的上線治理與正式營運證據還不夠」。

## 各面向評分

以下為本次審查的主觀營運評分，滿分 10 分：

- 產品功能完整度：7.5/10
- 後端架構成熟度：7/10
- 多租戶與安全設計：6.5/10
- 正式部署與營運治理：5/10
- 支付與商業化準備：4.5/10
- 法遵與對外文件成熟度：4/10
- 測試可作為上線證據的程度：4.5/10

整體正式開賣就緒度：**5.3/10**

## 建議修復順序

### P0：必須先完成

1. 移除 [README.md](README.md#L41-L47) 中所有正式管理入口、IP 與預設帳密敘述。
2. 收斂金流主線，移除或明確標示未啟用的 Stripe 遺留程式，並統一 `/subscription` 與 `/payment` 的升級流程。
3. 將隱私權政策、服務條款、DPA、法務聯絡資訊替換為正式內容，不得再使用 placeholder。
4. 確認正式部署已啟用 TLS、Secure cookie、管理角色 2FA、管理入口 IP 隔離、DB SSL 或替代保護控制。
5. 補齊支付、驗證信、重設密碼、邀請註冊、管理角色登入與權限矩陣的測試證據。

### P1：正式開賣前強烈建議完成

1. 將登入、忘記密碼、驗證、支付等高風險路徑改為限流 fail-closed 或降級保護模式。
2. 對所有高風險 CRUD 路徑進行 tenant filter / RLS context 專項審查。
3. 做一輪 production-like staging 演練，保留可審計的驗證紀錄與截圖。

### P2：正式營運後一個版本內完成

1. 建立 Security Questionnaire 回覆包。
2. 建立 SLA / incident response / customer-facing trust docs。
3. 建立真正可用的 release gate 與回歸測試矩陣。
4. 透過 Alembic migration 將 `BillingRecord.amount_usd` 重命名為 `amount_twd`，消除幣別語意歧義。
   **✅ 已完成（2026-04-12）**：`billing_records.amount_usd` 已透過 SQL ALTER TABLE 重命名為 `amount_twd`，DB currency 預設改為 `TWD`。相關 ORM、API schema（billing.py、analytics.py、payment.py）、前端型別（api.ts、SubscriptionPage.tsx）、invoice PDF 格式（`NT$` + 整數顯示）全數更新。Alembic 版本已 stamp 為 `t12_1`。

## 建議的上線前驗收清單

在重新申請上線審查前，至少應提供以下證據：

- 正式法務文件定稿版
- 實際部署設定截圖或檢查輸出，證明已啟用 HTTPS、Secure cookie、2FA、IP whitelist
- 支付成功、退款/失敗、訂閱取消的 end-to-end 驗證紀錄
- 密碼重設、驗證信、邀請接受流程的測試紀錄
- Playwright 或整合測試報告，不可大量 rely on skip
- 一份最新的 release checklist 執行結果

## 審查範圍說明

本次審查以靜態審查與抽樣驗證為主，未在此輪直接重跑完整測試矩陣或 live production 演練。因此本報告偏向「上線阻斷風險盤點」與「正式商業化治理審查」，不是完整滲透測試替代品。

但就本次已取得的證據而言，No-Go 判定已足夠明確。