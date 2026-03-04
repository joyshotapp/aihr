#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List

TARGET_PHASES = {"2", "3", "4", "5", "6", "7"}


def load_steps(log_path: Path) -> Dict[Tuple[str, str], Dict[str, Any]]:
    rows: Dict[Tuple[str, str], Dict[str, Any]] = {}
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj.get("event") != "step":
                continue
            phase = str(obj.get("phase", ""))
            step_id = str(obj.get("step_id", ""))
            if phase not in TARGET_PHASES or not step_id:
                continue
            req = obj.get("request") or {}
            resp = obj.get("response") or {}
            question = req.get("question")
            answer = resp.get("answer")
            if not question or answer is None:
                continue
            rows[(phase, step_id)] = {
                "phase": phase,
                "step_id": step_id,
                "question": question,
                "answer": answer,
                "score": obj.get("score"),
                "max_score": obj.get("max_score"),
                "notes": obj.get("notes", ""),
                "duration_ms": obj.get("duration_ms"),
            }
    return rows


def phase_step_sort_key(key: Tuple[str, str]) -> Tuple[int, str]:
    phase, step_id = key
    return (int(phase), step_id)


def short(text: Any, n: int = 70) -> str:
    if text is None:
        return ""
    s = str(text).replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def build_report(
    left_name: str,
    right_name: str,
    left_rows: Dict[Tuple[str, str], Dict[str, Any]],
    right_rows: Dict[Tuple[str, str], Dict[str, Any]],
) -> str:
    keys = sorted(set(left_rows.keys()) & set(right_rows.keys()), key=phase_step_sort_key)

    lines: List[str] = []
    lines.append("# Run 並排比較（內容與分數）")
    lines.append("")
    lines.append(f"- Left: {left_name}")
    lines.append(f"- Right: {right_name}")
    lines.append(f"- 共同題數: {len(keys)}")
    lines.append("")

    better_left = 0
    better_right = 0
    same = 0
    diffs: List[Tuple[Tuple[str, str], int]] = []

    for key in keys:
        l = left_rows[key]
        r = right_rows[key]
        ls = int(l.get("score") or 0)
        rs = int(r.get("score") or 0)
        delta = rs - ls
        if delta > 0:
            better_right += 1
        elif delta < 0:
            better_left += 1
        else:
            same += 1
        if delta != 0:
            diffs.append((key, delta))

    lines.append("## 分數摘要")
    lines.append("")
    lines.append(f"- 同分題數: {same}")
    lines.append(f"- {left_name} 較高題數: {better_left}")
    lines.append(f"- {right_name} 較高題數: {better_right}")
    lines.append("")

    lines.append("## 差異題（依 phase/step）")
    lines.append("")
    lines.append("| Phase | Step | 分數 Left | 分數 Right | Δ(R-L) | 問題 |")
    lines.append("|---|---|---:|---:|---:|---|")

    if diffs:
        for key, delta in sorted(diffs, key=lambda x: phase_step_sort_key(x[0])):
            l = left_rows[key]
            r = right_rows[key]
            lines.append(
                f"| {l['phase']} | {l['step_id']} | {l['score']}/{l['max_score']} | {r['score']}/{r['max_score']} | {delta:+d} | {short(l['question'])} |"
            )
    else:
        lines.append("| - | - | - | - | 0 | 無差異 |")

    lines.append("")
    lines.append("## 差異題答案摘要")
    lines.append("")
    for key, delta in sorted(diffs, key=lambda x: phase_step_sort_key(x[0])):
        l = left_rows[key]
        r = right_rows[key]
        lines.append(f"### Phase {l['phase']} / {l['step_id']} (Δ={delta:+d})")
        lines.append("")
        lines.append(f"- 問題: {short(l['question'], 140)}")
        lines.append(f"- Left 回答: {short(l['answer'], 220)}")
        lines.append(f"- Right 回答: {short(r['answer'], 220)}")
        lines.append(f"- Left notes: {l.get('notes', '')}")
        lines.append(f"- Right notes: {r.get('notes', '')}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two run test_log.jsonl files side-by-side")
    parser.add_argument("--left-run-dir", required=True)
    parser.add_argument("--right-run-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    left_run_dir = Path(args.left_run_dir)
    right_run_dir = Path(args.right_run_dir)

    left_log = left_run_dir / "test_log.jsonl"
    right_log = right_run_dir / "test_log.jsonl"
    if not left_log.exists() or not right_log.exists():
        raise FileNotFoundError("test_log.jsonl missing in left or right run dir")

    left_rows = load_steps(left_log)
    right_rows = load_steps(right_log)

    report = build_report(left_run_dir.name, right_run_dir.name, left_rows, right_rows)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"✅ Generated: {out_path}")


if __name__ == "__main__":
    main()
