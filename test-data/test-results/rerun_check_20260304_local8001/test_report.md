# aihr 系統測試報告

**Run**: `rerun_check_20260304_local8001` | **目標**: `http://localhost:8001` | **時間**: 02:03~02:03 | **耗時**: 8s

## 階段總覽

| 階段 | 標題 | 狀態 | 耗時 | 得分 | 得分率 |
|------|------|------|------|------|--------|
| 0 | 環境準備 | ⚠️ | 8s | 0/0 | N/A |

**總分: 0/0 (0.0%) — ❌不合格**

---
## 詳細結果

### Phase 0: 環境準備

狀態: completed_with_errors | 耗時: 8.5s

摘要: {"ok": 2, "fail": 2, "has_su": false, "has_hr": false, "tenant": null}

| # | 動作 | 狀態 | 評分 | 耗時 | 備註 |
|---|------|------|------|------|------|
| 0.1 | GET /aihr/health | ✅ | - | 8ms | aihr ok |
| 0.2 | GET /core/health | ✅ | - | 1203ms | core ok |
| 0.3 | POST /auth/login(su) | ❌ | - | 4097ms | fail:500 |
| 0.6 | POST /auth/login(hr) | ❌ | - | 3176ms | hr fail |

---
## 問答詳細


---
日誌: `C:\Users\User\Desktop\aihr\test-data\test-results\rerun_check_20260304_local8001`