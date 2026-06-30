# Trigger eval

20 queries — test `SKILL.md` description triggering.

| File | Purpose |
|------|---------|
| `trigger_eval.json` | 10 should-trigger + 10 should-not (+ 2 near-miss negatives) |

## Should trigger (`t01`–`t10`)

Formal/casual mix; paths; domain terms (LGU, tenant_id, OKF); full skill workflow tasks.

## Should not trigger (`n01`–`n12`)

Near-misses:
- `n03` — security review → owasp
- `n04` — OpenAPI (machine contract, not OKF)
- `n08` — caveman compress (different skill)
- `n11` — single markdown (not OKF bundle)
- `n12` — vector KB infra (not OKF)

## Usage

### Cursor (recommended — no Claude CLI)

Install for Agent discovery:

```powershell
# Repo root (once)
New-Item -ItemType Junction -Force -Path .cursor/skills/bakaknowledgeyan -Target bakaknowledgeyan
```

Offline score + manual chat check:

```bash
py bakaknowledgeyan/scripts/run_trigger_eval.py
py bakaknowledgeyan/scripts/score_trigger.py bakaknowledgeyan bakaknowledgeyan/evals/trigger_eval.json
```

Open [trigger_eval_review.html](trigger_eval_review.html). Paste each query in **Cursor Agent chat** — confirm `bakaknowledgeyan` loads (not `owasp`, etc.).

Results → `evals/trigger_eval_results.json`.

### Claude Code only (skill-creator)

`run_loop.py` needs **Claude CLI** (`claude -p`) + `ANTHROPIC_API_KEY`. From skill-creator, not this repo:

```bash
cd .cursor/skills/skill-creator
py -m scripts.run_loop ^
  --eval-set ../../bakaknowledgeyan/evals/trigger_eval.json ^
  --skill-path ../../bakaknowledgeyan ^
  --max-iterations 5
```

Does **not** work in Cursor IDE alone.

## Description

Iteration-final — [description-optimization.json](description-optimization.json). Offline heuristic: 10/10 should-trigger (`score_trigger.py`); real trigger = LLM + description.

Manual review: [trigger_eval_review.html](trigger_eval_review.html).

## Functional evals (`evals.json`)

| ID | Name | Tests |
|----|------|-------|
| 1 | tenant-onboarding | OKF authoring — entities, isolation, indexes |
| 2 | database-tables | PostgreSQL table concepts from schema |
| 3 | incident-playbook | Playbook + cross-links + citations |
| 4 | token-efficient-consume | `query_okf` before read; answer.md + files_read.txt |

Outputs: `bakaknowledgeyan-workspace/iteration-N/`.

**Iteration 1:** 97% with skill vs 87% baseline — [benchmark.md](../bakaknowledgeyan-workspace/iteration-1/benchmark.md), [review.html](../bakaknowledgeyan-workspace/iteration-1/review.html).

Grade / review:

```bash
py bakaknowledgeyan/scripts/grade_eval.py <outputs-dir> <repo-root> <eval-name>
py bakaknowledgeyan/scripts/aggregate_benchmark.py bakaknowledgeyan-workspace/iteration-1
py bakaknowledgeyan/scripts/generate_review_static.py bakaknowledgeyan-workspace/iteration-1 bakaknowledgeyan-workspace/iteration-1/review.html
```
