# OWASP Skill

Agent skill for **finding vulnerabilities** using the [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) ([GitHub](https://github.com/OWASP/CheatSheetSeries)) and the [OWASP Application Security Verification Standard (ASVS)](https://owasp.org/www-project-application-security-verification-standard/). Use it for security reviews, bug hunting, and code assessment — with cited cheat sheets for both what to check and how to fix issues.

[Overview](#overview) · [Structure](#structure) · [Usage](#usage) · [Commands](#commands) · [Attribution](#attribution)

## Overview

The skill helps map code and flows to common flaw patterns (injection, XSS, auth/session, IDOR, CSRF, file upload, misconfig, crypto, etc.), suggests where to look and what to test, and ties findings to OWASP remediation guidance. It supports ASVS verification (V1–V17) via an index that maps requirements to cheat sheets.

**When to use:** Security review, vulnerability assessment, attack-surface analysis, or any question about OWASP topics. The agent will name vulnerability types, point to components/flows, and cite specific cheat sheets for checks and fixes.

## Structure

```
owasp/
├── SKILL.md           # Agent instructions and conventions
├── README.md          # This file
├── commands/          # Standalone commands (see commands/README.md)
├── evals/             # Skill evals
├── references/        # Cheat sheets and indexes
│   ├── cheatsheet-index.md   # Topic → cheat sheet
│   ├── IndexASVS.md          # ASVS V1–V17 → cheat sheets
│   ├── cheatsheets/          # Published sheets
│   └── cheatsheets_draft/    # Draft sheets
└── assets/
```

Key references the agent uses: **cheatsheet-index.md** (find sheets by theme), **IndexASVS.md** (verification mapping; use TOC for long file).

## Usage

- **In Cursor:** Ensure the skill is available (e.g. under `skills/owasp/` or `.cursor/skills/owasp/`). Refer to it when doing security work: `@skills/owasp` or invoke one of the [commands](#commands).
- **Skill path:** `skills/owasp/SKILL.md` (project root) or `.cursor/skills/owasp/SKILL.md` (Cursor skills dir).

> [!TIP]
> For ASVS alignment, use the **owasp-asvs** command or ask explicitly for ASVS verification; the skill uses `references/IndexASVS.md` to map requirements to cheat sheets.

## Commands

Bundled commands live in `commands/`. Each can run on selected code, the open file, or the repo (dynamic scope).

| Command | Purpose |
|--------|--------|
| **owasp-audit** | Vulnerability audit: flaw types, cited cheat sheets, prioritized findings and remediation. |
| **owasp-asvs** | ASVS verification: map to V1–V17, checklist, gaps. |
| **owasp-scenarios** | Edge cases and failure modes: categories, severity, mitigations, coverage score. |
| **owasp-cheatsheet** | Look up or apply a specific cheat sheet (by topic or name) to selected code. |

Run by path (e.g. `@skills/owasp/commands/owasp-audit.md`) or copy the `.md` files into `.cursor/commands/` for the command palette. See **commands/README.md** for install and scope details.

## Attribution

Reference content in `references/cheatsheets/` and `references/cheatsheets_draft/` is from the [OWASP Cheat Sheet Series](https://github.com/OWASP/CheatSheetSeries) and ASVS, used under [CC-BY-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/). One file is © 2021 Nokia (CC-BY-SA-3.0). This skill package is distributed under CC-BY-SA-4.0. See **NOTICE** in this directory for full attribution, license terms, and disclaimer. OWASP and Nokia are not affiliated with this skill.
