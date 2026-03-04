# aihr Live E2E Test Report

**Server**: http://api.172-237-5-254.sslip.io
**Time**: 2026-02-12 02:42:08
**Duration**: 2642.7s

## Summary

| Phase | Pass/Total | Score | % | Time |
|-------|-----------|-------|---|------|
| Phase 0 | 5/5 | 5/5 | 100% | 80.4s |
| Phase 1 | 14/15 | 14/15 | 93% | 128.2s |
| Phase 2 | 3/5 | 12/20 | 60% | 401.3s |
| Phase 3 | 3/3 | 12/12 | 100% | 231.7s |
| Phase 4 | 2/2 | 8/8 | 100% | 167.2s |
| Phase 5 | 0/2 | 0/8 | 0% | 94.9s |
| Phase 6 | 4/4 | 4/4 | 100% | 40.8s |
| Phase 7 | 0/2 | 0/8 | 0% | 360.6s |
| Phase 8 | 2/2 | 0/0 | N/A% | 89.8s |

**Total: 55/80 (68.8%) -- FAIR**

## Details

### Phase 0

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 0.1 | Health Check | OK | 1/1 | 410ms |  |
| 0.2 | Superuser Login | OK | 1/1 | 2077ms | eyJhbGciOiJIUzI1NiIs... |
| 0.3 | Get Tenant | OK | 1/1 | 21792ms | ID=7a77da32-b9b... |
| 0.4 | Create HR User | OK | 1/1 | 54136ms | hr-test-1770832709@example.com |
| 0.5 | HR User Login | OK | 1/1 | 1985ms |  |

### Phase 1

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 1.1 | Upload hr-policy-test.md | OK | 1/1 | 1211ms | ID=ff52103d |
| 1.2 | Upload 新增文件說明.md | OK | 1/1 | 900ms | ID=e890380b |
| 1.3 | Upload 勞動契約書-謝雅玲.pdf | OK | 1/1 | 1217ms | ID=33e0e9e4 |
| 1.4 | Upload 勞動契約書-謝雅玲.txt | OK | 1/1 | 391ms | ID=fa68d41c |
| 1.5 | Upload 員工名冊.csv | OK | 1/1 | 1596ms | ID=8ce979a2 |
| 1.6 | Upload 員工名冊.pdf | FAIL | 0/1 | 47195ms | {'_text': '<html>\r\n<head><title>502 Bad Gateway</title></h |
| 1.7 | Upload 請假單範本-E012-周秀蘭.pdf | OK | 1/1 | 988ms | ID=aba2f509 |
| 1.8 | Upload 請假單範本-E012-周秀蘭.txt | OK | 1/1 | 528ms | ID=b484d42e |
| 1.9 | Upload 健康檢查報告-E016-高淑珍.pdf | OK | 1/1 | 1323ms | ID=c63cca1c |
| 1.10 | Upload 健康檢查報告-E016-高淑珍.txt | OK | 1/1 | 391ms | ID=7cd62ccf |
| 1.11 | Upload 員工手冊-第一章-總則.md | OK | 1/1 | 474ms | ID=98bc7a31 |
| 1.12 | Upload 員工手冊-第一章-總則.pdf | OK | 1/1 | 1599ms | ID=3ea58e92 |
| 1.13 | Upload 獎懲管理辦法.md | OK | 1/1 | 562ms | ID=df2fca0e |
| 1.14 | Upload 獎懲管理辦法.pdf | OK | 1/1 | 69349ms | ID=c21b2421 |
| 1.15 | Upload README.md | OK | 1/1 | 488ms | ID=d48ecaa1 |

### Phase 2

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| A1 | Q: 我們公司有交通津貼嗎？補助多少？ | OK | 4/4 | 1174ms | hits=3/3 ans=公司提供交通津貼，依通勤距離補貼 500-2,000 元。金額範圍依員工手冊規定辦理，實際補助以距離... |
| A2 | Q: 公司績效考核是一年幾次？ | OK | 4/4 | 20464ms | hits=3/3 ans=公司績效考核一年 2 次，分別在 6 月與 12 月各進行一次。此為公司內規規定的考核週期，詳見員工... |
| A3 | Q: 請問公司報帳有時間限制嗎？ | OK | 4/4 | 19251ms | hits=1/3 ans=報帳需在費用發生後 30 日內完成，超過 30 日需填寫逾期報帳說明。超過 60 日不予核銷；代墊公... |
| A4 | Q: 新人到職第一天需要準備什麼？ | FAIL | 0/4 | 180182ms | HTTP 0: HTTPConnectionPool(host='api.172-237-5-254.sslip.i |
| A5 | Q: 公司的加班費怎麼算？ | FAIL | 0/4 | 180198ms | HTTP 0: HTTPConnectionPool(host='api.172-237-5-254.sslip.i |

### Phase 3

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| C1 | Q: 我們公司平日加班給 1.5 倍工資，這樣合法嗎？ | OK | 4/4 | 5871ms | hits=2/4 ans=公司平日加班給 1.5 倍，高於法定前 2 小時 1.34 倍，原則合法。但超過 2 小時仍需 1.... |
| C2 | Q: 員工特休沒休完，公司規定逾期視同放棄，這樣可以嗎？ | OK | 4/4 | 110439ms | hits=1/4 ans=### 員工特休逾期視同放棄的合法性

根據公司內規的規定，未休畢之特休可於次年度 3 月底前使用，... |
| C3 | Q: 全勤獎金因為員工請生理假被扣掉，合法嗎？ | OK | 4/4 | 115363ms | hits=2/5 ans=### 全勤獎金扣除的合法性

根據公司內規第 5.6 條的規定，女性員工每月可請 1 天生理假，且... |

### Phase 4

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| D1 | Q: 公司目前有多少位員工？ | OK | 4/4 | 166492ms | hits=3/3 ans=根據提供的參考資料，並未包含有關公司目前員工人數的具體資訊。因此，無法回答公司目前有多少位員工的問題... |
| D2 | Q: 技術部的平均月薪是多少？ | OK | 4/4 | 669ms | hits=3/3 ans=技術部平均月薪約 59,833 元（共 6 人平均）。計算使用員工名冊中所有該部門月薪欄位，已排除空... |

### Phase 5

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| E1 | Q: 如果明天有新人到職，我需要準備哪些流程和文件？ | FAIL | 0/4 | 73582ms | HTTP 502: <html>
<head><title>502 Bad Gateway</title></head |
| E2 | Q: 請幫我比較正職和約聘人員在福利上有什麼差異？ | FAIL | 0/4 | 21292ms | HTTP 502: <html>
<head><title>502 Bad Gateway</title></head |

### Phase 6

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 6.1 | List Documents | OK | 1/1 | 39428ms | 94 docs |
| 6.2 | Get Document Detail | OK | 1/1 | 568ms |  |
| 6.3 | GET /users/me | OK | 1/1 | 408ms | hr-test-1770832709@example.com |
| 6.4 | GET /audit/ | OK | 1/1 | 436ms |  |

### Phase 7

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| F1 | Follow: 承上題，如果這位員工年資未滿一年呢？ | FAIL | 0/4 | 180198ms | HTTP 0 |
| F2 | Follow: 那他可以申請育嬰假嗎？ | FAIL | 0/4 | 180402ms | HTTP 0 |

### Phase 8

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 8.1 | Chat Latency (5x avg) | OK | 0/0 | 84374ms | avg=84374ms min=46263ms max=122486ms |
| 8.2 | Health Latency (10x) | OK | 0/0 | 5390ms | avg=5390ms |
