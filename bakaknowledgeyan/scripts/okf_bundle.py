#!/usr/bin/env python3
"""Shared OKF bundle detection — repo-agnostic, any project layout."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

RESERVED = {"index.md", "log.md"}
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "dist",
    "build",
    "out",
    "target",
    "__pycache__",
    ".venv",
    "venv",
    ".turbo",
    ".next",
    "vendor",
    "coverage",
    ".cache",
}

COMMON_BUNDLE_REL_PATHS = (
    "knowledge",
    "docs/knowledge",
    "doc/knowledge",
    "okf",
    "docs/okf",
    ".okf",
    "docs/agent-knowledge",
    "agent-knowledge",
)


def parse_simple_yaml_block(block: str) -> dict[str, str | list[str]]:
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

    return result


def is_concept_file(path: Path) -> bool:
    if path.name in RESERVED:
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    match = FRONTMATTER_RE.match(text)
    if not match:
        return False
    fm = parse_simple_yaml_block(match.group(1))
    type_val = fm.get("type", "")
    return bool(type_val and str(type_val).strip())


def root_level_concept_count(bundle: Path) -> int:
    count = 0
    for path in bundle.glob("*.md"):
        if is_concept_file(path):
            count += 1
    return count


def standalone_bundle_at_root(repo_root: Path) -> bool:
    """True when repo root itself is the OKF bundle (not a monorepo wrapper)."""
    index = repo_root / "index.md"
    if not index.exists():
        return False
    try:
        text = index.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    match = FRONTMATTER_RE.match(text)
    if match:
        fm = parse_simple_yaml_block(match.group(1))
        if fm.get("okf_version"):
            return True
    return root_level_concept_count(repo_root) >= 1


def bundle_stats(bundle: Path) -> tuple[int, bool, str | None]:
    concept_count = 0
    okf_version: str | None = None
    has_index = (bundle / "index.md").exists()

    if has_index:
        try:
            text = (bundle / "index.md").read_text(encoding="utf-8")
        except OSError:
            text = ""
        match = FRONTMATTER_RE.match(text)
        if match:
            fm = parse_simple_yaml_block(match.group(1))
            raw = fm.get("okf_version", "")
            if raw:
                okf_version = str(raw).strip("'\"")

    if bundle.is_dir():
        for path in bundle.rglob("*.md"):
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            try:
                if is_concept_file(path):
                    concept_count += 1
            except OSError:
                continue

    return concept_count, has_index, okf_version


def is_okf_bundle(bundle: Path) -> bool:
    if not bundle.is_dir():
        return False
    concept_count, has_index, okf_version = bundle_stats(bundle)
    if okf_version:
        return True
    if concept_count >= 1 and has_index:
        return True
    if concept_count >= 2:
        return True
    return False


def confidence_label(
    bundle: Path,
    repo_root: Path,
    okf_version: str | None,
    concept_count: int,
) -> str:
    if okf_version:
        return "high"
    try:
        rel = bundle.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        rel = bundle.as_posix()
    if rel in COMMON_BUNDLE_REL_PATHS or rel == ".":
        return "high"
    if concept_count >= 3:
        return "medium"
    return "low"


@dataclass
class BundleCandidate:
    path: Path
    rel_path: str
    concept_count: int
    has_index: bool
    okf_version: str | None
    confidence: str


def _should_skip_dir(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def discover_bundles(repo_root: Path, deep: bool = False) -> list[BundleCandidate]:
    repo_root = repo_root.resolve()
    seen: set[Path] = set()
    candidates: list[BundleCandidate] = []

    def add_candidate(bundle: Path) -> None:
        resolved = bundle.resolve()
        if resolved in seen or not is_okf_bundle(resolved):
            return
        seen.add(resolved)
        concept_count, has_index, okf_version = bundle_stats(resolved)
        try:
            rel = resolved.relative_to(repo_root).as_posix()
        except ValueError:
            rel = resolved.as_posix()
        candidates.append(
            BundleCandidate(
                path=resolved,
                rel_path=rel,
                concept_count=concept_count,
                has_index=has_index,
                okf_version=okf_version,
                confidence=confidence_label(resolved, repo_root, okf_version, concept_count),
            )
        )

    if standalone_bundle_at_root(repo_root):
        add_candidate(repo_root)

    for rel in COMMON_BUNDLE_REL_PATHS:
        add_candidate(repo_root / rel)

    if deep:
        for path in repo_root.rglob("index.md"):
            if _should_skip_dir(path.parent):
                continue
            add_candidate(path.parent)

        for path in repo_root.rglob("*.md"):
            if _should_skip_dir(path.parent):
                continue
            if path.name in RESERVED:
                continue
            if is_concept_file(path):
                add_candidate(path.parent)

    order = {"high": 0, "medium": 1, "low": 2}
    candidates.sort(
        key=lambda c: (order.get(c.confidence, 9), -c.concept_count, c.rel_path),
    )
    return candidates


def resolve_bundle(repo_root: Path, deep: bool = False) -> Path | None:
    """Pick a single bundle: only candidate, or highest-confidence with most concepts."""
    found = discover_bundles(repo_root, deep=deep)
    if not found:
        return None
    if len(found) == 1:
        return found[0].path
    high = [c for c in found if c.confidence == "high"]
    pool = high if high else found
    return pool[0].path
