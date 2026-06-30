#!/usr/bin/env python3
"""Package a skill folder into a distributable .skill file (zip)."""

from __future__ import annotations

import fnmatch
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quick_validate import validate_skill  # noqa: E402

EXCLUDE_DIRS = {"__pycache__", "node_modules", ".git"}
EXCLUDE_GLOBS = {"*.pyc", "*.pyo"}
EXCLUDE_FILES = {".DS_Store", "Thumbs.db"}
ROOT_EXCLUDE_DIRS = {"evals"}


def should_exclude(rel_path: Path) -> bool:
    parts = rel_path.parts
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    if len(parts) > 1 and parts[1] in ROOT_EXCLUDE_DIRS:
        return True
    name = rel_path.name
    if name in EXCLUDE_FILES:
        return True
    return any(fnmatch.fnmatch(name, pat) for pat in EXCLUDE_GLOBS)


def package_skill(skill_path: Path, output_dir: Path | None = None) -> Path | None:
    skill_path = skill_path.resolve()
    valid, message = validate_skill(skill_path)
    if not valid:
        print(f"ERROR: {message}", file=sys.stderr)
        return None
    print(message)

    output_path = (output_dir or Path.cwd()).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    skill_filename = output_path / f"{skill_path.name}.skill"

    with zipfile.ZipFile(skill_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in skill_path.rglob("*"):
            if not file_path.is_file():
                continue
            arcname = file_path.relative_to(skill_path.parent)
            if should_exclude(arcname):
                continue
            zipf.write(file_path, arcname.as_posix())

    print(f"Packaged: {skill_filename}")
    return skill_filename


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: package_skill.py <skill-folder> [output-dir]")
        sys.exit(1)
    skill_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    result = package_skill(skill_path, output_dir)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
