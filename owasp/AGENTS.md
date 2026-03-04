# OWASP Skill — for agents

**When to use:** Security reviews, vulnerability hunting, assessing code for flaws, or any OWASP topic (injection, auth, session, XSS, CSRF, file upload, ASVS, attack vectors, weak points). Use the skill whenever the user asks what could go wrong or how to fix a security issue — and **cite the relevant cheat sheets** for both detection and remediation.

**Instructions:** Read **SKILL.md** in this directory for full workflow (map area → vulnerability types, what to look for, remediation, ASVS verification) and when to load each reference.

**References (load as needed):**
- `references/cheatsheet-index.md` — Find cheat sheets by topic (injection, auth, session, file upload, etc.).
- `references/IndexASVS.md` — Map ASVS V1–V17 to cheat sheets; use TOC for long file.
- `references/New_CheatSheet.md` — Only when drafting new OWASP-style content (e.g. webhook security).

**Commands:** See `commands/README.md`. Bundled commands: **owasp-audit** (vulnerability audit), **owasp-asvs** (ASVS verification), **owasp-scenarios** (edge cases / failure modes), **owasp-cheatsheet** (look up a specific sheet). Selection = run on selected files; no selection = open file or repo root.

**Subagents:** For large scope (full repo, many areas, or broad ASVS), use subagents if available: split by area (auth, input validation, file upload, etc.) or by ASVS section; run one subagent per slice in parallel with this skill; then aggregate and deduplicate findings. See **SKILL.md** § Using subagents.
