# aihr Live E2E Test Report

**Server**: http://api.172-237-5-254.sslip.io
**Time**: 2026-02-11 17:54:28
**Duration**: 392.9s

## Summary

| Phase | Pass/Total | Score | % | Time |
|-------|-----------|-------|---|------|
| Phase 0 | 5/5 | 5/5 | 100% | 3.5s |
| Phase 1 | 5/15 | 5/15 | 33% | 8.5s |
| Phase 2 | 4/5 | 16/20 | 82% | 28.9s |
| Phase 3 | 1/3 | 5/12 | 38% | 25.3s |
| Phase 4 | 2/2 | 8/8 | 100% | 7.9s |
| Phase 5 | 2/2 | 6/8 | 80% | 57.3s |
| Phase 6 | 3/4 | 3/4 | 75% | 2.6s |
| Phase 7 | 2/2 | 8/8 | 100% | 84.4s |
| Phase 8 | 1/2 | 0/0 | N/A% | 27.6s |

**Total: 56/80 (70.4%) -- GOOD**

## Details

### Phase 0

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 0.1 | Health Check | OK | 1/1 | 286ms |  |
| 0.2 | Superuser Login | OK | 1/1 | 1000ms | eyJhbGciOiJIUzI1NiIs... |
| 0.3 | Get Tenant | OK | 1/1 | 484ms | ID=7a77da32-b9b... |
| 0.4 | Create HR User | OK | 1/1 | 900ms | hr-test-1770803277@example.com |
| 0.5 | HR User Login | OK | 1/1 | 843ms |  |

