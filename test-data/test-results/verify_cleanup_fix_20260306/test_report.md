# aihr 系統測試報告

**Run**: `verify_cleanup_fix_20260306` | **目標**: `http://localhost:8002` | **時間**: 03:26~03:26 | **耗時**: 3s

## 階段總覽

| 階段 | 標題 | 狀態 | 耗時 | 得分 | 得分率 |
|------|------|------|------|------|--------|
| 0 | 環境準備 | ✅ | 3s | 0/0 | N/A |

**總分: 0/0 (0.0%) — ❌不合格**

---
## 詳細結果

### Phase 0: 環境準備

狀態: completed | 耗時: 3.1s

摘要: {"ok": 6, "fail": 0, "has_su": true, "has_hr": true, "tenant": "4520faf7-e68c-46dc-a048-bfde8e1bce74"}

| # | 動作 | 狀態 | 評分 | 耗時 | 備註 |
|---|------|------|------|------|------|
| 0.1 | GET /aihr/health | ✅ | - | 15ms | aihr ok |
| 0.2 | GET /core/health | ✅ | - | 1673ms | core ok |
| 0.3 | POST /auth/login(su) | ✅ | - | 222ms | token ok |
| 0.4 | POST /tenants/ | ✅ | - | 26ms | tenant_id=4520faf7-e68c-4 |
| 0.5 | POST /users/ | ✅ | - | 28ms |  |
| 0.6 | POST /auth/login(hr) | ✅ | - | 175ms | hr token ok |

---
## 問答詳細


---
日誌: `C:\Users\User\Desktop\aihr\test-data\test-results\verify_cleanup_fix_20260306`