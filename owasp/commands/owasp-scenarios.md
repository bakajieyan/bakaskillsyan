# OWASP Scenarios

**Edge cases and failure modes** (scenario-style) with OWASP alignment: group by category, assign severity, give mitigations and test ideas from the Cheat Sheet Series, plus coverage score.

**Skills:** `skills/owasp/SKILL.md` or `.cursor/skills/owasp/SKILL.md` — use scenario-style analysis from SKILL.md (categories, severity, mitigations, summary, weights/coverage).

**Scope:** Selected function, file, or area. If nothing selected, use open file or ask. Optional: user names a focus (e.g. "login", "file upload", "API").

**Do:** (1) Group by at least two of: Inputs (null, types, overflow, encoding), API/usage (missing params, auth, races), System (network, disk, time), Business (boundaries, workflows), Security (injection, replay, privilege). (2) Assign Critical/High/Medium/Low per item. (3) For each finding: mitigations or test ideas; include short code examples where they clarify the fix; cite the relevant OWASP cheat sheet. (4) Simplified summary (compact table or bullets: main categories, counts, top risks). (5) Optionally: weights per category and coverage score (%).

**Output:** Edge-case list (grouped) · Severity per item · Mitigations + cited cheat sheets · Short summary · Coverage score (%).
