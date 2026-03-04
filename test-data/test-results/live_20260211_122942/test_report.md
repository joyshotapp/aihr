# aihr Live E2E Test Report

**Server**: http://api.172-237-5-254.sslip.io
**Time**: 2026-02-11 12:41:33
**Duration**: 710.8s

## Summary

| Phase | Pass/Total | Score | % | Time |
|-------|-----------|-------|---|------|
| Phase 0 | 5/5 | 5/5 | 100% | 2.7s |
| Phase 1 | 15/15 | 15/15 | 100% | 10.6s |
| Phase 2 | 5/5 | 20/20 | 100% | 159.6s |
| Phase 3 | 2/3 | 5/12 | 45% | 107.1s |
| Phase 4 | 2/2 | 7/8 | 84% | 67.8s |
| Phase 5 | 2/2 | 6/8 | 80% | 93.5s |
| Phase 6 | 3/4 | 3/4 | 75% | 1.4s |
| Phase 7 | 2/2 | 8/8 | 100% | 60.6s |
| Phase 8 | 1/2 | 0/0 | N/A% | 30.4s |

**Total: 70/80 (86.9%) -- GOOD**

## Details

### Phase 0

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 0.1 | Health Check | OK | 1/1 | 554ms |  |
| 0.2 | Superuser Login | OK | 1/1 | 581ms | eyJhbGciOiJIUzI1NiIs... |
| 0.3 | Get Tenant | OK | 1/1 | 346ms | ID=b4539d8d-ea5... |
| 0.4 | Create HR User | OK | 1/1 | 636ms | hr-test-1770784184@example.com |
| 0.5 | HR User Login | OK | 1/1 | 550ms |  |

### Phase 1

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 1.1 | Upload hr-policy-test.md | OK | 1/1 | 809ms | ID=d1fc1705 |
| 1.2 | Upload 新增文件說明.md | OK | 1/1 | 358ms | ID=d586e602 |
| 1.3 | Upload 勞動契約書-謝雅玲.pdf | OK | 1/1 | 1603ms | ID=6896cd94 |
| 1.4 | Upload 勞動契約書-謝雅玲.txt | OK | 1/1 | 380ms | ID=41e515d6 |
| 1.5 | Upload 員工名冊.csv | OK | 1/1 | 292ms | ID=812b7261 |
| 1.6 | Upload 員工名冊.pdf | OK | 1/1 | 750ms | ID=cecd8365 |
| 1.7 | Upload 請假單範本-E012-周秀蘭.pdf | OK | 1/1 | 945ms | ID=cda81ddc |
| 1.8 | Upload 請假單範本-E012-周秀蘭.txt | OK | 1/1 | 302ms | ID=a24b4825 |
| 1.9 | Upload 健康檢查報告-E016-高淑珍.pdf | OK | 1/1 | 827ms | ID=bc6500a0 |
| 1.10 | Upload 健康檢查報告-E016-高淑珍.txt | OK | 1/1 | 355ms | ID=028137cb |
| 1.11 | Upload 員工手冊-第一章-總則.md | OK | 1/1 | 366ms | ID=e8d38d3a |
| 1.12 | Upload 員工手冊-第一章-總則.pdf | OK | 1/1 | 962ms | ID=05313990 |
| 1.13 | Upload 獎懲管理辦法.md | OK | 1/1 | 371ms | ID=5d6f35da |
| 1.14 | Upload 獎懲管理辦法.pdf | OK | 1/1 | 1878ms | ID=15439481 |
| 1.15 | Upload README.md | OK | 1/1 | 360ms | ID=0a463540 |

### Phase 2

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| A1 | Q: 我們公司有交通津貼嗎？補助多少？ | OK | 4/4 | 31423ms | hits=3/3 ans=### 交通津貼相關資訊

1. **交通津貼的存在性**
   - 根據提供的資料，交通津貼的發放... |
