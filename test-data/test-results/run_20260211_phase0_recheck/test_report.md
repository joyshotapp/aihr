# aihr 系統測試報告

**Run**: `run_20260211_phase0_recheck` | **時間**: 13:50~13:50 | **耗時**: 2s

## 階段總覽

| 階段 | 標題 | 狀態 | 耗時 | 得分 | 得分率 |
|------|------|------|------|------|--------|
| 0 | 環境準備 | ⚠️ | 2s | 0/0 | N/A |

**總分: 0/0 (0.0%) — ❌不合格**

---
## 詳細結果

### Phase 0: 環境準備

狀態: completed_with_errors | 耗時: 2.0s

摘要: {"ok": 2, "fail": 2, "has_su": false, "has_hr": false, "tenant": null}

| # | 動作 | 狀態 | 評分 | 耗時 | 備註 |
|---|------|------|------|------|------|
| 0.1 | GET /aihr/health | ✅ | - | 289ms | aihr ok |
| 0.2 | GET /core/health | ✅ | - | 1317ms | core ok |
| 0.3 | POST /auth/login(su) | ❌ | - | 366ms | fail:502 |
| 0.6 | POST /auth/login(hr) | ❌ | - | 350ms | hr fail |

---
## 問答詳細


---
日誌: `C:\Users\User\Desktop\aihr\test-data\test-results\run_20260211_phase0_recheck`