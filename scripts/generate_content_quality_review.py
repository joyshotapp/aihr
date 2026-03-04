#!/usr/bin/env python3
import argparse
import json
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

PHASE_NAMES = {
    "2": "基礎問答",
    "3": "合規偵測",
    "4": "數據推理",
    "5": "進階能力",
    "6": "跨文件綜合",
    "7": "多輪對話",
}


def load_steps(log_path: Path, phases: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    by_phase: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("event") != "step":
                continue
            phase = str(row.get("phase", ""))
            if phase not in phases:
                continue
            req = row.get("request") or {}
            resp = row.get("response") or {}
            question = req.get("question")
            expected = req.get("expected")
            answer = resp.get("answer")
            if not question or answer is None:
                continue
            item = {
                "phase": phase,
                "step_id": row.get("step_id", ""),
                "question": question,
                "expected": expected,
                "answer": answer,
                "auto_score": row.get("score"),
                "auto_max": row.get("max_score"),
                "notes": row.get("notes", ""),
                "sources": resp.get("sources") or [],
                "duration_ms": row.get("duration_ms"),
            }
            by_phase[phase].append(item)
    return by_phase


def pick_samples(by_phase: Dict[str, List[Dict[str, Any]]], per_phase: int, seed: int) -> Dict[str, List[Dict[str, Any]]]:
    rng = random.Random(seed)
    chosen: Dict[str, List[Dict[str, Any]]] = {}
    for phase in sorted(by_phase.keys(), key=lambda x: int(x)):
        items = by_phase[phase]
        if len(items) <= per_phase:
            chosen[phase] = items
        else:
            chosen[phase] = rng.sample(items, per_phase)
    return chosen


def esc(text: Any) -> str:
    if text is None:
        return ""
    return str(text).replace("\n", " ").strip()


def build_markdown(
    run_id: str,
    log_path: Path,
    samples: Dict[str, List[Dict[str, Any]]],
    per_phase: int,
    seed: int,
) -> str:
    now = datetime.now().isoformat(timespec="seconds")
    lines: List[str] = []
    lines.append("# 內容品質人工評測表")
    lines.append("")
    lines.append(f"- 產生時間: {now}")
    lines.append(f"- Run ID: {run_id}")
    lines.append(f"- 來源檔案: {log_path}")
    lines.append(f"- 抽樣策略: 每個 phase 至多 {per_phase} 題，seed={seed}")
    lines.append("")
    lines.append("## 評分規則（1-5 分）")
    lines.append("")
    lines.append("- 正確性: 是否符合事實與法規，不含明顯錯誤")
    lines.append("- 完整性: 是否回答到問題重點，無關鍵遺漏")
    lines.append("- 可執行性: 建議是否可操作、可落地")
    lines.append("- 清晰度: 結構與語句是否易讀")
    lines.append("- 風險控管: 是否有必要的限制與提醒（法律/合規/不確定性）")
    lines.append("")
    lines.append("## 單題評分模板")
    lines.append("")
    lines.append("- 正確性: [ ]1 [ ]2 [ ]3 [ ]4 [ ]5")
    lines.append("- 完整性: [ ]1 [ ]2 [ ]3 [ ]4 [ ]5")
    lines.append("- 可執行性: [ ]1 [ ]2 [ ]3 [ ]4 [ ]5")
    lines.append("- 清晰度: [ ]1 [ ]2 [ ]3 [ ]4 [ ]5")
    lines.append("- 風險控管: [ ]1 [ ]2 [ ]3 [ ]4 [ ]5")
    lines.append("- 備註: ")
    lines.append("")

    total = 0
    for phase in sorted(samples.keys(), key=lambda x: int(x)):
        title = PHASE_NAMES.get(phase, f"Phase {phase}")
        lines.append(f"## Phase {phase} - {title}")
        lines.append("")
        for idx, item in enumerate(samples[phase], start=1):
            total += 1
            lines.append(f"### 題目 {phase}-{idx}（step: {item['step_id']}）")
            lines.append("")
            lines.append(f"- 問題: {esc(item['question'])}")
            lines.append(f"- 期望: {esc(item['expected'])}")
            lines.append(f"- 回答: {esc(item['answer'])}")
            lines.append(f"- 自動評分: {item['auto_score']}/{item['auto_max']} ({esc(item['notes'])})")
            lines.append(f"- 來源數: {len(item['sources'])}")
            lines.append(f"- 延遲: {item['duration_ms']} ms")
            lines.append("")
            lines.append("- 正確性: [ ]1 [ ]2 [ ]3 [ ]4 [ ]5")
            lines.append("- 完整性: [ ]1 [ ]2 [ ]3 [ ]4 [ ]5")
            lines.append("- 可執行性: [ ]1 [ ]2 [ ]3 [ ]4 [ ]5")
            lines.append("- 清晰度: [ ]1 [ ]2 [ ]3 [ ]4 [ ]5")
            lines.append("- 風險控管: [ ]1 [ ]2 [ ]3 [ ]4 [ ]5")
            lines.append("- 備註: ")
            lines.append("")
    lines.append("## 摘要")
    lines.append("")
    lines.append(f"- 抽樣總題數: {total}")
    lines.append("- 建議至少兩位評審獨立評分後再彙整")
    lines.append("- 建議另行記錄『錯得很自信』與『關鍵風險漏提示』案例")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate manual content-quality review sheet from test_log.jsonl")
    parser.add_argument("--run-dir", required=True, help="Path to run directory, e.g. test-data/test-results/<run_id>")
    parser.add_argument("--per-phase", type=int, default=3, help="Max sampled questions per phase")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling")
    parser.add_argument("--phases", default="2,3,4,5,6,7", help="Comma-separated phases to sample")
    parser.add_argument("--output", default="content_quality_review.md", help="Output markdown filename under run-dir")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    log_path = run_dir / "test_log.jsonl"
    if not log_path.exists():
        raise FileNotFoundError(f"Missing log file: {log_path}")

    phases = [p.strip() for p in args.phases.split(",") if p.strip()]
    by_phase = load_steps(log_path, phases)
    sampled = pick_samples(by_phase, args.per_phase, args.seed)

    run_id = run_dir.name
    md = build_markdown(run_id, log_path, sampled, args.per_phase, args.seed)
    out_path = run_dir / args.output
    out_path.write_text(md, encoding="utf-8")

    print(f"✅ Generated: {out_path}")
    for phase in sorted(sampled.keys(), key=lambda x: int(x)):
        print(f"  - Phase {phase}: {len(sampled[phase])} 題")


if __name__ == "__main__":
    main()
