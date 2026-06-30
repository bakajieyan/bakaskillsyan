#!/usr/bin/env python3
"""Cursor-friendly trigger eval — offline score + review HTML (no claude CLI)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent


def main() -> None:
    skill_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (REPO_ROOT / "bakaknowledgeyan")
    eval_path = (
        Path(sys.argv[2]).resolve()
        if len(sys.argv) > 2
        else skill_path / "evals" / "trigger_eval.json"
    )
    score_script = SCRIPT_DIR / "score_trigger.py"
    review_html = skill_path / "evals" / "trigger_eval_review.html"
    results_json = skill_path / "evals" / "trigger_eval_results.json"

    proc = subprocess.run(
        [sys.executable, str(score_script), str(skill_path), str(eval_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(proc.stdout)
    results_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print("\n--- Cursor manual trigger test ---", file=sys.stderr)
    print("1. Ensure skill is in .cursor/skills/bakaknowledgeyan/", file=sys.stderr)
    print("2. Open Agent chat; paste each query from trigger_eval.json", file=sys.stderr)
    print("3. Confirm bakaknowledgeyan loads (not owasp / create-readme)", file=sys.stderr)
    print(f"4. Review: {review_html}", file=sys.stderr)
    print(f"5. Results: {results_json}", file=sys.stderr)


if __name__ == "__main__":
    main()
