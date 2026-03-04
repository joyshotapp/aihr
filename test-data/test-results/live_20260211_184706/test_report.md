# aihr Live E2E Test Report

**Server**: http://api.172-237-5-254.sslip.io
**Time**: 2026-02-11 19:20:00
**Duration**: 1974.0s

## Summary

| Phase | Pass/Total | Score | % | Time |
|-------|-----------|-------|---|------|
| Phase 0 | 5/5 | 5/5 | 100% | 23.7s |
| Phase 1 | 15/15 | 15/15 | 100% | 157.2s |
| Phase 2 | 4/5 | 16/20 | 80% | 329.0s |
| Phase 3 | 2/3 | 8/12 | 67% | 292.6s |
| Phase 4 | 1/2 | 4/8 | 50% | 210.8s |
| Phase 5 | 1/2 | 4/8 | 50% | 219.8s |
| Phase 6 | 4/4 | 4/4 | 100% | 6.5s |
| Phase 7 | 2/2 | 8/8 | 100% | 175.8s |
| Phase 8 | 2/2 | 0/0 | N/A% | 63.2s |

**Total: 64/80 (80.0%) -- GOOD**

## Details

### Phase 0

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 0.1 | Health Check | OK | 1/1 | 326ms |  |
| 0.2 | Superuser Login | OK | 1/1 | 1577ms | eyJhbGciOiJIUzI1NiIs... |
| 0.3 | Get Tenant | OK | 1/1 | 576ms | ID=7a77da32-b9b... |
| 0.4 | Create HR User | OK | 1/1 | 2346ms | hr-test-1770806828@example.com |
| 0.5 | HR User Login | OK | 1/1 | 18874ms |  |

### Phase 1

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 1.1 | Upload hr-policy-test.md | OK | 1/1 | 1033ms | ID=a0c2cc85 |
| 1.2 | Upload 新增文件說明.md | OK | 1/1 | 643ms | ID=b91d33b1 |
| 1.3 | Upload 勞動契約書-謝雅玲.pdf | OK | 1/1 | 1050ms | ID=d2b680da |
| 1.4 | Upload 勞動契約書-謝雅玲.txt | OK | 1/1 | 547ms | ID=a3aa16fd |
| 1.5 | Upload 員工名冊.csv | OK | 1/1 | 615ms | ID=04eab0c6 |
| 1.6 | Upload 員工名冊.pdf | OK | 1/1 | 1024ms | ID=36d02520 |
| 1.7 | Upload 請假單範本-E012-周秀蘭.pdf | OK | 1/1 | 21991ms | ID=b22e3b92 |
| 1.8 | Upload 請假單範本-E012-周秀蘭.txt | OK | 1/1 | 1111ms | ID=b298624f |
| 1.9 | Upload 健康檢查報告-E016-高淑珍.pdf | OK | 1/1 | 33679ms | ID=c38068cd |
| 1.10 | Upload 健康檢查報告-E016-高淑珍.txt | OK | 1/1 | 38232ms | ID=370f660f |
| 1.11 | Upload 員工手冊-第一章-總則.md | OK | 1/1 | 3581ms | ID=937696ee |
| 1.12 | Upload 員工手冊-第一章-總則.pdf | OK | 1/1 | 1748ms | ID=5599b4d8 |
| 1.13 | Upload 獎懲管理辦法.md | OK | 1/1 | 774ms | ID=c3f1d1fd |
| 1.14 | Upload 獎懲管理辦法.pdf | OK | 1/1 | 50596ms | ID=f29fb3fb |
| 1.15 | Upload README.md | OK | 1/1 | 597ms | ID=7954d6fd |

### Phase 2

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| A1 | Q: 我們公司有交通津貼嗎？補助多少？ | OK | 4/4 | 1143ms | hits=3/3 ans=公司提供交通津貼，依通勤距離補貼 500-2,000 元。金額範圍依員工手冊規定辦理，實際補助以距離... |
| A2 | Q: 公司績效考核是一年幾次？ | OK | 4/4 | 27218ms | hits=3/3 ans=公司績效考核一年 2 次，分別在 6 月與 12 月各進行一次。此為公司內規規定的考核週期，詳見員工... |
| A3 | Q: 請問公司報帳有時間限制嗎？ | OK | 4/4 | 663ms | hits=1/3 ans=報帳需在費用發生後 30 日內完成，超過 30 日需填寫逾期報帳說明。超過 60 日不予核銷；代墊公... |
| A4 | Q: 新人到職第一天需要準備什麼？ | OK | 4/4 | 119815ms | hits=3/4 ans=根據目前的參考資料，並未明確提到新人到職第一天需要準備的具體事項。建議您諮詢 HR 部門以獲取詳細資... |
| A5 | Q: 公司的加班費怎麼算？ | FAIL | 0/4 | 180153ms | HTTP 0: HTTPConnectionPool(host='api.172-237-5-254.sslip.i |

### Phase 3

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| C1 | Q: 我們公司平日加班給 1.5 倍工資，這樣合法嗎？ | OK | 4/4 | 31108ms | hits=2/4 ans=公司平日加班給 1.5 倍，高於法定前 2 小時 1.34 倍，原則合法。但超過 2 小時仍需 1.... |
| C2 | Q: 員工特休沒休完，公司規定逾期視同放棄，這樣可以嗎？ | OK | 4/4 | 81265ms | hits=1/4 ans=根據公司內規，特休假未休畢可於次年度 3 月底前使用，逾期視同放棄的規定是存在的。然而，這樣的規定違... |
| C3 | Q: 全勤獎金因為員工請生理假被扣掉，合法嗎？ | FAIL | 0/4 | 180188ms | HTTP 0: HTTPConnectionPool(host='api.172-237-5-254.sslip.i |

### Phase 4

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| D1 | Q: 公司目前有多少位員工？ | FAIL | 0/4 | 180162ms | HTTP 0: HTTPConnectionPool(host='api.172-237-5-254.sslip.i |
| D2 | Q: 技術部的平均月薪是多少？ | OK | 4/4 | 30614ms | hits=3/3 ans=技術部平均月薪約 70,667 元（共 3 人平均）。計算使用員工名冊中所有該部門月薪欄位，已排除空... |

### Phase 5

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| E1 | Q: 如果明天有新人到職，我需要準備哪些流程和文件？ | FAIL | 0/4 | 180198ms | HTTP 0: HTTPConnectionPool(host='api.172-237-5-254.sslip.i |
| E2 | Q: 請幫我比較正職和約聘人員在福利上有什麼差異？ | OK | 4/4 | 39573ms | hits=4/4 ans=根據提供的參考資料，並未明確列出正職與約聘人員在福利上的具體差異。一般來說，正職員工和約聘人員在福利... |

### Phase 6

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 6.1 | List Documents | OK | 1/1 | 3406ms | 80 docs |
| 6.2 | Get Document Detail | OK | 1/1 | 1190ms |  |
| 6.3 | GET /users/me | OK | 1/1 | 1317ms | hr-test-1770806828@example.com |
| 6.4 | GET /audit/ | OK | 1/1 | 569ms |  |

### Phase 7

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| F1 | Follow: 承上題，如果這位員工年資未滿一年呢？ | OK | 4/4 | 138442ms | hits=3/3 |
| F2 | Follow: 那他可以申請育嬰假嗎？ | OK | 4/4 | 37359ms | hits=3/3 |

### Phase 8

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 8.1 | Chat Latency (5x avg) | OK | 0/0 | 60722ms | avg=60722ms min=42363ms max=75965ms |
| 8.2 | Health Latency (10x) | OK | 0/0 | 2467ms | avg=2467ms |
