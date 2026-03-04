# aihr Live E2E Test Report

**Server**: http://api.172-237-5-254.sslip.io
**Time**: 2026-02-11 17:31:19
**Duration**: 188.2s

## Summary

| Phase | Pass/Total | Score | % | Time |
|-------|-----------|-------|---|------|
| Phase 0 | 5/5 | 5/5 | 100% | 3.4s |
| Phase 1 | 15/15 | 15/15 | 100% | 8.4s |
| Phase 2 | 0/5 | 0/20 | 0% | 37.2s |
| Phase 3 | 0/3 | 0/12 | 0% | 21.9s |
| Phase 4 | 0/2 | 0/8 | 0% | 9.1s |
| Phase 5 | 0/2 | 0/8 | 0% | 11.6s |
| Phase 6 | 3/4 | 3/4 | 75% | 1.4s |
| Phase 7 | 0/2 | 0/8 | 0% | 8.4s |
| Phase 8 | 2/2 | 0/0 | N/A% | 6.2s |

**Total: 23/80 (28.7%) -- NEEDS WORK**

## Details

### Phase 0

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 0.1 | Health Check | OK | 1/1 | 484ms |  |
| 0.2 | Superuser Login | OK | 1/1 | 872ms | eyJhbGciOiJIUzI1NiIs... |
| 0.3 | Get Tenant | OK | 1/1 | 332ms | ID=7a77da32-b9b... |
| 0.4 | Create HR User | OK | 1/1 | 790ms | hr-test-1770802092@example.com |
| 0.5 | HR User Login | OK | 1/1 | 906ms |  |

### Phase 1

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 1.1 | Upload hr-policy-test.md | OK | 1/1 | 341ms | ID=8fb2ddea |
| 1.2 | Upload 新增文件說明.md | OK | 1/1 | 387ms | ID=f2ca26de |
| 1.3 | Upload 勞動契約書-謝雅玲.pdf | OK | 1/1 | 1028ms | ID=ec5012dd |
| 1.4 | Upload 勞動契約書-謝雅玲.txt | OK | 1/1 | 461ms | ID=c1e388b9 |
| 1.5 | Upload 員工名冊.csv | OK | 1/1 | 322ms | ID=ed31ec3c |
| 1.6 | Upload 員工名冊.pdf | OK | 1/1 | 732ms | ID=b3cfd6b3 |
| 1.7 | Upload 請假單範本-E012-周秀蘭.pdf | OK | 1/1 | 821ms | ID=9d0abfd8 |
| 1.8 | Upload 請假單範本-E012-周秀蘭.txt | OK | 1/1 | 320ms | ID=53f7aec5 |
| 1.9 | Upload 健康檢查報告-E016-高淑珍.pdf | OK | 1/1 | 1050ms | ID=41671a39 |
| 1.10 | Upload 健康檢查報告-E016-高淑珍.txt | OK | 1/1 | 365ms | ID=5f642fe1 |
| 1.11 | Upload 員工手冊-第一章-總則.md | OK | 1/1 | 381ms | ID=a9ab0ffd |
| 1.12 | Upload 員工手冊-第一章-總則.pdf | OK | 1/1 | 715ms | ID=cd10cbf4 |
| 1.13 | Upload 獎懲管理辦法.md | OK | 1/1 | 318ms | ID=a91e5ef6 |
| 1.14 | Upload 獎懲管理辦法.pdf | OK | 1/1 | 862ms | ID=124a2222 |
| 1.15 | Upload README.md | OK | 1/1 | 324ms | ID=5a16d70e |

### Phase 2

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| A1 | Q: 我們公司有交通津貼嗎？補助多少？ | FAIL | 0/4 | 8083ms | hits=0/3 ans=抱歉，未找到相關資訊。請嘗試換個方式提問，或聯繫 HR 部門。

本回覆僅為內規與法規摘要，仍以公司... |
| A2 | Q: 公司績效考核是一年幾次？ | FAIL | 0/4 | 7531ms | hits=0/3 ans=抱歉，未找到相關資訊。請嘗試換個方式提問，或聯繫 HR 部門。

