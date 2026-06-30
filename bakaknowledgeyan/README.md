# Bakaknowledgeyan

OKF skill — create/read/validate [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) bundles on any repo.

**Status:** Iteration-1 — 97% vs 87% baseline; consume +40% ([benchmark](../bakaknowledgeyan-workspace/iteration-1/benchmark.md)).

## Install

| Method | Path |
|--------|------|
| Monorepo | `bakaknowledgeyan/` → `AGENTS.md` → `SKILL.md` |
| Cursor | Symlink/copy → `.cursor/skills/bakaknowledgeyan/` |

Python 3, stdlib only.

## Structure

| Path | Role |
|------|------|
| `AGENTS.md` | Entry |
| `SKILL.md` | Workflows |
| `references/okf-spec.md` | OKF v0.1 |
| `scripts/` | discover, query, validate, package |
| `evals/` | Functional + [trigger evals](evals/trigger_eval.json) |

## Package

```bash
python scripts/package_skill.py . ../dist
```

→ `../dist/bakaknowledgeyan.skill`. Unzip to `.cursor/skills/` or `~/.cursor/skills/`. `evals/` excluded.

## Commands

```bash
python <skill-root>/scripts/discover_okf.py <repo-root>
python <skill-root>/scripts/query_okf.py --repo <repo-root> "keywords"
python <skill-root>/scripts/query_okf.py <bundle-root> --catalog
python <skill-root>/scripts/validate_okf.py <bundle-root>
```

Bundle path flexible: `knowledge/`, `docs/knowledge/`, `okf/`, custom, or repo root.

Example bundle: [`../knowledge/`](../knowledge/).

→ [SKILL.md](SKILL.md) · [okf-spec](references/okf-spec.md) · [evals](evals/README.md)
