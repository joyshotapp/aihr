# aihr Live E2E Test Report

**Server**: http://api.172-237-5-254.sslip.io
**Time**: 2026-02-12 09:47:39
**Duration**: 2406.0s

## Summary

| Phase | Pass/Total | Score | % | Time |
|-------|-----------|-------|---|------|
| Phase 0 | 5/5 | 5/5 | 100% | 4.2s |
| Phase 1 | 15/15 | 15/15 | 100% | 8.7s |
| Phase 2 | 5/5 | 20/20 | 100% | 223.0s |
| Phase 3 | 3/3 | 12/12 | 100% | 199.7s |
| Phase 4 | 2/2 | 8/8 | 100% | 57.6s |
| Phase 5 | 1/2 | 4/8 | 50% | 145.8s |
| Phase 6 | 4/4 | 4/4 | 100% | 1.9s |
| Phase 7 | 2/2 | 8/8 | 100% | 119.7s |
| Phase 8 | 2/2 | 0/0 | N/A% | 112.5s |

**Total: 76/80 (95.0%) -- EXCELLENT**

## Details

### Phase 0

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 0.1 | Health Check | OK | 1/1 | 1146ms |  |
| 0.2 | Superuser Login | OK | 1/1 | 1026ms | eyJhbGciOiJIUzI1NiIs... |
| 0.3 | Get Tenant | OK | 1/1 | 373ms | ID=7a77da32-b9b... |
| 0.4 | Create HR User | OK | 1/1 | 833ms | hr-test-1770858455@example.com |
| 0.5 | HR User Login | OK | 1/1 | 804ms |  |

### Phase 1

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 1.1 | Upload hr-policy-test.md | OK | 1/1 | 504ms | ID=0776fc73 |
| 1.2 | Upload 新增文件說明.md | OK | 1/1 | 294ms | ID=9f9a825e |
| 1.3 | Upload 勞動契約書-謝雅玲.pdf | OK | 1/1 | 1144ms | ID=f288c971 |
| 1.4 | Upload 勞動契約書-謝雅玲.txt | OK | 1/1 | 296ms | ID=86e6640d |
| 1.5 | Upload 員工名冊.csv | OK | 1/1 | 375ms | ID=88b2bb75 |
| 1.6 | Upload 員工名冊.pdf | OK | 1/1 | 758ms | ID=a5537c5f |
| 1.7 | Upload 請假單範本-E012-周秀蘭.pdf | OK | 1/1 | 801ms | ID=3f29bb10 |
| 1.8 | Upload 請假單範本-E012-周秀蘭.txt | OK | 1/1 | 418ms | ID=33295d83 |
| 1.9 | Upload 健康檢查報告-E016-高淑珍.pdf | OK | 1/1 | 1085ms | ID=6ffc86fe |
| 1.10 | Upload 健康檢查報告-E016-高淑珍.txt | OK | 1/1 | 356ms | ID=dc1ed335 |
| 1.11 | Upload 員工手冊-第一章-總則.md | OK | 1/1 | 322ms | ID=00470b3a |
| 1.12 | Upload 員工手冊-第一章-總則.pdf | OK | 1/1 | 836ms | ID=08632142 |
| 1.13 | Upload 獎懲管理辦法.md | OK | 1/1 | 367ms | ID=ab9823f8 |
| 1.14 | Upload 獎懲管理辦法.pdf | OK | 1/1 | 746ms | ID=67796e6e |
| 1.15 | Upload README.md | OK | 1/1 | 390ms | ID=0ae61849 |

### Phase 2

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| A1 | Q: 我們公司有交通津貼嗎？補助多少？ | OK | 4/4 | 907ms | hits=3/3 ans=公司提供交通津貼，依通勤距離補貼 500-2,000 元。金額範圍依員工手冊規定辦理，實際補助以距離... |
| A2 | Q: 公司績效考核是一年幾次？ | OK | 4/4 | 758ms | hits=3/3 ans=公司績效考核一年 2 次，分別在 6 月與 12 月各進行一次。此為公司內規規定的考核週期，詳見員工... |
| A3 | Q: 請問公司報帳有時間限制嗎？ | OK | 4/4 | 49884ms | hits=1/3 ans=報帳需在費用發生後 30 日內完成，超過 30 日需填寫逾期報帳說明。超過 60 日不予核銷；代墊公... |
| A4 | Q: 新人到職第一天需要準備什麼？ | OK | 4/4 | 72828ms | hits=4/4 ans=根據目前的參考資料，關於新人到職第一天需要準備的事項並未明確列出。建議您可以諮詢 HR 部門以獲取具... |
| A5 | Q: 公司的加班費怎麼算？ | OK | 4/4 | 98653ms | hits=3/3 ans=### 公司的加班費計算方式

根據公司內規，公司的加班費計算如下：

| 加班類型        ... |

### Phase 3

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| C1 | Q: 我們公司平日加班給 1.5 倍工資，這樣合法嗎？ | OK | 4/4 | 1974ms | hits=2/4 ans=公司平日加班給 1.5 倍，高於法定前 2 小時 1.34 倍，原則合法。但超過 2 小時仍需 1.... |
| C2 | Q: 員工特休沒休完，公司規定逾期視同放棄，這樣可以嗎？ | OK | 4/4 | 107563ms | hits=1/4 ans=### 員工特休逾期視同放棄的合法性

根據公司內規，特休假未休畢可於次年度 3 月底前使用，逾期視... |
| C3 | Q: 全勤獎金因為員工請生理假被扣掉，合法嗎？ | OK | 4/4 | 90129ms | hits=2/5 ans=### 全勤獎金因請生理假被扣的合法性

根據公司內規，女性員工每月可請 1 天生理假，且全年不扣全... |

### Phase 4

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| D1 | Q: 公司目前有多少位員工？ | OK | 4/4 | 56567ms | hits=2/3 ans=抱歉，根據提供的參考資料，我無法得知公司目前的員工人數。建議您諮詢人資部門以獲取準確的員工人數資訊。... |
| D2 | Q: 技術部的平均月薪是多少？ | OK | 4/4 | 1003ms | hits=3/3 ans=技術部平均月薪約 70,667 元（共 3 人平均）。計算使用員工名冊中所有該部門月薪欄位，已排除空... |

### Phase 5

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| E1 | Q: 如果明天有新人到職，我需要準備哪些流程和文件？ | FAIL | 0/4 | 92980ms | HTTP 502: <html>
<head><title>502 Bad Gateway</title></head |
| E2 | Q: 請幫我比較正職和約聘人員在福利上有什麼差異？ | OK | 4/4 | 52865ms | hits=4/4 ans=### 正職與約聘人員在福利上的差異

根據提供的參考資料，無法直接得知正職與約聘人員在福利上的具體... |

### Phase 6

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 6.1 | List Documents | OK | 1/1 | 747ms | 100 docs |
| 6.2 | Get Document Detail | OK | 1/1 | 420ms |  |
| 6.3 | GET /users/me | OK | 1/1 | 387ms | hr-test-1770858455@example.com |
| 6.4 | GET /audit/ | OK | 1/1 | 347ms |  |

### Phase 7

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| F1 | Follow: 承上題，如果這位員工年資未滿一年呢？ | OK | 4/4 | 49253ms | hits=3/3 |
| F2 | Follow: 那他可以申請育嬰假嗎？ | OK | 4/4 | 70468ms | hits=3/3 |

### Phase 8

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 8.1 | Chat Latency (5x avg) | OK | 0/0 | 112038ms | avg=112038ms min=54968ms max=164507ms |
| 8.2 | Health Latency (10x) | OK | 0/0 | 483ms | avg=484ms |
