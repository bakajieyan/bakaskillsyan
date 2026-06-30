#!/usr/bin/env python3
"""Query an OKF bundle — catalog and rank concepts without loading full bodies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

RESERVED = {"index.md", "log.md"}
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LINK_RE = re.compile(r"\]\(([^)]+)\)")
TOKEN_EST_CHARS = 4  # rough chars-per-token for budgeting


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


@dataclass
class ConceptMeta:
    path: str
    type: str
    title: str
    description: str
    tags: list[str]
    resource: str
    chars: int
    body_chars: int

    @property
    def est_tokens(self) -> int:
        return max(1, self.chars // TOKEN_EST_CHARS)


def rel(path: Path, bundle: Path) -> str:
    try:
        return str(path.relative_to(bundle)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def collect_concepts(bundle: Path) -> list[tuple[Path, ConceptMeta, str]]:
    rows: list[tuple[Path, ConceptMeta, str]] = []
    for path in sorted(bundle.rglob("*.md")):
        if not path.is_file() or path.name in RESERVED:
            continue
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if not match:
            continue
        fm = parse_simple_yaml_block(match.group(1))
        body = text[match.end() :]
        tags = fm.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        meta = ConceptMeta(
            path=rel(path, bundle),
            type=str(fm.get("type", "")),
            title=str(fm.get("title", "")),
            description=str(fm.get("description", "")),
            tags=list(tags),
            resource=str(fm.get("resource", "")),
            chars=len(text),
            body_chars=len(body),
        )
        rows.append((path, meta, body))
    return rows


def tokenize_query(query: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9_-]+", query.lower()) if len(t) > 1]


def score_concept(meta: ConceptMeta, body: str, terms: list[str]) -> int:
    if not terms:
        return 0
    haystacks = {
        "title": (meta.title or Path(meta.path).stem).lower(),
        "description": meta.description.lower(),
        "type": meta.type.lower(),
        "path": meta.path.lower(),
        "tags": " ".join(meta.tags).lower(),
        "body": body.lower(),
    }
    weights = {
        "title": 12,
        "tags": 10,
        "description": 8,
        "type": 6,
        "path": 5,
        "body": 2,
    }
    total = 0
    for term in terms:
        for field, text in haystacks.items():
            if term in text:
                total += weights[field]
                if field == "body":
                    total += text.count(term) * weights[field]
    return total


def resolve_link(source: Path, target: str, bundle: Path) -> Path | None:
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return None
    if target.startswith("/"):
        return bundle / target.lstrip("/")
    return (source.parent / target).resolve()


def outbound_links(path: Path, body: str, bundle: Path) -> list[str]:
    seen: set[str] = set()
    links: list[str] = []
    for link_match in LINK_RE.finditer(body):
        target = link_match.group(1).strip()
        if target.endswith("/"):
            continue
        if not target.endswith(".md"):
            target = target.rstrip("/") + ".md"
        resolved = resolve_link(path, target, bundle)
        if not resolved:
            continue
        try:
            link_rel = rel(resolved, bundle)
        except ValueError:
            continue
        if link_rel not in seen and resolved.exists():
            seen.add(link_rel)
            links.append(link_rel)
    return links


def format_row(meta: ConceptMeta, score: int | None = None) -> str:
    tags = ",".join(meta.tags) if meta.tags else "-"
    title = meta.title or Path(meta.path).stem
    desc = meta.description or "-"
    prefix = f"{score:>3} " if score is not None else ""
    return (
        f"{prefix}{meta.path} | {meta.type} | {title} | {desc} "
        f"| tags:{tags} | ~{meta.est_tokens}tok"
    )


def print_catalog(concepts: list[tuple[Path, ConceptMeta, str]], as_json: bool) -> None:
    total_tokens = sum(m.est_tokens for _, m, _ in concepts)
    if as_json:
        payload = {
            "concepts": [asdict(m) for _, m, _ in concepts],
            "count": len(concepts),
            "est_tokens_if_full_load": total_tokens,
        }
        print(json.dumps(payload, indent=2))
        return
    print(f"# catalog: {len(concepts)} concepts (~{total_tokens} tok if fully loaded)")
    print("path | type | title | description | tags | est_tokens")
    for _, meta, _ in concepts:
        print(format_row(meta))


def print_matches(
    scored: list[tuple[int, Path, ConceptMeta, str]],
    max_results: int,
    as_json: bool,
) -> None:
    top = scored[:max_results]
    if not top:
        print("No matches. Try --catalog or broader terms.", file=sys.stderr)
        return
    load_tokens = sum(m.est_tokens for _, _, m, _ in top)
    if as_json:
        print(
            json.dumps(
                {
                    "matches": [
                        {"score": s, **asdict(m)} for s, _, m, _ in top
                    ],
                    "count": len(top),
                    "est_tokens_if_load_matches": load_tokens,
                },
                indent=2,
            )
        )
        return
    print(f"# {len(top)} matches (~{load_tokens} tok if you load these only)")
    for score, _, meta, _ in top:
        print(format_row(meta, score))
    print("\n# next: Read matched paths only; follow links on demand with --path X --links")


def print_path_detail(
    bundle: Path,
    concepts: list[tuple[Path, ConceptMeta, str]],
    target_path: str,
    links_only: bool,
    as_json: bool,
) -> None:
    norm = target_path.replace("\\", "/").lstrip("/")
    match_row: tuple[Path, ConceptMeta, str] | None = None
    for path, meta, body in concepts:
        if meta.path == norm or meta.path.endswith("/" + norm):
            match_row = (path, meta, body)
            break
    if not match_row:
        print(f"ERROR: concept not found: {target_path}", file=sys.stderr)
        sys.exit(1)

    path, meta, body = match_row
    link_paths = outbound_links(path, body, bundle)
    link_meta = {m.path: m for _, m, _ in concepts}
    linked = [
        {
            "path": lp,
            "type": link_meta[lp].type if lp in link_meta else "",
            "title": link_meta[lp].title if lp in link_meta else Path(lp).stem,
        }
        for lp in link_paths
    ]

    if as_json:
        print(
            json.dumps(
                {
                    "concept": asdict(meta),
                    "outbound_links": linked,
                    "read_instruction": f"Read {meta.path} for full body",
                },
                indent=2,
            )
        )
        return

    print(format_row(meta))
    if links_only:
        print("\n# outbound links (load only if needed)")
        for item in linked:
            title = item["title"] or Path(item["path"]).stem
            print(f"  -> {item['path']} | {item['type']} | {title}")
        print(f"\n# next: Read {meta.path} — do not bulk-load sibling concepts")
        return

    print(f"\n# Read tool: {meta.path} (~{meta.est_tokens} tok)")
    if linked:
        print("# linked (on demand):")
        for item in linked:
            print(f"  -> {item['path']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query OKF bundle — progressive disclosure without full bundle load",
    )
    parser.add_argument(
        "bundle",
        nargs="?",
        type=Path,
        help="Bundle root directory (optional with --repo)",
    )
    parser.add_argument(
        "rest",
        nargs="*",
        default=[],
        help="Search keywords when bundle path is explicit (prefer --query with --repo)",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        help="Discover bundle under repo root (any project layout)",
    )
    parser.add_argument(
        "--query",
        "-q",
        default="",
        help="Search keywords (recommended with --repo)",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Deep bundle discovery with --repo",
    )
    parser.add_argument("--catalog", action="store_true", help="List all concept metadata")
    parser.add_argument("--type", dest="type_filter", help="Filter by frontmatter type")
    parser.add_argument("--tag", dest="tag_filter", help="Filter by tag")
    parser.add_argument("--path", dest="concept_path", help="Inspect one concept + links")
    parser.add_argument(
        "--links",
        action="store_true",
        help="With --path: show outbound links only (no body)",
    )
    parser.add_argument("--max", type=int, default=5, help="Max ranked results (default 5)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    query = args.query or " ".join(args.rest)

    if args.repo:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from okf_bundle import discover_bundles, resolve_bundle  # noqa: E402

        repo = args.repo.resolve()
        bundle = resolve_bundle(repo, deep=args.deep)
        if not bundle:
            print(f"ERROR: no OKF bundle found under {repo}", file=sys.stderr)
            print("Run discover_okf.py on the repo or pass an explicit bundle path.", file=sys.stderr)
            sys.exit(1)
        found = discover_bundles(repo, deep=args.deep)
        if len(found) > 1 and not args.json:
            print(
                f"# auto-selected bundle: {bundle} ({len(found)} candidates — pass explicit path to override)",
                file=sys.stderr,
            )
    elif args.bundle:
        bundle = args.bundle.resolve()
    else:
        print("ERROR: pass <bundle> or --repo <workspace-root>", file=sys.stderr)
        sys.exit(1)

    if not bundle.is_dir():
        print(f"ERROR: not a directory: {bundle}", file=sys.stderr)
        sys.exit(1)

    concepts = collect_concepts(bundle)
    if args.type_filter:
        needle = args.type_filter.lower()
        concepts = [(p, m, b) for p, m, b in concepts if needle in m.type.lower()]
    if args.tag_filter:
        needle = args.tag_filter.lower()
        concepts = [
            (p, m, b)
            for p, m, b in concepts
            if any(needle in t.lower() for t in m.tags)
        ]

    if args.concept_path:
        print_path_detail(bundle, concepts, args.concept_path, args.links, args.json)
        return

    if args.catalog or not query.strip():
        print_catalog(concepts, args.json)
        return

    terms = tokenize_query(query)
    scored_rows: list[tuple[int, Path, ConceptMeta, str]] = []
    for path, meta, body in concepts:
        score = score_concept(meta, body, terms)
        if score > 0:
            scored_rows.append((score, path, meta, body))
    scored_rows.sort(key=lambda row: (-row[0], row[2].path))
    print_matches(scored_rows, args.max, args.json)


if __name__ == "__main__":
    main()