| A2 | Q: 公司績效考核是一年幾次？ | OK | 4/4 | 25637ms | hits=3/3 ans=### 績效考核的頻率

1. **考核頻率**
   - 根據《促進中高齡者及高齡者就業獎勵辦法》... |
| A3 | Q: 請問公司報帳有時間限制嗎？ | OK | 4/4 | 29133ms | hits=3/3 ans=### 公司報帳的時間限制

1. **報帳的時間限制**
   - 根據《勞動基準法》第30條，雇... |
| A4 | Q: 新人到職第一天需要準備什麼？ | OK | 4/4 | 35321ms | hits=4/4 ans=### 新人到職第一天需要準備的事項

1. **身份證明文件**
   - 準備身份證及其他必要的... |
| A5 | Q: 公司的加班費怎麼算？ | OK | 4/4 | 38081ms | hits=3/3 ans=### 加班費的計算方式

根據《勞動基準法》第24條的規定，加班費的計算方式如下：

1. **平... |

### Phase 3

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| C1 | Q: 我們公司平日加班給 1.5 倍工資，這樣合法嗎？ | OK | 2/4 | 47195ms | hits=2/4 ans=### 公司平日加班支付1.5倍工資的合法性

根據《勞動基準法》第24條的規定，平日加班的工資計算... |
| C2 | Q: 員工特休沒休完，公司規定逾期視同放棄，這樣可以嗎？ | WARN | 1/4 | 32371ms | hits=1/4 ans=### 員工特休未休完逾期視同放棄的合法性

根據《勞動基準法》第38條的規定，勞工在同一雇主或事業... |
| C3 | Q: 全勤獎金因為員工請生理假被扣掉，合法嗎？ | OK | 2/4 | 27535ms | hits=3/5 ans=### 全勤獎金因員工請生理假被扣除的合法性

根據《性別工作平等法》第14條及第21條的規定，女性... |

### Phase 4

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| D1 | Q: 公司目前有多少位員工？ | OK | 4/4 | 55275ms | hits=3/3 ans=抱歉，根據提供的參考資料，並未包含具體的公司員工人數資訊。因此，我無法直接回答您目前公司有多少位員工... |
| D2 | Q: 技術部的平均月薪是多少？ | OK | 3/4 | 12568ms | hits=2/3 ans=抱歉，根據提供的參考資料，並未包含技術部的平均月薪資訊。因此，我無法直接回答您技術部的平均月薪是多少... |

### Phase 5

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| E1 | Q: 如果明天有新人到職，我需要準備哪些流程和文件？ | OK | 2/4 | 41191ms | hits=3/5 ans=### 新人到職需要準備的流程和文件

為了確保新人到職的順利進行，您需要準備以下流程和文件：

#... |
| E2 | Q: 請幫我比較正職和約聘人員在福利上有什麼差異？ | OK | 4/4 | 52282ms | hits=4/4 ans=### 正職與約聘人員在福利上的差異比較

根據相關法律法規，正職與約聘人員在福利上存在以下主要差異... |

### Phase 6

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 6.1 | List Documents | OK | 1/1 | 500ms | 48 docs |
| 6.2 | Get Document Detail | OK | 1/1 | 282ms |  |
| 6.3 | GET /users/me | OK | 1/1 | 327ms | hr-test-1770784184@example.com |
| 6.4 | GET /audit/ | WARN | 0/1 | 292ms |  |

### Phase 7

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| F1 | Follow: 承上題，如果這位員工年資未滿一年呢？ | OK | 4/4 | 35830ms | hits=3/3 |
| F2 | Follow: 那他可以申請育嬰假嗎？ | OK | 4/4 | 24762ms | hits=3/3 |

### Phase 8

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 8.1 | Chat Latency (5x avg) | WARN | 0/0 | 30021ms | avg=30022ms min=27022ms max=35591ms |
| 8.2 | Health Latency (10x) | OK | 0/0 | 337ms | avg=338ms |
