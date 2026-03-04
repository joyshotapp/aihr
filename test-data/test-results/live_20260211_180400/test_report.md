# aihr Live E2E Test Report

**Server**: http://api.172-237-5-254.sslip.io
**Time**: 2026-02-11 18:13:26
**Duration**: 566.5s

## Summary

| Phase | Pass/Total | Score | % | Time |
|-------|-----------|-------|---|------|
| Phase 0 | 5/5 | 5/5 | 100% | 43.0s |
| Phase 1 | 15/15 | 15/15 | 100% | 11.1s |
| Phase 2 | 4/5 | 16/20 | 80% | 31.1s |
| Phase 3 | 2/3 | 8/12 | 67% | 78.1s |
| Phase 4 | 2/2 | 8/8 | 100% | 25.2s |
| Phase 5 | 1/2 | 4/8 | 50% | 44.9s |
| Phase 6 | 3/4 | 3/4 | 75% | 1.8s |
| Phase 7 | 1/2 | 4/8 | 50% | 64.2s |
| Phase 8 | 2/2 | 0/0 | N/A% | 37.6s |

**Total: 63/80 (78.8%) -- GOOD**

## Details

### Phase 0

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 0.1 | Health Check | OK | 1/1 | 37423ms |  |
| 0.2 | Superuser Login | OK | 1/1 | 2203ms | eyJhbGciOiJIUzI1NiIs... |
| 0.3 | Get Tenant | OK | 1/1 | 459ms | ID=7a77da32-b9b... |
| 0.4 | Create HR User | OK | 1/1 | 1368ms | hr-test-1770804280@example.com |
| 0.5 | HR User Login | OK | 1/1 | 1564ms |  |

### Phase 1

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 1.1 | Upload hr-policy-test.md | OK | 1/1 | 930ms | ID=1ebe9d69 |
| 1.2 | Upload 新增文件說明.md | OK | 1/1 | 394ms | ID=548bec39 |
| 1.3 | Upload 勞動契約書-謝雅玲.pdf | OK | 1/1 | 1849ms | ID=7ec16840 |
| 1.4 | Upload 勞動契約書-謝雅玲.txt | OK | 1/1 | 864ms | ID=245da9e9 |
| 1.5 | Upload 員工名冊.csv | OK | 1/1 | 467ms | ID=fe25b372 |
| 1.6 | Upload 員工名冊.pdf | OK | 1/1 | 722ms | ID=b63b4387 |
| 1.7 | Upload 請假單範本-E012-周秀蘭.pdf | OK | 1/1 | 1195ms | ID=e668bfe3 |
| 1.8 | Upload 請假單範本-E012-周秀蘭.txt | OK | 1/1 | 426ms | ID=839935bc |
| 1.9 | Upload 健康檢查報告-E016-高淑珍.pdf | OK | 1/1 | 1089ms | ID=31a5434f |
| 1.10 | Upload 健康檢查報告-E016-高淑珍.txt | OK | 1/1 | 403ms | ID=c6a6e7d0 |
| 1.11 | Upload 員工手冊-第一章-總則.md | OK | 1/1 | 319ms | ID=a44f26e8 |
| 1.12 | Upload 員工手冊-第一章-總則.pdf | OK | 1/1 | 748ms | ID=ff63ca4a |
| 1.13 | Upload 獎懲管理辦法.md | OK | 1/1 | 444ms | ID=58feffc8 |
| 1.14 | Upload 獎懲管理辦法.pdf | OK | 1/1 | 866ms | ID=da55dc14 |
| 1.15 | Upload README.md | OK | 1/1 | 387ms | ID=fbfdbfb8 |

### Phase 2

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| A1 | Q: 我們公司有交通津貼嗎？補助多少？ | OK | 4/4 | 539ms | hits=3/3 ans=公司提供交通津貼，依通勤距離補貼 500-2,000 元。金額範圍依員工手冊規定辦理，實際補助以距離... |
| A2 | Q: 公司績效考核是一年幾次？ | OK | 4/4 | 352ms | hits=3/3 ans=公司績效考核一年 2 次，分別在 6 月與 12 月各進行一次。此為公司內規規定的考核週期，詳見員工... |
| A3 | Q: 請問公司報帳有時間限制嗎？ | OK | 4/4 | 542ms | hits=1/3 ans=報帳需在費用發生後 30 日內完成，超過 30 日需填寫逾期報帳說明。超過 60 日不予核銷；代墊公... |
| A4 | Q: 新人到職第一天需要準備什麼？ | FAIL | 0/4 | 12918ms | HTTP 502: <html>
<head><title>502 Bad Gateway</title></head |
| A5 | Q: 公司的加班費怎麼算？ | OK | 4/4 | 16745ms | hits=3/3 ans=### 新人到職第一天需要準備的事項
新人到職第一天需要準備以下事項：
1. **身份證明文件**：... |

### Phase 3

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| C1 | Q: 我們公司平日加班給 1.5 倍工資，這樣合法嗎？ | OK | 4/4 | 758ms | hits=2/4 ans=公司平日加班給 1.5 倍，高於法定前 2 小時 1.34 倍，原則合法。但超過 2 小時仍需 1.... |
| C2 | Q: 員工特休沒休完，公司規定逾期視同放棄，這樣可以嗎？ | FAIL | 0/4 | 37958ms | HTTP 502: <html>
<head><title>502 Bad Gateway</title></head |
| C3 | Q: 全勤獎金因為員工請生理假被扣掉，合法嗎？ | OK | 4/4 | 39403ms | hits=1/5 ans=### 員工特休逾期視同放棄的合法性
根據勞動法規，員工的特休假不得隨意視同放棄。若公司規定逾期視同... |

### Phase 4

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| D1 | Q: 公司目前有多少位員工？ | OK | 4/4 | 24002ms | hits=3/3 ans=根據提供的參考資料，並未明確提及公司目前有多少位員工。因此，我無法回答此問題。建議您諮詢 HR 部門... |
| D2 | Q: 技術部的平均月薪是多少？ | OK | 4/4 | 1168ms | hits=3/3 ans=技術部平均月薪約 70,667 元（共 3 人平均）。計算使用員工名冊中所有該部門月薪欄位，已排除空... |

### Phase 5

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| E1 | Q: 如果明天有新人到職，我需要準備哪些流程和文件？ | OK | 4/4 | 18218ms | hits=3/5 ans=### 新人到職需要準備的流程和文件
根據公司內規，若明天有新人到職，需準備以下流程和文件：

1.... |
| E2 | Q: 請幫我比較正職和約聘人員在福利上有什麼差異？ | FAIL | 0/4 | 26707ms | HTTP 502: <html>
<head><title>502 Bad Gateway</title></head |

### Phase 6

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 6.1 | List Documents | OK | 1/1 | 738ms | 35 docs |
| 6.2 | Get Document Detail | OK | 1/1 | 412ms |  |
| 6.3 | GET /users/me | OK | 1/1 | 318ms | hr-test-1770804280@example.com |
| 6.4 | GET /audit/ | FAIL | 0/1 | 371ms |  |

### Phase 7

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| F1 | Follow: 承上題，如果這位員工年資未滿一年呢？ | OK | 4/4 | 14692ms | hits=3/3 |
| F2 | Follow: 那他可以申請育嬰假嗎？ | FAIL | 0/4 | 49520ms | HTTP 502 |

### Phase 8

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 8.1 | Chat Latency (5x avg) | OK | 0/0 | 37280ms | avg=37280ms min=35955ms max=38605ms |
| 8.2 | Health Latency (10x) | OK | 0/0 | 343ms | avg=343ms |
