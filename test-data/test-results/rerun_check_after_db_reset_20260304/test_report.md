# aihr 系統測試報告

**Run**: `rerun_check_after_db_reset_20260304` | **目標**: `http://localhost:8001` | **時間**: 02:04~02:05 | **耗時**: 1s

## 階段總覽

| 階段 | 標題 | 狀態 | 耗時 | 得分 | 得分率 |
|------|------|------|------|------|--------|
| 0 | 環境準備 | ⚠️ | 1s | 0/0 | N/A |

**總分: 0/0 (0.0%) — ❌不合格**

---
## 詳細結果

### Phase 0: 環境準備

狀態: completed_with_errors | 耗時: 1.4s

摘要: {"ok": 2, "fail": 2, "has_su": false, "has_hr": false, "tenant": null}

| # | 動作 | 狀態 | 評分 | 耗時 | 備註 |
|---|------|------|------|------|------|
| 0.1 | GET /aihr/health | ✅ | - | 25ms | aihr ok |
| 0.2 | GET /core/health | ✅ | - | 1271ms | core ok |
| 0.3 | POST /auth/login(su) | ❌ | - | 90ms | fail:500 |
| 0.6 | POST /auth/login(hr) | ❌ | - | 26ms | hr fail |

---
## 問答詳細


---
日誌: `C:\Users\User\Desktop\aihr\test-data\test-results\rerun_check_after_db_reset_20260304`