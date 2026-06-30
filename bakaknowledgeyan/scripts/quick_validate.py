#!/usr/bin/env python3
"""Validate SKILL.md frontmatter before packaging."""

from __future__ import annotations

import re
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9-]+$")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        m = re.match(r"^(\w+):\s*(.+)$", line.strip())
        if m:
            val = m.group(2).strip().strip("'\"")
            result[m.group(1)] = val
    return result


def validate_skill(skill_path: Path) -> tuple[bool, str]:
    skill_path = skill_path.resolve()
    if not skill_path.is_dir():
        return False, f"not a directory: {skill_path}"
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md missing"
    fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    name = fm.get("name", "")
    desc = fm.get("description", "")
    if not name:
        return False, "frontmatter missing name"
    if name != skill_path.name:
        return False, f"name '{name}' must match folder '{skill_path.name}'"
    if not NAME_RE.match(name):
        return False, "name must be lowercase letters, numbers, hyphens only"
    if not desc or len(desc) > 1024:
        return False, "description missing or exceeds 1024 chars"
    agents = skill_path / "AGENTS.md"
    if not agents.exists():
        return False, "AGENTS.md missing (recommended entry point)"
    return True, f"Skill '{name}' valid ({len(desc)} char description)"


if __name__ == "__main__":
    import sys

    ok, msg = validate_skill(Path(sys.argv[1]))
    print(msg)
    sys.exit(0 if ok else 1)
