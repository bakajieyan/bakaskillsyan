#!/usr/bin/env python3
"""Heuristic trigger-eval score for a skill description (offline, no LLM)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Keywords that suggest bakaknowledgeyan vs adjacent skills
TRIGGER_HINTS = [
    "okf",
    "knowledge bundle",
    "knowledge catalog",
    "concept",
    "frontmatter",
    "validate_okf",
    "query_okf",
    "discover_okf",
    "progressive",
    "playbook",
    "agent wiki",
    "turn",
    "enrich",
    "bundle",
    "index.md",
    "yaml",
]

NEGATIVE_HINTS = {
    "owasp": ["owasp", "security review", "injection", "idor", "asvs"],
    "openapi": ["openapi", "swagger", "protobuf"],
    "caveman": ["caveman", "compress claude", "compress agents"],
    "readme_only": ["single file", "readme.md for packages", "single file is fine"],
    "vector": ["embeddings", "vector search", "notion-style"],
    "explain_only": ["just explain", "no new docs"],
    "adr": ["adr-", "architecture decision"],
    "er_diagram": ["dbdiagram", "er diagram"],
}

# Description "Not for ..." clause → query must match these to suppress trigger
EXCLUSION_RULES = [
    ("owasp-only", ["owasp", "security review"]),
    ("openapi", ["openapi", "swagger"]),
    ("single-file readme", ["readme.md", "single file is fine"]),
    ("adrs", ["adr-"]),
    ("raw schema er diagrams", ["dbdiagram", "er diagram"]),
    ("vector/embedding search", ["embeddings", "vector search", "notion-style"]),
    ("explain-only", ["just explain", "no new docs"]),
    ("caveman compress", ["caveman", "compress claude", "compress agents"]),
    ("git commit", ["commit message", "git commit"]),
    ("prettier", ["prettier"]),
    ("orm migration", ["prisma migration"]),
]


def load_description(skill_path: Path) -> str:
    text = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return ""
    for line in match.group(1).splitlines():
        if line.strip().startswith("description:"):
            return line.split(":", 1)[1].strip().strip("'\"")
    return ""


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_/-]+", text.lower()))


def score_query(query: str, description: str, should_trigger: bool) -> tuple[bool, str]:
    q = query.lower()
    d = description.lower()
    q_tokens = tokenize(q)

    # Honor explicit exclusions in description ("Not for X, Y, Z")
    not_for_match = re.search(r"not for ([^.]+)", d, re.I)
    active_rules = EXCLUSION_RULES
    if not_for_match:
        clause = not_for_match.group(1).lower()
        active_rules = [r for r in EXCLUSION_RULES if any(k in clause for k in r[0].split()) or r[0] in clause]

    def query_hits_exclusion() -> str | None:
        for label, needles in active_rules:
            if any(n in q for n in needles):
                return label
        return None

    excluded = query_hits_exclusion()
    if excluded and not should_trigger:
        return True, f"excluded by description ({excluded})"
    if excluded and should_trigger:
        return False, f"wrongly excluded ({excluded})"

    skill_signal = sum(1 for h in TRIGGER_HINTS if h in q or h in q_tokens)
    skill_signal += sum(1 for t in q_tokens if t in d)

    for label, hints in NEGATIVE_HINTS.items():
        if any(h in q for h in hints):
            if should_trigger:
                return skill_signal >= 2, f"edge should-trigger ({label})"
            # should NOT trigger — description should not heavily match OKF when query is negative domain
            okf_in_desc = "okf" in d or "knowledge bundle" in d
            if okf_in_desc and skill_signal < 2:
                return True, f"correct reject ({label})"
            if skill_signal >= 3 and not should_trigger:
                return False, f"may over-trigger ({label})"
            return True, f"correct reject ({label})"

    if should_trigger:
        ok = skill_signal >= 1 or any(h in d for h in TRIGGER_HINTS if h in q)
        return ok, f"signal={skill_signal}"
    return skill_signal < 2, f"signal={skill_signal}"


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: score_trigger.py <skill-path> <trigger_eval.json>")
        sys.exit(1)

    skill_path = Path(sys.argv[1]).resolve()
    eval_path = Path(sys.argv[2]).resolve()
    description = load_description(skill_path)
    items = json.loads(eval_path.read_text(encoding="utf-8"))

    results = []
    for item in items:
        ok, reason = score_query(item["query"], description, item["should_trigger"])
        results.append({**item, "predicted_ok": ok, "reason": reason})

    should = [r for r in results if r["should_trigger"]]
    should_not = [r for r in results if not r["should_trigger"]]
    trig_pass = sum(1 for r in should if r["predicted_ok"])
    neg_pass = sum(1 for r in should_not if r["predicted_ok"])

    report = {
        "description_chars": len(description),
        "trigger_pass": f"{trig_pass}/{len(should)}",
        "negative_pass": f"{neg_pass}/{len(should_not)}",
        "total_pass": f"{trig_pass + neg_pass}/{len(results)}",
        "failures": [r for r in results if not r["predicted_ok"]],
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
