# aihr 系統測試報告

**Run**: `run_20260211_phase0_after_gateway_restart` | **時間**: 13:53~13:53 | **耗時**: 3s

## 階段總覽

| 階段 | 標題 | 狀態 | 耗時 | 得分 | 得分率 |
|------|------|------|------|------|--------|
| 0 | 環境準備 | ✅ | 3s | 0/0 | N/A |

**總分: 0/0 (0.0%) — ❌不合格**

---
## 詳細結果

### Phase 0: 環境準備

狀態: completed | 耗時: 3.4s

摘要: {"ok": 6, "fail": 0, "has_su": true, "has_hr": true, "tenant": "d9223114-e421-42fb-bd16-3c5bd19f8489"}

| # | 動作 | 狀態 | 評分 | 耗時 | 備註 |
|---|------|------|------|------|------|
| 0.1 | GET /aihr/health | ✅ | - | 318ms | aihr ok |
| 0.2 | GET /core/health | ✅ | - | 1239ms | core ok |
| 0.3 | POST /auth/login(su) | ✅ | - | 614ms | token ok |
| 0.4 | POST /tenants/ | ❌ | - | 341ms | tenant_id=d9223114-e421-4 |
| 0.5 | POST /users/ | ❌ | - | 366ms |  |
| 0.6 | POST /auth/login(hr) | ✅ | - | 571ms | hr token ok |

---
## 問答詳細


---
日誌: `C:\Users\User\Desktop\aihr\test-data\test-results\run_20260211_phase0_after_gateway_restart`