本回覆僅為內規與法規摘要，仍以公司... |
| A3 | Q: 請問公司報帳有時間限制嗎？ | FAIL | 0/4 | 5982ms | hits=0/3 ans=抱歉，未找到相關資訊。請嘗試換個方式提問，或聯繫 HR 部門。

本回覆僅為內規與法規摘要，仍以公司... |
| A4 | Q: 新人到職第一天需要準備什麼？ | FAIL | 0/4 | 8106ms | hits=0/4 ans=抱歉，未找到相關資訊。請嘗試換個方式提問，或聯繫 HR 部門。

本回覆僅為內規與法規摘要，仍以公司... |
| A5 | Q: 公司的加班費怎麼算？ | FAIL | 0/4 | 7457ms | hits=0/3 ans=抱歉，未找到相關資訊。請嘗試換個方式提問，或聯繫 HR 部門。

本回覆僅為內規與法規摘要，仍以公司... |

### Phase 3

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| C1 | Q: 我們公司平日加班給 1.5 倍工資，這樣合法嗎？ | FAIL | 0/4 | 6951ms | hits=0/4 ans=抱歉，未找到相關資訊。請嘗試換個方式提問，或聯繫 HR 部門。

本回覆僅為內規與法規摘要，仍以公司... |
| C2 | Q: 員工特休沒休完，公司規定逾期視同放棄，這樣可以嗎？ | FAIL | 0/4 | 7107ms | hits=0/4 ans=抱歉，未找到相關資訊。請嘗試換個方式提問，或聯繫 HR 部門。

本回覆僅為內規與法規摘要，仍以公司... |
| C3 | Q: 全勤獎金因為員工請生理假被扣掉，合法嗎？ | FAIL | 0/4 | 7883ms | hits=0/5 ans=抱歉，未找到相關資訊。請嘗試換個方式提問，或聯繫 HR 部門。

本回覆僅為內規與法規摘要，仍以公司... |

### Phase 4

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| D1 | Q: 公司目前有多少位員工？ | FAIL | 0/4 | 3922ms | hits=0/3 ans=抱歉，未找到相關資訊。請嘗試換個方式提問，或聯繫 HR 部門。

本回覆僅為內規與法規摘要，仍以公司... |
| D2 | Q: 技術部的平均月薪是多少？ | FAIL | 0/4 | 5178ms | hits=0/3 ans=抱歉，未找到相關資訊。請嘗試換個方式提問，或聯繫 HR 部門。

本回覆僅為內規與法規摘要，仍以公司... |

### Phase 5

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| E1 | Q: 如果明天有新人到職，我需要準備哪些流程和文件？ | FAIL | 0/4 | 7577ms | hits=0/5 ans=抱歉，未找到相關資訊。請嘗試換個方式提問，或聯繫 HR 部門。

本回覆僅為內規與法規摘要，仍以公司... |
| E2 | Q: 請幫我比較正職和約聘人員在福利上有什麼差異？ | FAIL | 0/4 | 4031ms | hits=0/4 ans=抱歉，未找到相關資訊。請嘗試換個方式提問，或聯繫 HR 部門。

本回覆僅為內規與法規摘要，仍以公司... |

### Phase 6

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 6.1 | List Documents | OK | 1/1 | 383ms | 15 docs |
| 6.2 | Get Document Detail | OK | 1/1 | 303ms |  |
| 6.3 | GET /users/me | OK | 1/1 | 347ms | hr-test-1770802092@example.com |
| 6.4 | GET /audit/ | WARN | 0/1 | 352ms |  |

### Phase 7

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| F1 | Follow: 承上題，如果這位員工年資未滿一年呢？ | FAIL | 0/4 | 5077ms | hits=0/3 |
| F2 | Follow: 那他可以申請育嬰假嗎？ | FAIL | 0/4 | 3295ms | hits=0/3 |

### Phase 8

| Step | Action | Status | Score | Time | Detail |
|------|--------|--------|-------|------|--------|
| 8.1 | Chat Latency (5x avg) | OK | 0/0 | 5852ms | avg=5853ms min=5219ms max=6245ms |
| 8.2 | Health Latency (10x) | OK | 0/0 | 334ms | avg=335ms |
