# aihr Live E2E Test Report

**Server**: http://api.172-237-5-254.sslip.io
**Time**: 2026-02-11 18:37:47
**Duration**: 683.1s

## Summary

| Phase | Pass/Total | Score | % | Time |
|-------|-----------|-------|---|------|
| Phase 0 | 5/5 | 5/5 | 100% | 3.4s |
| Phase 1 | 15/15 | 15/15 | 100% | 12.5s |
| Phase 2 | 3/5 | 12/20 | 60% | 123.0s |
| Phase 3 | 2/3 | 8/12 | 67% | 136.3s |
| Phase 4 | 2/2 | 8/8 | 100% | 36.3s |
| Phase 5 | 2/2 | 8/8 | 100% | 66.5s |
| Phase 6 | 4/4 | 4/4 | 100% | 2.0s |
| Phase 7 | 2/2 | 8/8 | 100% | 48.7s |
| Phase 8 | 2/2 | 0/0 | N/A% | 44.5s |

**Total: 68/80 (85.0%) -- GOOD**

## Details

### Phase 0

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 0.1 | Health Check | OK | 1/1 | 411ms |  |
| 0.2 | Superuser Login | OK | 1/1 | 1027ms | eyJhbGciOiJIUzI1NiIs... |
| 0.3 | Get Tenant | OK | 1/1 | 307ms | ID=7a77da32-b9b... |
| 0.4 | Create HR User | OK | 1/1 | 817ms | hr-test-1770805586@example.com |
| 0.5 | HR User Login | OK | 1/1 | 879ms |  |

### Phase 1

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 1.1 | Upload hr-policy-test.md | OK | 1/1 | 886ms | ID=52d86ace |
| 1.2 | Upload 新增文件說明.md | OK | 1/1 | 434ms | ID=7bc206bd |
| 1.3 | Upload 勞動契約書-謝雅玲.pdf | OK | 1/1 | 1270ms | ID=8909ed40 |
| 1.4 | Upload 勞動契約書-謝雅玲.txt | OK | 1/1 | 390ms | ID=d545cb7d |
| 1.5 | Upload 員工名冊.csv | OK | 1/1 | 324ms | ID=d28d7b34 |
| 1.6 | Upload 員工名冊.pdf | OK | 1/1 | 809ms | ID=a2843012 |
| 1.7 | Upload 請假單範本-E012-周秀蘭.pdf | OK | 1/1 | 717ms | ID=f47bcb07 |
| 1.8 | Upload 請假單範本-E012-周秀蘭.txt | OK | 1/1 | 385ms | ID=0da52846 |
| 1.9 | Upload 健康檢查報告-E016-高淑珍.pdf | OK | 1/1 | 890ms | ID=e90454c1 |
| 1.10 | Upload 健康檢查報告-E016-高淑珍.txt | OK | 1/1 | 441ms | ID=5d49a806 |
| 1.11 | Upload 員工手冊-第一章-總則.md | OK | 1/1 | 549ms | ID=edddfb6b |
| 1.12 | Upload 員工手冊-第一章-總則.pdf | OK | 1/1 | 2485ms | ID=bd0bdd7c |
| 1.13 | Upload 獎懲管理辦法.md | OK | 1/1 | 496ms | ID=5aebbaff |
| 1.14 | Upload 獎懲管理辦法.pdf | OK | 1/1 | 2008ms | ID=efb425b8 |
| 1.15 | Upload README.md | OK | 1/1 | 450ms | ID=d4fd81cc |

### Phase 2

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| A1 | Q: 我們公司有交通津貼嗎？補助多少？ | OK | 4/4 | 690ms | hits=3/3 ans=公司提供交通津貼，依通勤距離補貼 500-2,000 元。金額範圍依員工手冊規定辦理，實際補助以距離... |
| A2 | Q: 公司績效考核是一年幾次？ | OK | 4/4 | 711ms | hits=3/3 ans=公司績效考核一年 2 次，分別在 6 月與 12 月各進行一次。此為公司內規規定的考核週期，詳見員工... |
| A3 | Q: 請問公司報帳有時間限制嗎？ | OK | 4/4 | 623ms | hits=1/3 ans=報帳需在費用發生後 30 日內完成，超過 30 日需填寫逾期報帳說明。超過 60 日不予核銷；代墊公... |
| A4 | Q: 新人到職第一天需要準備什麼？ | FAIL | 0/4 | 60465ms | HTTP 504: <html>
<head><title>504 Gateway Time-out</title>< |
| A5 | Q: 公司的加班費怎麼算？ | FAIL | 0/4 | 60504ms | HTTP 504: <html>
<head><title>504 Gateway Time-out</title>< |

### Phase 3

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| C1 | Q: 我們公司平日加班給 1.5 倍工資，這樣合法嗎？ | OK | 4/4 | 37990ms | hits=2/4 ans=公司平日加班給 1.5 倍，高於法定前 2 小時 1.34 倍，原則合法。但超過 2 小時仍需 1.... |
| C2 | Q: 員工特休沒休完，公司規定逾期視同放棄，這樣可以嗎？ | FAIL | 0/4 | 60500ms | HTTP 504: <html>
<head><title>504 Gateway Time-out</title>< |
| C3 | Q: 全勤獎金因為員工請生理假被扣掉，合法嗎？ | OK | 4/4 | 37856ms | hits=2/5 ans=### 員工特休逾期視同放棄的合法性
根據目前的參考資料，關於員工特休逾期視同放棄的規定並未明確列出... |

### Phase 4

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| D1 | Q: 公司目前有多少位員工？ | OK | 4/4 | 35632ms | hits=3/3 ans=根據目前的參考資料，並未提供公司目前有多少位員工的具體資訊。建議您諮詢 HR 部門以獲取準確的員工人... |
| D2 | Q: 技術部的平均月薪是多少？ | OK | 4/4 | 712ms | hits=3/3 ans=技術部平均月薪約 70,667 元（共 3 人平均）。計算使用員工名冊中所有該部門月薪欄位，已排除空... |

### Phase 5

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| E1 | Q: 如果明天有新人到職，我需要準備哪些流程和文件？ | OK | 4/4 | 23121ms | hits=3/5 ans=根據目前的參考資料，並未提供具體的新人到職流程和所需文件的詳細資訊。建議您諮詢 HR 部門以獲取準確... |
| E2 | Q: 請幫我比較正職和約聘人員在福利上有什麼差異？ | OK | 4/4 | 43389ms | hits=4/4 ans=### 正職與約聘人員在福利上的差異

根據目前的參考資料，雖然未明確列出正職與約聘人員的具體福利差... |

### Phase 6

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 6.1 | List Documents | OK | 1/1 | 936ms | 65 docs |
| 6.2 | Get Document Detail | OK | 1/1 | 280ms |  |
| 6.3 | GET /users/me | OK | 1/1 | 423ms | hr-test-1770805586@example.com |
| 6.4 | GET /audit/ | OK | 1/1 | 337ms |  |

### Phase 7

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| F1 | Follow: 承上題，如果這位員工年資未滿一年呢？ | OK | 4/4 | 28892ms | hits=3/3 |
| F2 | Follow: 那他可以申請育嬰假嗎？ | OK | 4/4 | 19812ms | hits=3/3 |

### Phase 8

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 8.1 | Chat Latency (5x avg) | OK | 0/0 | 44133ms | avg=44133ms min=42205ms max=46061ms |
| 8.2 | Health Latency (10x) | OK | 0/0 | 347ms | avg=348ms |
