#!/usr/bin/env python3
"""Validate an OKF v0.1 knowledge bundle."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RESERVED = {"index.md", "log.md"}
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LINK_RE = re.compile(r"\]\(([^)]+)\)")


def parse_simple_yaml_block(block: str) -> dict[str, str]:
    """Minimal YAML parser for OKF frontmatter (key: value and tags lists)."""
    result: dict[str, str | list[str]] = {}
    current_key: str | None = None

    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- ") and current_key == "tags":
            tag = stripped[2:].strip().strip("'\"")
            existing = result.setdefault("tags", [])
            if isinstance(existing, list):
                existing.append(tag)
            continue

        match = re.match(r"^(\w+):\s*(.*)$", stripped)
        if match:
            key, value = match.group(1), match.group(2).strip()
            current_key = key
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                result[key] = (
                    [t.strip().strip("'\"") for t in inner.split(",") if t.strip()]
                    if inner
                    else []
                )
            elif value in ("", "null", "~"):
                result[key] = ""
            else:
                result[key] = value.strip("'\"")
        else:
            current_key = None

    return result  # type: ignore[return-value]


def collect_md_files(bundle: Path) -> list[Path]:
    return sorted(p for p in bundle.rglob("*.md") if p.is_file())


def validate_concept(path: Path, bundle: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = path.read_text(encoding="utf-8")

    match = FRONTMATTER_RE.match(text)
    if not match:
        errors.append(f"{rel(path, bundle)}: missing or malformed YAML frontmatter")
        return errors, warnings

    fm = parse_simple_yaml_block(match.group(1))
    type_val = fm.get("type", "")
    if not type_val or (isinstance(type_val, str) and not type_val.strip()):
        errors.append(f"{rel(path, bundle)}: frontmatter missing required 'type' field")

    for field in ("title", "description"):
        if field not in fm:
            warnings.append(f"{rel(path, bundle)}: missing recommended '{field}'")

    body = text[match.end() :]
    for link_match in LINK_RE.finditer(body):
        target = link_match.group(1).strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if target.endswith("/"):
            target_dir = resolve_link(path, target, bundle)
            if target_dir and not target_dir.exists():
                warnings.append(f"{rel(path, bundle)}: broken directory link -> {target}")
            continue
        if not target.endswith(".md"):
            target = target.rstrip("/") + ".md"
        resolved = resolve_link(path, target, bundle)
        if resolved and not resolved.exists():
            warnings.append(f"{rel(path, bundle)}: broken link -> {target}")

    return errors, warnings


def resolve_link(source: Path, target: str, bundle: Path) -> Path | None:
    if target.startswith("/"):
        return bundle / target.lstrip("/")
    return (source.parent / target).resolve()


def validate_index(path: Path, bundle: Path) -> list[str]:
    warnings: list[str] = []
    text = path.read_text(encoding="utf-8")
    if path == bundle / "index.md":
        match = FRONTMATTER_RE.match(text)
        if match:
            fm = parse_simple_yaml_block(match.group(1))
            if "okf_version" not in fm:
                warnings.append(f"{rel(path, bundle)}: bundle root index missing okf_version")
    elif FRONTMATTER_RE.match(text):
        warnings.append(f"{rel(path, bundle)}: non-root index.md should not have frontmatter")
    return warnings


def rel(path: Path, bundle: Path) -> str:
    try:
        return str(path.relative_to(bundle))
    except ValueError:
        return str(path)


def validate_bundle(bundle: Path) -> int:
    if not bundle.is_dir():
        print(f"ERROR: not a directory: {bundle}", file=sys.stderr)
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    md_files = collect_md_files(bundle)

    if not md_files:
        warnings.append("bundle contains no .md files")

    for path in md_files:
        name = path.name
        if name in RESERVED:
            warnings.extend(validate_index(path, bundle))
            continue
        e, w = validate_concept(path, bundle)
        errors.extend(e)
        warnings.extend(w)

    print(f"OKF validation: {bundle}")
    print(f"  files scanned: {len(md_files)}")
    print(f"  errors: {len(errors)}")
    print(f"  warnings: {len(warnings)}")

    for msg in errors:
        print(f"  ERROR: {msg}")
    for msg in warnings:
        print(f"  WARN:  {msg}")

    return 1 if errors else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an OKF v0.1 knowledge bundle")
    parser.add_argument("bundle", type=Path, help="Path to the bundle root directory")
    args = parser.parse_args()
    sys.exit(validate_bundle(args.bundle.resolve()))


if __name__ == "__main__":
    main()
