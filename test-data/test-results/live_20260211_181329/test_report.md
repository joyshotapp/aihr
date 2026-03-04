# aihr Live E2E Test Report

**Server**: http://api.172-237-5-254.sslip.io
**Time**: 2026-02-11 18:23:06
**Duration**: 576.5s

## Summary

| Phase | Pass/Total | Score | % | Time |
|-------|-----------|-------|---|------|
| Phase 0 | 3/4 | 3/4 | 75% | 30.0s |
| Phase 1 | 15/15 | 15/15 | 100% | 11.8s |
| Phase 2 | 3/5 | 12/20 | 60% | 85.0s |
| Phase 3 | 3/3 | 12/12 | 100% | 98.2s |
| Phase 4 | 2/2 | 8/8 | 100% | 11.0s |
| Phase 5 | 1/2 | 4/8 | 50% | 40.2s |
| Phase 6 | 3/4 | 3/4 | 75% | 14.1s |
| Phase 7 | 1/2 | 4/8 | 50% | 104.6s |
| Phase 8 | 2/2 | 0/0 | N/A% | 33.9s |

**Total: 61/79 (77.2%) -- GOOD**

## Details

### Phase 0

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 0.1 | Health Check | OK | 1/1 | 536ms |  |
| 0.2 | Superuser Login | OK | 1/1 | 1607ms | eyJhbGciOiJIUzI1NiIs... |
| 0.3 | Get Tenant | OK | 1/1 | 14960ms | ID=7a77da32-b9b... |
| 0.4 | Create HR User | FAIL | 0/1 | 12923ms | {'_text': '<html>\r\n<head><title>502 Bad Gateway</title></head>\r\n<body>\r\n<c |

### Phase 1

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 1.1 | Upload hr-policy-test.md | OK | 1/1 | 1137ms | ID=5075a344 |
| 1.2 | Upload 新增文件說明.md | OK | 1/1 | 402ms | ID=f03d81a3 |
| 1.3 | Upload 勞動契約書-謝雅玲.pdf | OK | 1/1 | 1175ms | ID=b5ef7d82 |
| 1.4 | Upload 勞動契約書-謝雅玲.txt | OK | 1/1 | 727ms | ID=06afec32 |
| 1.5 | Upload 員工名冊.csv | OK | 1/1 | 379ms | ID=0ea42382 |
| 1.6 | Upload 員工名冊.pdf | OK | 1/1 | 713ms | ID=78dadb6b |
| 1.7 | Upload 請假單範本-E012-周秀蘭.pdf | OK | 1/1 | 863ms | ID=d9b4035d |
| 1.8 | Upload 請假單範本-E012-周秀蘭.txt | OK | 1/1 | 945ms | ID=4ca83a07 |
| 1.9 | Upload 健康檢查報告-E016-高淑珍.pdf | OK | 1/1 | 2220ms | ID=b786555c |
| 1.10 | Upload 健康檢查報告-E016-高淑珍.txt | OK | 1/1 | 621ms | ID=e249a84f |
| 1.11 | Upload 員工手冊-第一章-總則.md | OK | 1/1 | 405ms | ID=ce0dc49a |
| 1.12 | Upload 員工手冊-第一章-總則.pdf | OK | 1/1 | 770ms | ID=1a447851 |
| 1.13 | Upload 獎懲管理辦法.md | OK | 1/1 | 334ms | ID=e4f8084c |
| 1.14 | Upload 獎懲管理辦法.pdf | OK | 1/1 | 702ms | ID=6747908c |
| 1.15 | Upload README.md | OK | 1/1 | 399ms | ID=f746fefc |

### Phase 2

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| A1 | Q: 我們公司有交通津貼嗎？補助多少？ | OK | 4/4 | 575ms | hits=3/3 ans=公司提供交通津貼，依通勤距離補貼 500-2,000 元。金額範圍依員工手冊規定辦理，實際補助以距離... |
| A2 | Q: 公司績效考核是一年幾次？ | OK | 4/4 | 386ms | hits=3/3 ans=公司績效考核一年 2 次，分別在 6 月與 12 月各進行一次。此為公司內規規定的考核週期，詳見員工... |
| A3 | Q: 請問公司報帳有時間限制嗎？ | OK | 4/4 | 435ms | hits=1/3 ans=報帳需在費用發生後 30 日內完成，超過 30 日需填寫逾期報帳說明。超過 60 日不予核銷；代墊公... |
| A4 | Q: 新人到職第一天需要準備什麼？ | FAIL | 0/4 | 23063ms | HTTP 502: <html>
<head><title>502 Bad Gateway</title></head |
| A5 | Q: 公司的加班費怎麼算？ | FAIL | 0/4 | 60518ms | HTTP 504: <html>
<head><title>504 Gateway Time-out</title>< |

### Phase 3

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| C1 | Q: 我們公司平日加班給 1.5 倍工資，這樣合法嗎？ | OK | 4/4 | 1726ms | hits=2/4 ans=公司平日加班給 1.5 倍，高於法定前 2 小時 1.34 倍，原則合法。但超過 2 小時仍需 1.... |
| C2 | Q: 員工特休沒休完，公司規定逾期視同放棄，這樣可以嗎？ | OK | 4/4 | 51643ms | hits=1/4 ans=根據公司內規，特休假（年假）未休畢可於次年度 3 月底前使用，逾期視同放棄的規定存在問題。這樣的規定... |
| C3 | Q: 全勤獎金因為員工請生理假被扣掉，合法嗎？ | OK | 4/4 | 44813ms | hits=2/5 ans=根據公司內規，女性員工每月可請 1 天生理假，且全年不扣全勤獎金 3 天。因此，若因為請生理假而扣掉... |

### Phase 4

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| D1 | Q: 公司目前有多少位員工？ | OK | 4/4 | 10352ms | hits=3/3 ans=根據提供的參考資料，無法得知公司目前有多少位員工。建議您諮詢 HR 部門以獲取準確的員工人數資訊。
... |
| D2 | Q: 技術部的平均月薪是多少？ | OK | 4/4 | 622ms | hits=3/3 ans=技術部平均月薪約 70,667 元（共 3 人平均）。計算使用員工名冊中所有該部門月薪欄位，已排除空... |

### Phase 5

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| E1 | Q: 如果明天有新人到職，我需要準備哪些流程和文件？ | FAIL | 0/4 | 24286ms | HTTP 502: <html>
<head><title>502 Bad Gateway</title></head |
| E2 | Q: 請幫我比較正職和約聘人員在福利上有什麼差異？ | OK | 4/4 | 15917ms | hits=1/4 ans=若明天有新人到職，您需要準備的流程和文件如下：

### 準備流程
1. **入職前準備**
   ... |

### Phase 6

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 6.1 | List Documents | OK | 1/1 | 12794ms | 50 docs |
| 6.2 | Get Document Detail | OK | 1/1 | 513ms |  |
| 6.3 | GET /users/me | OK | 1/1 | 412ms | admin@example.com |
| 6.4 | GET /audit/ | FAIL | 0/1 | 331ms |  |

### Phase 7

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| F1 | Follow: 承上題，如果這位員工年資未滿一年呢？ | OK | 4/4 | 44131ms | hits=2/3 |
| F2 | Follow: 那他可以申請育嬰假嗎？ | FAIL | 0/4 | 60486ms | HTTP 504 |

### Phase 8

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 8.1 | Chat Latency (5x avg) | OK | 0/0 | 33573ms | avg=33574ms min=20142ms max=41968ms |
| 8.2 | Health Latency (10x) | OK | 0/0 | 347ms | avg=347ms |
