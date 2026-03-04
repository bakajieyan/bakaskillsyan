# OWASP ASVS

**ASVS verification** for selected area or requirement set: map to V1–V17, list which cheat sheets cover each requirement, what to verify, and what’s missing or weak.

**Skills:** `skills/owasp/SKILL.md` or `.cursor/skills/owasp/SKILL.md` — use `references/IndexASVS.md` for ASVS → cheat sheet mapping; use TOC to jump.

**Scope:** Selected module/area, or user-named ASVS section(s) (e.g. "V4 Access Control", "V7 Cryptography"). If nothing selected, ask for area or list all V1–V17 with key cheat sheets.

**Do:** (1) Identify ASVS section(s) in scope. (2) From IndexASVS, list cheat sheets that support each requirement. (3) For each requirement, state what to verify and common gaps. (4) Frame as checklist: "what’s missing or weak" for that requirement.

**Output:** ASVS section(s) in scope · Requirement → cheat sheet(s) · Verification checklist · Gaps/risks · Suggested order of checks.

**Broad ASVS (many sections):** If verifying across V1–V17 or many sections, use subagents (see SKILL.md § Using subagents): split by ASVS section or group (e.g. V4+V5, V6+V7), run in parallel, then aggregate into one checklist.
