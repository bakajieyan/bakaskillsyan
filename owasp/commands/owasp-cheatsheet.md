# OWASP Cheatsheet

**Look up or apply** a specific OWASP cheat sheet to selected code. Use when the user wants guidance from one topic (e.g. SQL injection, session management, file upload) or to map code to a named sheet.

**Skills:** `skills/owasp/SKILL.md` or `.cursor/skills/owasp/SKILL.md` — use `references/cheatsheet-index.md` to find sheets by topic; read the sheet from `references/cheatsheets/` or `references/cheatsheets_draft/`.

**Scope:** User names a topic or cheat sheet (e.g. "Input Validation", "OAuth2", "File Upload"); optionally select code to apply it to. If no topic given, infer from selection or suggest topics from the index.

**Do:** (1) Resolve topic to a specific cheat sheet (published or draft) via cheatsheet-index. (2) Summarize: what goes wrong, what to check, how to fix (from the sheet). (3) If code is selected, map it to the sheet: where it aligns, where it’s missing controls, and concrete changes. Cite the sheet by filename/title.

**Output:** Cheat sheet name + path · Summary (failure modes, checks, fixes) · If code selected: alignment, gaps, and recommended changes with citations.
