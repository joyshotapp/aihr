# aihr Live E2E Test Report

**Server**: http://api.172-237-5-254.sslip.io
**Time**: 2026-02-11 12:03:57
**Duration**: 355.8s

## Summary

| Phase | Pass/Total | Score | % | Time |
|-------|-----------|-------|---|------|
| Phase 0 | 3/4 | 3/4 | 75% | 1.8s |
| Phase 1 | 0/15 | 0/15 | 0% | 295.3s |

**Total: 3/19 (15.8%) -- NEEDS WORK**

## Details

### Phase 0

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 0.1 | Health Check | OK | 1/1 | 370ms |  |
| 0.2 | Superuser Login | OK | 1/1 | 737ms | eyJhbGciOiJIUzI1NiIs... |
| 0.3 | Get Tenant | OK | 1/1 | 314ms | ID=b4539d8d-ea5... |
| 0.4 | Create HR User | FAIL | 0/1 | 364ms | {'detail': [{'type': 'value_error', 'loc': ['body', 'email'], 'msg': 'value is n |

### Phase 1

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 1.1 | Upload hr-policy-test.md | FAIL | 0/1 | 19457ms | {'_text': 'Internal Server Error'} |
| 1.2 | Upload 新增文件說明.md | FAIL | 0/1 | 19429ms | {'_text': 'Internal Server Error'} |
| 1.3 | Upload 勞動契約書-謝雅玲.pdf | FAIL | 0/1 | 19879ms | {'_text': 'Internal Server Error'} |
| 1.4 | Upload 勞動契約書-謝雅玲.txt | FAIL | 0/1 | 19357ms | {'_text': 'Internal Server Error'} |
| 1.5 | Upload 員工名冊.csv | FAIL | 0/1 | 19425ms | {'_text': 'Internal Server Error'} |
| 1.6 | Upload 員工名冊.pdf | FAIL | 0/1 | 19608ms | {'_text': 'Internal Server Error'} |
| 1.7 | Upload 請假單範本-E012-周秀蘭.pdf | FAIL | 0/1 | 19734ms | {'_text': 'Internal Server Error'} |
| 1.8 | Upload 請假單範本-E012-周秀蘭.txt | FAIL | 0/1 | 19417ms | {'_text': 'Internal Server Error'} |
| 1.9 | Upload 健康檢查報告-E016-高淑珍.pdf | FAIL | 0/1 | 20027ms | {'_text': 'Internal Server Error'} |
| 1.10 | Upload 健康檢查報告-E016-高淑珍.txt | FAIL | 0/1 | 19343ms | {'_text': 'Internal Server Error'} |
| 1.11 | Upload 員工手冊-第一章-總則.md | FAIL | 0/1 | 19345ms | {'_text': 'Internal Server Error'} |
| 1.12 | Upload 員工手冊-第一章-總則.pdf | FAIL | 0/1 | 19777ms | {'_text': 'Internal Server Error'} |
| 1.13 | Upload 獎懲管理辦法.md | FAIL | 0/1 | 19351ms | {'_text': 'Internal Server Error'} |
| 1.14 | Upload 獎懲管理辦法.pdf | FAIL | 0/1 | 21798ms | {'_text': 'Internal Server Error'} |
| 1.15 | Upload README.md | FAIL | 0/1 | 19400ms | {'_text': 'Internal Server Error'} |
