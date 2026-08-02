---
name: stacking-prs
description: >
  Break large or multi-layer work into a chain of small stacked pull requests
  (gh stack). Use when the user says stacked PRs, stack this, gh stack, split
  into PRs, PR stack, reviewable layers, or when a change exceeds ~20–30 files /
  one coherent concern. Prefer GitHub stacked PRs + gh stack; squash-sync
  fallback when org uses squash-into-trunk without native stack rebase.
  Does NOT invent product features — only shapes delivery into reviewable layers.
---

# Stacking PRs

Break one large change into an ordered chain of small PRs. Each PR targets the
branch below it; the bottom targets the trunk (`dev` by default; override with
`--base`). Reviewers see one layer’s diff. Merge bottom-up.

**Pieces:** this skill · optional Cursor rule [`rules/stacking-prs.mdc`](rules/stacking-prs.mdc) ·
CLI/squash details → [`references/cli-and-squash-sync.md`](references/cli-and-squash-sync.md)

**Voice:** concise. Destructive git / force-push → clear English + confirm with user.

---

## WHEN

- Feature / AI dump too big for one reviewable PR
- Next work depends on unmerged PR below
- User asks to stack / `gh stack` / split PRs
- After a multi-layer build: several coherent layers ready

**Not when:** single small PR already ≤ layer budgets · cross-fork stacks (unsupported) · user forbids push/PR

---

## Layer budgets (hard)

| Metric | Target | Ceiling | Action if over |
| ------ | ------ | ------- | -------------- |
| Files changed (vs parent) | **≤20** | **30** | Split layer before `submit` |
| Net lines (add+del, ignore lock/gen) | **≤300** | **500** | Split or drop drive-by |
| Concerns / theme | **1** | 1 | New layer for next concern |
| Commits per layer | focused | — | Squash noise only if user asks |

Also:

- One layer = one review story (schema · API · UI · tests — not all four)
- Dependency rule: if A needs B, B is same layer or **below**
- No drive-by refactors in a layer
- Lockfiles / generated: count separately; call out in PR body if they dominate

Self-check before submit:

```bash
git diff --stat $(gh stack bottom 2>/dev/null; true)..HEAD
# or: git diff --stat origin/<parent-branch>...HEAD
```

Over ceiling → `gh stack add` / split commits into new top layer — do not submit oversized.

---

## Prerequisites

```bash
gh --version          # need ≥ 2.90 for gh-stack
gh extension install github/gh-stack
gh auth status
```

Optional agent skill (upstream): `gh skill install github/gh-stack`

Trunk = org integration base (`dev` by default; override with `--base`).

---

## STEPS

### 0. Design the stack (before code thrash)

Order layers by dependency — foundation first:

```
L1 data model / migration / shared types
L2 application / API / ports
L3 UI / wiring / middleware
L4 tests / docs / polish
```

Write the plan (short) and get user OK if >2 layers or budgets are tight.

### 1. Init bottom layer

```bash
gh stack init [--base dev] <branch-L1>
# implement · commit (Conventional Commits)
# self-review + lint/tests on this layer only
```

### 2. Add layers

```bash
gh stack add <branch-L2>
# … implement · commit · budget check …
gh stack add -Am "short message"   # commit + new top when current already has commits
```

Navigate: `gh stack up|down|top|bottom|switch|view`

### 3. Sync / rebase

```bash
gh stack sync                 # fetch · cascade rebase · push · PR state
# or after local fix on a mid layer:
gh stack rebase --upstack
gh stack push
```

Conflict → resolve → `gh stack rebase --continue` (or `--abort`).
Use the repo’s merge-conflict skill/procedure if present.

### 4. Submit

```bash
gh stack submit               # interactive titles/bodies
gh stack submit --auto        # CI / non-interactive (drafts by default)
gh stack submit --open        # ready for review
```

Each PR: focused title + 2–5 line “what this layer does / depends on below”.
Ask before push/PR unless user already ordered submit.

### 5. Review order

- Strong deps → review **bottom → top**; land fixes on the flagged layer, then `rebase --upstack`
- Independent reviewers → parallel OK
- Self-review every layer before requesting humans

### 6. Merge

```bash
gh stack merge                # interactive; bottom-up
gh stack merge --yes --squash # whole stack / up to chosen PR
```

Merge mid-stack → below merges too; above re-targets trunk.
Prefer merge queue when org has one.

### 7. Squash-into-trunk fallback (no native stack rebase)

When trunk uses **squash merge** and GitHub did not auto-fix the next base, use the
Pacheco three-step sync — see [`references/cli-and-squash-sync.md`](references/cli-and-squash-sync.md) § Squash sync.
Verify with diff-of-diffs before force-pushing anything.

---

## OUTPUT SHAPE

```
stack: <name or #N>
trunk: <dev|main|…>
layers:
  1. <branch> — <one-line theme> — files:N lines:~M — PR:#? | draft|open
  2. …
budget: OK | SPLIT needed @ layer K (files=X>30 | lines=Y>500 | multi-concern)
next: submit | sync | merge bottom | await review
```

---

## BOUNDARIES

| Do | Don't |
| -- | ----- |
| Prefer `gh stack` over hand-rolled base branches | Cross-fork stacks |
| Enforce file/line ceilings before submit | One mega-PR “to save time” |
| Fix on the owning layer, then upstack rebase | Land downstream commits into upstream |
| Ask before push / merge / force-with-lease | Silent force-push |
| Keep org branch prefixes (`feature/`, `bug/`, …) | Random branch names |

**Operate:** main thread for operate/sync/submit loops.
**Optional always-on rule:** [`rules/stacking-prs.mdc`](rules/stacking-prs.mdc) — budgets + when to stack.

---

## NON-GOALS

- Rewriting product specs / PRDs
- Implementing product code beyond shaping commits into layers
- Owning full delivery orchestration — stacks **land** work; other workflows still own phases
- Desktop GitHub app stacks (unsupported)

---

## Related

| Doc | Role |
| --- | ---- |
| [`references/cli-and-squash-sync.md`](references/cli-and-squash-sync.md) | CLI map + squash-sync procedure |
| [`rules/stacking-prs.mdc`](rules/stacking-prs.mdc) | Optional Cursor always-on rule |
| [`README.md`](README.md) | Install |
