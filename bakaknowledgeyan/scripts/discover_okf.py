#!/usr/bin/env python3
"""Discover OKF knowledge bundles in any repository."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from okf_bundle import discover_bundles  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find OKF bundle roots in a repository (any layout)",
    )
    parser.add_argument(
        "repo",
        type=Path,
        nargs="?",
        default=Path("."),
        help="Repository or workspace root (default: cwd)",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Scan entire tree (slower; use when bundle is not in common paths)",
    )
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not repo.is_dir():
        print(f"ERROR: not a directory: {repo}", file=sys.stderr)
        sys.exit(1)

    found = discover_bundles(repo, deep=args.deep)
    if not found:
        print(f"No OKF bundles under {repo}", file=sys.stderr)
        print(
            "Hint: pass an explicit bundle path to query_okf.py / validate_okf.py, "
            "or create a bundle (index.md + concepts with type frontmatter).",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.json:
        print(
            json.dumps(
                {
                    "repo": str(repo),
                    "bundles": [
                        {
                            "path": str(c.path),
                            "rel_path": c.rel_path,
                            "concepts": c.concept_count,
                            "has_index": c.has_index,
                            "okf_version": c.okf_version,
                            "confidence": c.confidence,
                        }
                        for c in found
                    ],
                },
                indent=2,
            )
        )
        return

    print(f"# OKF bundles under {repo} ({len(found)} found)")
    print("rel_path | concepts | okf_version | confidence")
    for c in found:
        version = c.okf_version or "-"
        print(f"{c.rel_path} | {c.concept_count} | {version} | {c.confidence}")

    if len(found) == 1:
        print(f"\n# use: query_okf.py {found[0].path} --catalog")
    else:
        print("\n# multiple bundles — pass explicit path or use query_okf.py --repo")


if __name__ == "__main__":
    main()