### Phase 1

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 1.1 | Upload hr-policy-test.md | OK | 1/1 | 525ms | ID=885f7c0e |
| 1.2 | Upload 新增文件說明.md | OK | 1/1 | 339ms | ID=6359cb19 |
| 1.3 | Upload 勞動契約書-謝雅玲.pdf | OK | 1/1 | 1121ms | ID=6f0f3f63 |
| 1.4 | Upload 勞動契約書-謝雅玲.txt | OK | 1/1 | 376ms | ID=db4846a3 |
| 1.5 | Upload 員工名冊.csv | OK | 1/1 | 322ms | ID=6f28190c |
| 1.6 | Upload 員工名冊.pdf | FAIL | 0/1 | 559ms | {'detail': {'error': 'quota_exceeded', 'message': '文件數量已達上限  |
| 1.7 | Upload 請假單範本-E012-周秀蘭.pdf | FAIL | 0/1 | 816ms | {'detail': {'error': 'quota_exceeded', 'message': '文件數量已達上限  |
| 1.8 | Upload 請假單範本-E012-周秀蘭.txt | FAIL | 0/1 | 289ms | {'detail': {'error': 'quota_exceeded', 'message': '文件數量已達上限  |
| 1.9 | Upload 健康檢查報告-E016-高淑珍.pdf | FAIL | 0/1 | 1041ms | {'detail': {'error': 'quota_exceeded', 'message': '文件數量已達上限  |
| 1.10 | Upload 健康檢查報告-E016-高淑珍.txt | FAIL | 0/1 | 347ms | {'detail': {'error': 'quota_exceeded', 'message': '文件數量已達上限  |
| 1.11 | Upload 員工手冊-第一章-總則.md | FAIL | 0/1 | 331ms | {'detail': {'error': 'quota_exceeded', 'message': '文件數量已達上限  |
| 1.12 | Upload 員工手冊-第一章-總則.pdf | FAIL | 0/1 | 870ms | {'detail': {'error': 'quota_exceeded', 'message': '文件數量已達上限  |
| 1.13 | Upload 獎懲管理辦法.md | FAIL | 0/1 | 284ms | {'detail': {'error': 'quota_exceeded', 'message': '文件數量已達上限  |
| 1.14 | Upload 獎懲管理辦法.pdf | FAIL | 0/1 | 876ms | {'detail': {'error': 'quota_exceeded', 'message': '文件數量已達上限  |
| 1.15 | Upload README.md | FAIL | 0/1 | 373ms | {'detail': {'error': 'quota_exceeded', 'message': '文件數量已達上限  |

### Phase 2

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| A1 | Q: 我們公司有交通津貼嗎？補助多少？ | OK | 4/4 | 437ms | hits=3/3 ans=公司提供交通津貼，依通勤距離補貼 500-2,000 元。金額範圍依員工手冊規定辦理，實際補助以距離... |
| A2 | Q: 公司績效考核是一年幾次？ | OK | 4/4 | 399ms | hits=3/3 ans=公司績效考核一年 2 次，分別在 6 月與 12 月各進行一次。此為公司內規規定的考核週期，詳見員工... |
| A3 | Q: 請問公司報帳有時間限制嗎？ | WARN | 1/4 | 503ms | hits=1/3 ans=報帳需在費用發生後 30 日內完成，超過 30 日需填寫逾期報帳說明。超過 60 日不予核銷；代墊公... |
| A4 | Q: 新人到職第一天需要準備什麼？ | OK | 3/4 | 14194ms | hits=3/4 ans=新人到職第一天需要準備以下文件：

1. **健康檢查報告**：
   - 包含完整的員工健檢項目，... |
| A5 | Q: 公司的加班費怎麼算？ | OK | 4/4 | 13407ms | hits=3/3 ans=### 加班費計算方式

根據公司內規，公司的加班費計算依照勞基法第 24 條規定，具體計算方式如下... |

### Phase 3

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| C1 | Q: 我們公司平日加班給 1.5 倍工資，這樣合法嗎？ | OK | 2/4 | 479ms | hits=2/4 ans=公司平日加班給 1.5 倍，高於法定前 2 小時 1.34 倍，原則合法。但超過 2 小時仍需 1.... |
| C2 | Q: 員工特休沒休完，公司規定逾期視同放棄，這樣可以嗎？ | WARN | 1/4 | 12846ms | hits=1/4 ans=### 員工特休逾期視同放棄的合法性

根據公司內規，特休假未休畢可於次年度 3 月底前使用，逾期視... |
| C3 | Q: 全勤獎金因為員工請生理假被扣掉，合法嗎？ | WARN | 2/4 | 11978ms | hits=2/5 ans=### 全勤獎金因生理假被扣的合法性

根據公司內規，女性員工每月可請 1 天生理假，且全年不扣全勤... |

### Phase 4

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| D1 | Q: 公司目前有多少位員工？ | OK | 4/4 | 7488ms | hits=3/3 ans=根據提供的參考資料，並未包含有關公司目前員工人數的具體資訊。因此，我無法回答您關於公司目前有多少位員... |
| D2 | Q: 技術部的平均月薪是多少？ | OK | 4/4 | 429ms | hits=3/3 ans=技術部平均月薪約 59,833 元（共 6 人平均）。計算使用員工名冊中所有該部門月薪欄位，已排除空... |

### Phase 5

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| E1 | Q: 如果明天有新人到職，我需要準備哪些流程和文件？ | OK | 2/4 | 40673ms | hits=3/5 ans=### 新人到職需準備的流程和文件

根據公司內規，以下是新人到職時需要準備的流程和文件：

1. ... |
| E2 | Q: 請幫我比較正職和約聘人員在福利上有什麼差異？ | OK | 4/4 | 16631ms | hits=4/4 ans=### 正職與約聘人員在福利上的差異

根據公司內規，以下是正職與約聘人員在福利上的主要差異：

1... |

### Phase 6

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 6.1 | List Documents | OK | 1/1 | 705ms | 20 docs |
| 6.2 | Get Document Detail | OK | 1/1 | 974ms |  |
| 6.3 | GET /users/me | OK | 1/1 | 499ms | hr-test-1770803277@example.com |
| 6.4 | GET /audit/ | WARN | 0/1 | 472ms |  |

### Phase 7

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| F1 | Follow: 承上題，如果這位員工年資未滿一年呢？ | OK | 4/4 | 55390ms | hits=3/3 |
| F2 | Follow: 那他可以申請育嬰假嗎？ | OK | 4/4 | 29058ms | hits=3/3 |

### Phase 8

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 8.1 | Chat Latency (5x avg) | WARN | 0/0 | 27236ms | avg=27236ms min=12130ms max=52921ms |
| 8.2 | Health Latency (10x) | OK | 0/0 | 360ms | avg=360ms |
