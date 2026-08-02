# Stacking PRs — CLI & squash-sync reference

Load from [`SKILL.md`](../SKILL.md) only when operating a stack or recovering after squash-into-trunk.

---

## Install

```bash
gh extension install github/gh-stack
# optional (agents / Copilot):
gh skill install github/gh-stack
```

Requires GitHub CLI ≥ 2.90 (extension docs also list ≥ 2.0 for older builds — prefer current). Auth: `gh auth login`.

---

## Command map

| Command | Purpose |
| ------- | ------- |
| `gh stack init [branches…]` | New stack; `--base` trunk |
| `gh stack add [branch]` | New top branch; `-Am` stage-all + commit + branch |
| `gh stack view [--json\|-s]` | Show stack |
| `gh stack checkout <n\|pr\|branch>` | Fetch/switch stack |
| `gh stack modify` | Interactive reorder / fold / rename |
| `gh stack unstack` / `delete` | Drop local (+ remote) stack tracking |
| `gh stack submit` | Push + create/update PRs + link stack |
| `gh stack sync` | Fetch · rebase · push · PR state · prune |
| `gh stack rebase [--upstack\|--downstack]` | Cascading rebase |
| `gh stack push` | Push active branches (`--force-with-lease` after rebase) |
| `gh stack link …` | Link PRs without local tracking |
| `gh stack merge` | Merge stack / prefix bottom-up |
| `gh stack up\|down\|top\|bottom\|trunk\|switch` | Navigate |

### Exit codes (selected)

| Code | Meaning |
| ---- | ------- |
| 0 | OK |
| 2 | Not in a stack |
| 3 | Rebase conflict |
| 9 | Stacked PRs not enabled for repo |
| 10 | Modify session recovery needed |

---

## Happy path

```bash
gh stack init --base dev feature/SP-1-schema
# … commit L1 …
gh stack add feature/SP-1-api
# … commit L2 …
gh stack add -Am "feat: UI for SP-1"
gh stack view
gh stack submit --open
# reviews bottom → top
gh stack merge --yes --squash   # or merge via UI / queue
```

After a mid-layer fix:

```bash
gh stack checkout <layer-branch>
# commit fix
gh stack rebase --upstack
gh stack push
```

---

## Squash sync (Pacheco) — when trunk is squash-merged

Use when the bottom PR **squash-landed** on trunk and the next PR still contains pre-squash commits that conflict with the squash commit. Prefer GitHub/gh-stack cascading rebase when available; this is the manual recovery.

Context: parent branch tip was `A4`; landed on trunk as squash `M4`; previous trunk tip `M3` (`M4^`).

On the **next** branch (`branch2`):

```bash
git fetch
# 1) Sync to parent tip that was squashed (branch may be deleted — use A4 SHA)
git merge origin/branch1   # or: git merge <A4>

# 2) Sync trunk up to (but not including) the squash
git merge M3               # or: git merge M4^

# 3) Absorb squash without re-fighting identical trees
git merge -Xours M4
```

Then push (may need lease after history rewrite of merges — confirm with user before force).

### Verify (diff of diffs)

```bash
git diff --merge-base origin/dev my/branch/before > before.txt
git diff --merge-base origin/dev my/branch/after  > after.txt
# compare — only real conflict resolutions + trunk lines near your edits
```

Principles from that workflow:

- Ordinary work = regular commits (avoid rewrite while reviewers mid-review if possible)
- Upstream → immediate downstream only via merge (or `gh stack rebase`)
- Never land downstream commits into upstream
- After front-of-line is fixed, sync the rest with their immediate parent only

---

## Budget measurement

```bash
# files + shortstat vs parent branch
PARENT=$(git rev-parse --abbrev-ref HEAD@{-1} 2>/dev/null || true)
# better: parent from gh stack view / PR base
git diff --name-only origin/<parent>...HEAD | wc -l
git diff --shortstat origin/<parent>...HEAD
```

Ignore pure lockfile/generated noise when judging “review burden,” but still note them in the PR body.

---

## Further reading

- GitHub: About stacked pull requests
- GitHub: Stack code changes tutorial / quickstart
- GitHub: Managing stacked PRs
- `gh stack` CLI help: `gh stack --help`
- Dave Pacheco — stacked PRs + squash merge sync
