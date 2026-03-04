# aihr Live E2E Test Report

**Server**: http://api.172-237-5-254.sslip.io
**Time**: 2026-02-11 11:52:49
**Duration**: 45.4s

## Summary

| Phase | Pass/Total | Score | % | Time |
|-------|-----------|-------|---|------|
| Phase 0 | 3/4 | 3/4 | 75% | 1.6s |
| Phase 1 | 0/15 | 0/15 | 0% | 10.9s |
| Phase 2 | 0/5 | 0/20 | 0% | 2.0s |
| Phase 3 | 0/3 | 0/12 | 0% | 1.2s |
| Phase 4 | 0/2 | 0/8 | 0% | 0.7s |
| Phase 5 | 0/2 | 0/8 | 0% | 0.8s |
| Phase 6 | 0/3 | 0/3 | 0% | 1.2s |
| Phase 8 | 1/1 | 0/0 | N/A% | 0.3s |

**Total: 3/70 (4.3%) -- NEEDS WORK**

## Details

### Phase 0

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 0.1 | Health Check | OK | 1/1 | 338ms |  |
| 0.2 | Superuser Login | OK | 1/1 | 603ms | eyJhbGciOiJIUzI1NiIs... |
| 0.3 | Get Tenant | OK | 1/1 | 346ms | ID=b4539d8d-ea5... |
| 0.4 | Create HR User | FAIL | 0/1 | 283ms | {'detail': [{'type': 'value_error', 'loc': ['body', 'email'], 'msg': 'value is n |

### Phase 1

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 1.1 | Upload hr-policy-test.md | FAIL | 0/1 | 402ms | {'_text': 'Internal Server Error'} |
| 1.2 | Upload 新增文件說明.md | FAIL | 0/1 | 420ms | {'_text': 'Internal Server Error'} |
| 1.3 | Upload 勞動契約書-謝雅玲.pdf | FAIL | 0/1 | 2289ms | {'_text': 'Internal Server Error'} |
| 1.4 | Upload 勞動契約書-謝雅玲.txt | FAIL | 0/1 | 355ms | {'_text': 'Internal Server Error'} |
| 1.5 | Upload 員工名冊.csv | FAIL | 0/1 | 296ms | {'_text': 'Internal Server Error'} |
| 1.6 | Upload 員工名冊.pdf | FAIL | 0/1 | 616ms | {'_text': 'Internal Server Error'} |
| 1.7 | Upload 請假單範本-E012-周秀蘭.pdf | FAIL | 0/1 | 917ms | {'_text': 'Internal Server Error'} |
| 1.8 | Upload 請假單範本-E012-周秀蘭.txt | FAIL | 0/1 | 377ms | {'_text': 'Internal Server Error'} |
| 1.9 | Upload 健康檢查報告-E016-高淑珍.pdf | FAIL | 0/1 | 985ms | {'_text': 'Internal Server Error'} |
| 1.10 | Upload 健康檢查報告-E016-高淑珍.txt | FAIL | 0/1 | 382ms | {'_text': 'Internal Server Error'} |
| 1.11 | Upload 員工手冊-第一章-總則.md | FAIL | 0/1 | 477ms | {'_text': 'Internal Server Error'} |
| 1.12 | Upload 員工手冊-第一章-總則.pdf | FAIL | 0/1 | 1743ms | {'_text': 'Internal Server Error'} |
| 1.13 | Upload 獎懲管理辦法.md | FAIL | 0/1 | 313ms | {'_text': 'Internal Server Error'} |
| 1.14 | Upload 獎懲管理辦法.pdf | FAIL | 0/1 | 967ms | {'_text': 'Internal Server Error'} |
| 1.15 | Upload README.md | FAIL | 0/1 | 315ms | {'_text': 'Internal Server Error'} |

### Phase 2

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| A1 | Q: 我們公司有交通津貼嗎？補助多少？ | FAIL | 0/4 | 401ms | HTTP 500: Internal Server Error |
| A2 | Q: 公司績效考核是一年幾次？ | FAIL | 0/4 | 377ms | HTTP 500: Internal Server Error |
| A3 | Q: 請問公司報帳有時間限制嗎？ | FAIL | 0/4 | 372ms | HTTP 500: Internal Server Error |
| A4 | Q: 新人到職第一天需要準備什麼？ | FAIL | 0/4 | 377ms | HTTP 500: Internal Server Error |
| A5 | Q: 公司的加班費怎麼算？ | FAIL | 0/4 | 429ms | HTTP 500: Internal Server Error |

### Phase 3

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| C1 | Q: 我們公司平日加班給 1.5 倍工資，這樣合法嗎？ | FAIL | 0/4 | 418ms | HTTP 500: Internal Server Error |
| C2 | Q: 員工特休沒休完，公司規定逾期視同放棄，這樣可以嗎？ | FAIL | 0/4 | 424ms | HTTP 500: Internal Server Error |
| C3 | Q: 全勤獎金因為員工請生理假被扣掉，合法嗎？ | FAIL | 0/4 | 406ms | HTTP 500: Internal Server Error |

### Phase 4

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| D1 | Q: 公司目前有多少位員工？ | FAIL | 0/4 | 332ms | HTTP 500: Internal Server Error |
| D2 | Q: 技術部的平均月薪是多少？ | FAIL | 0/4 | 396ms | HTTP 500: Internal Server Error |

### Phase 5

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| E1 | Q: 如果明天有新人到職，我需要準備哪些流程和文件？ | FAIL | 0/4 | 389ms | HTTP 500: Internal Server Error |
| E2 | Q: 請幫我比較正職和約聘人員在福利上有什麼差異？ | FAIL | 0/4 | 391ms | HTTP 500: Internal Server Error |

### Phase 6

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 6.1 | List Documents | FAIL | 0/1 | 392ms | {'_text': 'Internal Server Error'} |
| 6.3 | GET /users/me | FAIL | 0/1 | 376ms | {'_text': 'Internal Server Error'} |
| 6.4 | GET /audit/ | WARN | 0/1 | 395ms |  |

### Phase 8

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 8.2 | Health Latency (10x) | OK | 0/0 | 319ms | avg=319ms |
