# Bakaknowledgeyan — agents

**When:** OKF bundles — create/read/validate/update. Trigger: knowledge bundles, agent wikis, concept docs, progressive indexes, tables/APIs/playbooks, "turn into knowledge", codebase enrichment — w/o saying "OKF".

**Universal:** Any repo. Never assume bundle path — discover or ask.

**How:** `SKILL.md` → bundle → concepts → cross-link → index → log → validate.

## Paths

| Var | Meaning |
|-----|---------|
| `<skill-root>` | This skill folder (`SKILL.md` + `scripts/`) |
| `<repo-root>` | Workspace / git root |
| `<bundle-root>` | OKF `.md` tree |

## Scripts

```bash
python <skill-root>/scripts/discover_okf.py <repo-root>
python <skill-root>/scripts/query_okf.py --repo <repo-root> "<keywords>"
python <skill-root>/scripts/query_okf.py <bundle-root> --catalog
python <skill-root>/scripts/validate_okf.py <bundle-root>
```

## Consume (Q&A default)

No bulk bundle load.

1. Confirm `<bundle-root>` — user path or `discover_okf.py`
2. Root `index.md` only (~30 lines)
3. `query_okf.py` — rank by metadata
4. Read 1–3 matched `.md`; `--path X --links` for one hop
5. Stop when answerable. Skip `log.md`, bulk indexes, `okf-spec.md`

→ **SKILL.md** § Workflow 3

## Author / validate

**SKILL.md** workflows 1–2, 4. `validate_okf.py` after edits. Terse body prose. External refs in `# Citations` only — no `.mdc.md` body links.

## Refs

- `references/okf-spec.md` — OKF v0.1
- [Google OKF SPEC](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)

## Subagents

Big scope → split `tables/` / `apis/` / `playbooks/`; parallel; merge root `index.md` + `log.md`.

## Output

Concept dir (not monolith); root + subdir indexes; `log.md`; validation report + concept count.
