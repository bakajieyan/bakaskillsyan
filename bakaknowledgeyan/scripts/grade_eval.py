#!/usr/bin/env python3
"""Grade OKF eval outputs against eval_metadata assertions."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

FILLER = re.compile(r"\b(just|basically|simply|actually|essentially)\b", re.I)
FRONTMATTER = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
BUNDLE_LINK = re.compile(r"\]\(/[^)]+\.md\)")


def find_bundle(outputs: Path) -> Path | None:
    candidates = [
        outputs / "knowledge",
        outputs,
    ]
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        md = list(candidate.rglob("*.md"))
        if not md:
            continue
        if any(p.name == "index.md" for p in md):
            return candidate
        # Flat table concepts at outputs root (eval baseline)
        if candidate == outputs and len([p for p in md if p.suffix == ".md" and p.name not in ("index.md", "log.md")]) >= 2:
            return candidate
        if candidate.name == "knowledge":
            return candidate
    return None


def concept_files(bundle: Path) -> list[Path]:
    reserved = {"index.md", "log.md"}
    return [p for p in bundle.rglob("*.md") if p.name not in reserved]


def body_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return FRONTMATTER.sub("", text, count=1)


def terse_prose_ok(bundle: Path) -> tuple[bool, str]:
    return terse_prose_ok_bundle(concept_files(bundle), bundle)


def terse_prose_ok_bundle(concepts: list[Path], bundle: Path) -> tuple[bool, str]:
    if not concepts:
        return False, "no concept files"
    fillers = []
    long_paras = []
    for p in concepts:
        body = body_text(p)
        label = p.name
        try:
            label = str(p.relative_to(bundle))
        except ValueError:
            pass
        if FILLER.search(body):
            fillers.append(label)
        for block in re.split(r"\n#+ ", body):
            lines = [ln.strip() for ln in block.splitlines() if ln.strip() and not ln.strip().startswith("|")]
            para = " ".join(ln for ln in lines if not ln.startswith(("-", "*", "`", "[")))
            if len(para.split()) > 35:
                long_paras.append(label)
    if fillers:
        return False, f"filler words in: {', '.join(fillers[:3])}"
    if len(long_paras) > len(concepts) // 2:
        return False, f"too many long prose blocks: {', '.join(long_paras[:3])}"
    return True, "terse prose heuristics pass"


def run_validate(bundle: Path, repo: Path) -> tuple[bool, str]:
    script = repo / "bakaknowledgeyan" / "scripts" / "validate_okf.py"
    root = bundle
    while root.name != "knowledge" and root.parent != root:
        if (root / "index.md").exists() and root.name in ("knowledge", "tenant-system"):
            break
        root = root.parent
    # validate full knowledge tree if bundle is subtree
    validate_path = bundle
    if "tenant-system" in str(bundle) and (repo / "knowledge").exists():
        validate_path = bundle
    r = subprocess.run(
        [sys.executable, str(script), str(validate_path)],
        capture_output=True,
        text=True,
    )
    out = r.stdout + r.stderr
    ok = r.returncode == 0
    return ok, out.strip().splitlines()[-1] if out else f"exit {r.returncode}"


def grade_consume(outputs_dir: Path) -> dict:
    expectations: list[dict] = []

    def add(text: str, passed: bool, evidence: str):
        expectations.append({"text": text, "passed": passed, "evidence": evidence})

    answer = outputs_dir / "answer.md"
    files_read = outputs_dir / "files_read.txt"
    query_log = outputs_dir / "query_log.txt"

    if answer.exists():
        text = answer.read_text(encoding="utf-8").lower()
        ok = "tenant_id" in text or "tenant id" in text
        add(
            "answer.md exists and mentions tenant_id isolation",
            ok,
            "tenant_id mentioned" if ok else "missing tenant_id in answer",
        )
        catalog_dump = text.count(".md") > 8 or len(text) > 8000
        add(
            "answer does not paste full bundle catalog",
            not catalog_dump,
            "concise answer" if not catalog_dump else "answer looks like bulk dump",
        )
    else:
        add("answer.md exists and mentions tenant_id isolation", False, "missing answer.md")
        add("answer does not paste full bundle catalog", False, "missing answer.md")

    if query_log.exists():
        try:
            ql = query_log.read_text(encoding="utf-8-sig").lower()
        except UnicodeDecodeError:
            ql = query_log.read_text(encoding="utf-16").lower()
        ok = "query_okf" in ql or "discover_okf" in ql
        add(
            "query_log.txt exists and references query_okf.py or discover_okf.py",
            ok,
            "query script referenced" if ok else "no query_okf/discover_okf in log",
        )
    else:
        add(
            "query_log.txt exists and references query_okf.py or discover_okf.py",
            False,
            "missing query_log.txt",
        )

    if files_read.exists():
        lines = [ln.strip() for ln in files_read.read_text(encoding="utf-8").splitlines() if ln.strip()]
        add(
            "files_read.txt lists at most 4 file paths",
            len(lines) <= 4,
            f"{len(lines)} paths listed",
        )
        joined = files_read.read_text(encoding="utf-8").lower()
        hit = "tenant-id-isolation" in joined or "tenant_id" in joined
        add(
            "files_read.txt includes tenant-id-isolation concept or query matched it",
            hit,
            "isolation path listed" if hit else "isolation concept not in files_read",
        )
    else:
        add("files_read.txt lists at most 4 file paths", False, "missing files_read.txt")
        add(
            "files_read.txt includes tenant-id-isolation concept or query matched it",
            False,
            "missing files_read.txt",
        )

    passed = sum(1 for e in expectations if e["passed"])
    total = len(expectations)
    return {
        "expectations": expectations,
        "pass_rate": passed / total if total else 0,
        "passed": passed,
        "total": total,
    }


def grade_run(outputs_dir: Path, repo: Path, eval_name: str) -> dict:
    if eval_name == "token-efficient-consume":
        return grade_consume(outputs_dir)

    bundle = find_bundle(outputs_dir)
    expectations: list[dict] = []

    def add(text: str, passed: bool, evidence: str):
        expectations.append({"text": text, "passed": passed, "evidence": evidence})

    if not bundle:
        add("bundle exists", False, "no knowledge/ output found")
        return {"expectations": expectations, "pass_rate": 0.0, "passed": 0, "total": 0}

    md_files = list(bundle.rglob("*.md"))
    concepts = concept_files(bundle)
    concepts_db: list[Path] = []

    # Bundle structure (strict — discriminates incomplete baselines)
    index_files = [p for p in md_files if p.name == "index.md"]
    root_index = min(index_files, key=lambda p: len(p.parts)) if index_files else None
    root_log = next((p for p in md_files if p.name == "log.md"), None)

    add("Root index.md exists at bundle root", root_index is not None, str(root_index or "missing"))
    if eval_name in ("tenant-onboarding", "database-tables", "incident-playbook"):
        okf = root_index and "okf_version" in root_index.read_text(encoding="utf-8")
        add("Root index.md declares okf_version in frontmatter", bool(okf), "okf_version present" if okf else "missing okf_version")
    add("Root log.md exists at bundle root", root_log is not None, str(root_log or "missing"))
    if root_log:
        log_text = root_log.read_text(encoding="utf-8")
        has_entry = bool(re.search(r"## \d{4}-\d{2}-\d{2}", log_text))
        add("Root log.md has dated entry (YYYY-MM-DD)", has_entry, "dated heading found" if has_entry else "no date heading")

    if eval_name == "database-tables":
        tables_idx = bundle / "tables" / "index.md"
        add("tables/index.md subdirectory index exists", tables_idx.exists(), str(tables_idx if tables_idx.exists() else "missing"))

    if eval_name == "tenant-onboarding":
        org = any("organization" in p.stem for p in concepts)
        tenant = any(p.stem == "tenant" or p.stem.endswith("tenant") for p in concepts)
        add("Concept files exist for Organization and Tenant with non-empty type frontmatter", org and tenant, f"org={org} tenant={tenant}")
        iso = any("isolation" in p.stem or "tenant-id" in p.stem for p in concepts)
        add("A concept or section documents tenant_id isolation", iso, f"isolation concept={iso}")
        links = sum(1 for p in concepts if BUNDLE_LINK.search(body_text(p)))
        add("Cross-links use bundle-relative /path/concept.md format", links >= 2, f"{links} bundle-relative links")

    elif eval_name == "database-tables":
        tables_dir = bundle / "tables"
        if tables_dir.is_dir():
            concepts_db = [p for p in tables_dir.glob("*.md") if p.name != "index.md"]
        else:
            concepts_db = [p for p in bundle.glob("*.md") if p.name not in ("index.md", "log.md")]
        tables = {p.stem for p in concepts_db}
        for t in ("tenants", "admins", "transactions"):
            hit = t in tables
            add(f"Concept file for {t} with PostgreSQL Table type", hit, f"found={hit}")
        for p in concepts_db:
            if p.stem in ("tenants", "admins", "transactions"):
                body = body_text(p)
                add(f"{p.stem} has # Schema table", "# Schema" in body and "|" in body, p.name)
        idx = tables_dir / "index.md" if tables_dir.is_dir() else bundle / "index.md"
        add("Parent index lists all three table concepts", idx.exists() and all(t in idx.read_text(encoding="utf-8") for t in ("tenants", "admins", "transactions")) if idx.exists() else False, str(idx))
        concepts = concepts_db

    elif eval_name == "incident-playbook":
        playbooks_dir = bundle / "playbooks"
        if playbooks_dir.is_dir():
            pb_candidates = [p for p in playbooks_dir.glob("*.md") if p.name != "index.md"]
        else:
            pb_candidates = [p for p in concepts if "leakage" in p.stem or "cross-tenant" in p.stem]
        pb = pb_candidates[0] if pb_candidates else None
        add("Playbook-type concept exists for cross-tenant data leakage", pb is not None, str(pb or "missing"))
        if pb:
            b = body_text(pb)
            add("Body includes Trigger and Steps sections", "# Trigger" in b and "# Steps" in b, pb.name)
            rbac_links = len(re.findall(r"\]\(/[^)]*(auth|rbac|isolation|tenant)[^)]*\.md\)", b, re.I))
            add("Links to at least two related auth/RBAC or isolation concepts", rbac_links >= 2, f"{rbac_links} links")
            add("Citations section references module boundary rules", "# Citations" in b and "module-boundaries" in b, "citations checked")
            steps_terse = "**" in b and "# Steps" in b
            add("Playbook steps use terse format: bold verb labels, minimal filler", steps_terse, "bold step labels" if steps_terse else "missing")
        playbooks_idx = bundle / "playbooks" / "index.md"
        add("playbooks/index.md subdirectory index exists", playbooks_idx.exists(), str(playbooks_idx if playbooks_idx.exists() else "missing"))

    v_ok, v_ev = run_validate(bundle, repo)
    add("validate_okf.py exits 0 when run against the bundle", v_ok, v_ev)

    if eval_name != "incident-playbook":
        check_concepts = concepts_db if eval_name == "database-tables" else concepts
        t_ok, t_ev = terse_prose_ok_bundle(check_concepts, bundle)
        add("Concept bodies use terse prose: bullets over paragraphs, no filler words", t_ok, t_ev)

    passed = sum(1 for e in expectations if e["passed"])
    total = len(expectations)
    return {
        "expectations": expectations,
        "pass_rate": passed / total if total else 0,
        "passed": passed,
        "total": total,
    }


def main() -> None:
    if len(sys.argv) != 4:
        print("Usage: grade_eval.py <outputs_dir> <repo_root> <eval_name>")
        sys.exit(1)
    outputs = Path(sys.argv[1]).resolve()
    repo = Path(sys.argv[2]).resolve()
    name = sys.argv[3]
    result = grade_run(outputs, repo, name)
    out = outputs / "grading.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
