# aihr 系統測試報告

**Run**: `run_20260211_130312` | **時間**: 13:03~13:03 | **耗時**: 10s

## 階段總覽

| 階段 | 標題 | 狀態 | 耗時 | 得分 | 得分率 |
|------|------|------|------|------|--------|
| 0 | 環境準備 | ✅ | 4s | 0/0 | N/A |
| 1 | 文件上傳 (11 檔) | ✅ | 6s | 0/0 | N/A |

**總分: 0/0 (0.0%) — ❌不合格**

---
## 詳細結果

### Phase 0: 環境準備

狀態: completed | 耗時: 3.7s

摘要: {"ok": 6, "fail": 0, "has_su": true, "has_hr": true, "tenant": "d9223114-e421-42fb-bd16-3c5bd19f8489"}

| # | 動作 | 狀態 | 評分 | 耗時 | 備註 |
|---|------|------|------|------|------|
| 0.1 | GET /aihr/health | ✅ | - | 342ms | aihr ok |
| 0.2 | GET /core/health | ✅ | - | 1523ms | core ok |
| 0.3 | POST /auth/login(su) | ✅ | - | 572ms | token ok |
| 0.4 | POST /tenants/ | ✅ | - | 334ms | tenant_id=d9223114-e421-4 |
| 0.5 | POST /users/ | ✅ | - | 608ms |  |
| 0.6 | POST /auth/login(hr) | ✅ | - | 616ms | hr token ok |

### Phase 1: 文件上傳 (11 檔)

狀態: completed | 耗時: 6.1s

摘要: {"uploaded": 11, "total": 11}

| # | 動作 | 狀態 | 評分 | 耗時 | 備註 |
|---|------|------|------|------|------|
| 1.5 | POST /upload(員工名冊.csv) | ✅ | - | 391ms | id=dff32925-8492-4d63-996 |
| 1.2 | POST /upload(獎懲管理辦法.pdf) | ✅ | - | 758ms | id=f4f067e3-980b-4438-bdf |
| 1.6 | POST /upload(202601-E00) | ✅ | - | 625ms | id=b9d22367-8e0a-4e76-a8f |
| 1.4 | POST /upload(報帳作業規範.pdf) | ✅ | - | 1064ms | id=35a0944c-7795-4723-aa4 |
| 1.7 | POST /upload(請假單範本-E012) | ✅ | - | 817ms | id=d60baff4-a324-4481-8f9 |
| 1.1 | POST /upload(員工手冊-第一章-總) | ✅ | - | 1910ms | id=af009065-e6d1-4672-afe |
| 1.8 | POST /upload(勞動契約書-謝雅玲.) | ✅ | - | 897ms | id=0f56b064-cfd7-48b5-94f |
| 1.3 | POST /upload(新人到職SOP.pd) | ✅ | - | 2214ms | id=5d196bea-a502-43f3-8ee |
| 1.10 | POST /upload(變更登記表A.jpg) | ✅ | - | 1277ms | id=0c118795-d058-4020-908 |
| 1.11 | POST /upload(變更登記表B.jpg) | ✅ | - | 1154ms | id=59c7e483-e8d9-4647-8a4 |
| 1.9 | POST /upload(健康檢查報告-E01) | ✅ | - | 2112ms | id=8840f930-5dc4-41b8-86f |
| 1.chk | 員工名冊.csv: completed | ✅ | - | 328ms |  |
| 1.chk | 獎懲管理辦法.pdf: parsing | ✅ | - | 299ms |  |
| 1.chk | 202601-E00: uploading | ✅ | - | 332ms |  |

---
## 問答詳細


---
日誌: `C:\Users\User\Desktop\aihr\test-data\test-results\run_20260211_130312`