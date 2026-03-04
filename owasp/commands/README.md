# OWASP skill — bundled commands

Standalone commands that use the **OWASP skill** (Cheat Sheet Series + ASVS). Use them for security reviews, vulnerability hunting, and ASVS alignment.

## Commands (dynamic scope)

| Command | Purpose |
|--------|--------|
| **owasp-audit** | OWASP-style vulnerability audit: map code to flaw types, cite cheat sheets, prioritized findings and remediation. |
| **owasp-asvs** | ASVS verification for selected area: map to V1–V17, list relevant cheat sheets and what to verify. |
| **owasp-scenarios** | Edge cases and failure modes (scenario-style): categories, severity, mitigations, coverage score. |
| **owasp-cheatsheet** | Look up or apply a specific OWASP cheat sheet to selected code (by topic or name). |

**Dynamic scope:** For any command, **selection** = run on selected files/folder; **no selection** = use open file, repo root, or ask. You can also name a topic (e.g. "auth", "file upload") to focus the analysis.

## How to use

### Option A — Run from this package

- Reference a command by path, e.g. `@skills/owasp/commands/owasp-audit.md`, or paste its content into the chat.
- The command text tells the agent to use the OWASP skill (and where to find it).

### Option B — Install into `.cursor/commands/`

Copy the `.md` files from `skills/owasp/commands/` into `.cursor/commands/` so they appear in the command palette:

1. Copy `owasp-audit.md`, `owasp-asvs.md`, `owasp-scenarios.md`, `owasp-cheatsheet.md` to `.cursor/commands/`.
2. If the OWASP skill lives under `.cursor/skills/owasp/`, the **Skills** line in each command already points there. If the skill lives at `skills/owasp/` (project root), change the Skills path in each copied file to `skills/owasp/SKILL.md`.

### Skill path

- **In this repo (skill at project root):** `skills/owasp/SKILL.md`
- **Cursor skills directory:** `.cursor/skills/owasp/SKILL.md`

Each command uses one of these paths so the agent loads the OWASP skill and its references (cheatsheet-index, IndexASVS, etc.).
