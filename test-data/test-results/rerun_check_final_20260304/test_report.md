# aihr 系統測試報告

**Run**: `rerun_check_final_20260304` | **目標**: `http://localhost:8001` | **時間**: 02:07~02:07 | **耗時**: 2s

## 階段總覽

| 階段 | 標題 | 狀態 | 耗時 | 得分 | 得分率 |
|------|------|------|------|------|--------|
| 0 | 環境準備 | ✅ | 2s | 0/0 | N/A |

**總分: 0/0 (0.0%) — ❌不合格**

---
## 詳細結果

### Phase 0: 環境準備

狀態: completed | 耗時: 2.0s

摘要: {"ok": 6, "fail": 0, "has_su": true, "has_hr": true, "tenant": "4520faf7-e68c-46dc-a048-bfde8e1bce74"}

| # | 動作 | 狀態 | 評分 | 耗時 | 備註 |
|---|------|------|------|------|------|
| 0.1 | GET /aihr/health | ✅ | - | 13ms | aihr ok |
| 0.2 | GET /core/health | ✅ | - | 1343ms | core ok |
| 0.3 | POST /auth/login(su) | ✅ | - | 236ms | token ok |
| 0.4 | POST /tenants/ | ✅ | - | 39ms | tenant_id=4520faf7-e68c-4 |
| 0.5 | POST /users/ | ✅ | - | 177ms |  |
| 0.6 | POST /auth/login(hr) | ✅ | - | 162ms | hr token ok |

---
## 問答詳細


---
日誌: `C:\Users\User\Desktop\aihr\test-data\test-results\rerun_check_final_20260304`