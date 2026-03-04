# aihr Live E2E Test Report

**Server**: http://api.172-237-5-254.sslip.io
**Time**: 2026-02-11 12:24:32
**Duration**: 354.7s

## Summary

| Phase | Pass/Total | Score | % | Time |
|-------|-----------|-------|---|------|
| Phase 0 | 5/5 | 5/5 | 100% | 2.5s |
| Phase 1 | 15/15 | 15/15 | 100% | 8.7s |
| Phase 2 | 5/5 | 19/20 | 95% | 228.5s |
| Phase 3 | 1/1 | 2/4 | 50% | 35.4s |

**Total: 41/44 (93.2%) -- EXCELLENT**

## Details

### Phase 0

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 0.1 | Health Check | OK | 1/1 | 321ms |  |
| 0.2 | Superuser Login | OK | 1/1 | 549ms | eyJhbGciOiJIUzI1NiIs... |
| 0.3 | Get Tenant | OK | 1/1 | 346ms | ID=b4539d8d-ea5... |
| 0.4 | Create HR User | OK | 1/1 | 605ms | hr-test-1770783519@example.com |
| 0.5 | HR User Login | OK | 1/1 | 716ms |  |

### Phase 1

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 1.1 | Upload hr-policy-test.md | OK | 1/1 | 524ms | ID=ed893014 |
| 1.2 | Upload 新增文件說明.md | OK | 1/1 | 390ms | ID=c1bd9fe5 |
| 1.3 | Upload 勞動契約書-謝雅玲.pdf | OK | 1/1 | 1115ms | ID=5f2b61f2 |
| 1.4 | Upload 勞動契約書-謝雅玲.txt | OK | 1/1 | 311ms | ID=90aa3244 |
| 1.5 | Upload 員工名冊.csv | OK | 1/1 | 340ms | ID=dcbeed2a |
| 1.6 | Upload 員工名冊.pdf | OK | 1/1 | 777ms | ID=b56aaa10 |
| 1.7 | Upload 請假單範本-E012-周秀蘭.pdf | OK | 1/1 | 749ms | ID=06a7f4c2 |
| 1.8 | Upload 請假單範本-E012-周秀蘭.txt | OK | 1/1 | 329ms | ID=041d342a |
| 1.9 | Upload 健康檢查報告-E016-高淑珍.pdf | OK | 1/1 | 1072ms | ID=aad0cb73 |
| 1.10 | Upload 健康檢查報告-E016-高淑珍.txt | OK | 1/1 | 311ms | ID=a4a13b76 |
| 1.11 | Upload 員工手冊-第一章-總則.md | OK | 1/1 | 376ms | ID=8da40161 |
| 1.12 | Upload 員工手冊-第一章-總則.pdf | OK | 1/1 | 768ms | ID=2bb0a9e9 |
| 1.13 | Upload 獎懲管理辦法.md | OK | 1/1 | 357ms | ID=ff662a70 |
| 1.14 | Upload 獎懲管理辦法.pdf | OK | 1/1 | 937ms | ID=0c5a8989 |
| 1.15 | Upload README.md | OK | 1/1 | 381ms | ID=31d5e9be |

### Phase 2

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| A1 | Q: 我們公司有交通津貼嗎？補助多少？ | OK | 4/4 | 47001ms | hits=3/3 ans=### 交通津貼相關資訊

1. **交通津貼的發放依據**
   - 根據《就業促進津貼實施辦法》... |
| A2 | Q: 公司績效考核是一年幾次？ | OK | 4/4 | 32408ms | hits=3/3 ans=### 績效考核的頻率

1. **考核次數**
   - 根據目前的參考資料，並未明確規定公司績效... |
| A3 | Q: 請問公司報帳有時間限制嗎？ | OK | 4/4 | 49239ms | hits=3/3 ans=### 公司報帳的時間限制

1. **報帳的基本要求**
   - 根據《勞動基準法》第30條，雇... |
| A4 | Q: 新人到職第一天需要準備什麼？ | OK | 3/4 | 41771ms | hits=3/4 ans=### 新人到職第一天需要準備的事項

1. **勞工名卡**
   - 雇主應置備勞工名卡，記載勞... |
| A5 | Q: 公司的加班費怎麼算？ | OK | 4/4 | 58049ms | hits=3/3 ans=### 加班費的計算方式

根據《勞動基準法》第24條的規定，加班費的計算方式如下：

1. **平... |

### Phase 3

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| C1 | Q: 我們公司平日加班給 1.5 倍工資，這樣合法嗎？ | OK | 2/4 | 35374ms | hits=2/4 ans=### 公司平日加班費的合法性分析

根據《勞動基準法》第24條的規定，平日加班的工資計算標準如下：... |
