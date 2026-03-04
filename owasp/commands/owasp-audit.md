# OWASP Audit

**OWASP vulnerability audit** of selected code or repo: map to OWASP flaw types, cite Cheat Sheet Series for detection and remediation, prioritized findings.

**Skills:** `skills/owasp/SKILL.md` or `.cursor/skills/owasp/SKILL.md` — use `references/cheatsheet-index.md` to pick cheat sheets; cite sheets by name.

**Scope:** Selected files/folder or full repo. If nothing selected, use open file or ask. Optional: user can name a focus (e.g. "auth", "APIs", "file upload").

**Do:** (1) Map area to vulnerability types (injection, XSS, auth/session, IDOR, CSRF, crypto, file upload, misconfig, etc.). (2) For each, say what to look for and how to test; cite the relevant cheat sheet(s). (3) Tie findings to remediation (allowlisting, validation, encoding, controls from the sheets). (4) Prioritize Critical/High/Medium/Low.

**Output:** Summary · Findings (file/line or area, type, severity) · Relevant OWASP cheat sheet(s) per finding · Remediation plan · Risk score (%).

**Large scope:** If auditing a full repo or many areas, use subagents (see SKILL.md § Using subagents): split by area (auth, input validation, file upload, APIs, etc.), run in parallel, then aggregate and deduplicate.
