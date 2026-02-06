# UniHR 勞資 AI SaaS 專案

這是一個結合「專業勞動法知識庫」與「企業內規管理」的多租戶 B2B SaaS 平台。

## 專案概況

本專案旨在解決企業 HR 的痛點：
- 結合 **台灣勞動法 Core API**（提供法律底層邏輯與最新法規）。
- 提供 **企業專屬知識庫**（Isolated Tenant Knowledge Base）。
- 保障資料隱私，確保不同企業間的資料絕對隔離。

詳細的產品規格與技術計畫請參閱 [PROJECT_PLAN.md](PROJECT_PLAN.md)。

## 核心功能

- **多租戶架構**：每家公司擁有獨立的空間與知識庫索引。
- **混合檢索 (RAG)**：同時查詢「公司內規」與「勞動法 Core」並合併回答。
- **權限與稽核**：完整的角色權限控制與操作稽核紀錄。
- **成本追蹤**：精確記錄每租戶的 Token 用量與查詢成本。

## 開發計畫

目前的開發階段：**Phase 0-1 啟動中**

請參閱 [PROJECT_PLAN.md](PROJECT_PLAN.md) 中的 `Task Plan` 章節了解詳細任務清單。

## 目錄結構 (規劃中)

```
unihr-saas/
├── app/                  # 後端應用程式碼 (FastAPI)
├── docs/                 # 專案文件
├── tests/                # 測試程式
├── docker-compose.yml    # 開發環境配置
└── PROJECT_PLAN.md       # 產品規格書
```
