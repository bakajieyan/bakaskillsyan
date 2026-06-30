#!/usr/bin/env python3
"""Compare OKF bundle output sizes (proxy for token cost)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FRONTMATTER = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


def bundle_stats(outputs: Path) -> dict:
    bundle = outputs / "knowledge" if (outputs / "knowledge").is_dir() else outputs
    if not bundle.is_dir():
        return {"files": 0, "chars": 0, "body_chars": 0, "lines": 0}

    files = list(bundle.rglob("*.md"))
    total_chars = 0
    body_chars = 0
    lines = 0
    for p in files:
        text = p.read_text(encoding="utf-8")
        total_chars += len(text)
        lines += text.count("\n") + 1
        body = FRONTMATTER.sub("", text, count=1)
        body_chars += len(body)
    return {
        "files": len(files),
        "chars": total_chars,
        "body_chars": body_chars,
        "lines": lines,
    }


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    iteration = sys.argv[2] if len(sys.argv) > 2 else "iteration-2"
    base = repo / "bakaknowledgeyan-workspace" / iteration
    evals = ["tenant-onboarding", "database-tables", "incident-playbook"]
    rows = []
    for ev in evals:
        for cfg in ("with_skill", "without_skill"):
            out = base / ev / cfg / "outputs"
            g = out / "grading.json"
            grade = json.loads(g.read_text()) if g.exists() else {}
            stats = bundle_stats(out)
            rows.append({
                "eval": ev,
                "config": cfg,
                "pass_rate": grade.get("pass_rate", 0),
                "passed": grade.get("passed", 0),
                "total": grade.get("total", 0),
                **stats,
            })
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
