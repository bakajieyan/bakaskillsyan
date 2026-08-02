# Stacking PRs (skill)

Break large or multi-layer work into a chain of small stacked pull requests
(`gh stack`). Extracted from the typedbyhand v4 agent pack; standalone here.

## Contents

| Path | Description |
|------|-------------|
| `SKILL.md` | When to stack, layer budgets, `gh stack` steps |
| `references/cli-and-squash-sync.md` | CLI map + squash-into-trunk sync |
| `rules/stacking-prs.mdc` | Optional Cursor always-on rule (budgets) |

## Usage

Agent loads the skill when the description matches (stacked PRs, `gh stack`,
split into PRs, change exceeds ~20–30 files / one concern).

### Install into a Cursor project

```powershell
Copy-Item -Recurse .\stacking-prs <target-repo>\.cursor\skills\stacking-prs
# optional always-on rule:
Copy-Item .\stacking-prs\rules\stacking-prs.mdc <target-repo>\.cursor\rules\stacking-prs.mdc
```

## Prerequisites

```bash
gh --version
gh extension install github/gh-stack
gh auth status
```

Trunk defaults to `dev`; override with `gh stack init --base <trunk>`.

## Layer budgets

| Metric | Target | Ceiling |
| ------ | ------ | ------- |
| Files (vs parent) | ≤20 | 30 |
| Net lines (excl. lock/gen when judging) | ≤300 | 500 |
| Concerns / theme | 1 | 1 |

## License

Part of [bakaskillsyan](https://github.com/bakajieyan/bakaskillsyan) — MIT (repo root `LICENSE`).
