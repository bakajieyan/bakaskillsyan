#!/usr/bin/env python3
"""Aggregate grading.json + timing.json into benchmark.json for eval viewer."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: aggregate_benchmark.py <iteration-dir> [--skill-name NAME]")
        sys.exit(1)
    iteration = Path(sys.argv[1]).resolve()
    skill_name = "bakaknowledgeyan"
    if len(sys.argv) > 3 and sys.argv[2] == "--skill-name":
        skill_name = sys.argv[3]

    eval_dirs = [p for p in iteration.iterdir() if p.is_dir() and (p / "eval_metadata.json").exists()]
    rows = []
    for ev in sorted(eval_dirs):
        meta = load_json(ev / "eval_metadata.json") or {}
        for config in ("with_skill", "without_skill"):
            run_dir = ev / config / "outputs"
            grade = load_json(run_dir / "grading.json")
            timing = load_json(ev / config / "timing.json") or load_json(run_dir / "timing.json")
            if not grade:
                continue
            rows.append(
                {
                    "eval_name": meta.get("eval_name", ev.name),
                    "config": config,
                    "pass_rate": grade.get("pass_rate", 0),
                    "passed": grade.get("passed", 0),
                    "total": grade.get("total", 0),
                    "total_tokens": timing.get("total_tokens") if timing else None,
                    "duration_ms": timing.get("duration_ms") if timing else None,
                }
            )

    benchmark = {"skill_name": skill_name, "iteration": iteration.name, "runs": rows}
    out = iteration / "benchmark.json"
    out.write_text(json.dumps(benchmark, indent=2), encoding="utf-8")

    lines = [f"# Benchmark — {skill_name} ({iteration.name})", "", "| Eval | Config | Pass rate | Passed | Tokens | Duration |", "|------|--------|-----------|--------|--------|----------|"]
    for r in rows:
        tok = r["total_tokens"] if r["total_tokens"] is not None else "-"
        dur = f"{r['duration_ms']}ms" if r["duration_ms"] is not None else "-"
        lines.append(
            f"| {r['eval_name']} | {r['config']} | {r['pass_rate']:.0%} | {r['passed']}/{r['total']} | {tok} | {dur} |"
        )
    (iteration / "benchmark.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(benchmark, indent=2))


if __name__ == "__main__":
    main()
