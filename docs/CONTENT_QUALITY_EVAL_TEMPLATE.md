# 內容品質評測模板（人工評審版）

本模板用來補足 `run_tests.py` 的關鍵字命中分數，專注在「回答內容品質」。

## 目標

- 區分「答對關鍵詞」與「答得好」
- 比較不同模型（例如 OpenAI / Ollama）在內容品質上的差異
- 找出高風險回答型態（錯得很自信、缺少風險提醒、格式可讀性差）

## 評測維度（每題 1-5 分）

- 正確性：事實、法規、數字是否正確
- 完整性：是否完整覆蓋題目需求
- 可執行性：建議是否可實作
- 清晰度：結構與語句是否清楚
- 風險控管：是否適當揭露限制、前提與法律風險

## 建議流程

1. 從 `test_log.jsonl` 抽樣（每 phase 2-5 題）
2. 至少兩位評審獨立打分
3. 匯總平均、分歧、代表性 bad case
4. 回饋 prompt / retrieval / guardrails

## 產生評測表（自動）

使用腳本：`scripts/generate_content_quality_review.py`

範例：

```bash
python scripts/generate_content_quality_review.py \
  --run-dir test-data/test-results/local_v3_verify_ollama_gemma3_27b_20260304_rerun2 \
  --per-phase 3 \
  --seed 42
```

輸出檔案預設為：

- `test-data/test-results/<run_id>/content_quality_review.md`

## 建議輸出指標

- 維度平均分（五大維度）
- 各 phase 平均分
- 高風險錯誤率（錯誤且語氣肯定）
- 缺少風險提醒率
- 評審分歧率（同題分差 >= 2）
