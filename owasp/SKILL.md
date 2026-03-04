---
name: owasp
description: Help find vulnerabilities using the OWASP Cheat Sheet Series and ASVS. Use whenever the user is doing a security review, hunting for bugs, assessing code for flaws, or asking about attack vectors, weak points, or what could go wrong. Use for injection (SQL, XSS, LDAP, command), auth/session issues, misconfigurations, insecure crypto, IDOR, CSRF, file upload risks, or any OWASP topic — and cite the relevant cheat sheets so the user knows both what to look for and how to fix it.
---

# OWASP Skill — Finding Vulnerabilities

**License and attribution.** The content in `references/cheatsheets/`, `references/cheatsheets_draft/`, and related reference files is from the [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) and the [OWASP Application Security Verification Standard (ASVS)](https://owasp.org/www-project-application-security-verification-standard/), used under the [Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA-4.0)](https://creativecommons.org/licenses/by-sa/4.0/) license. One file (`Infrastructure_as_Code_Security_Cheat_Sheet.md`) is Copyright 2021 Nokia, licensed under CC-BY-SA-3.0. This skill package is distributed under [CC-BY-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/). OWASP and Nokia are not affiliated with this skill.

Use the **OWASP Cheat Sheet Series** and **ASVS** to help **find vulnerabilities**: map code and flows to common flaw patterns, suggest where to look and what to test, and cite specific cheat sheets for both detection and remediation.

## Anatomy (skill-creator standard)

```
owasp/
├── SKILL.md
├── commands/                (standalone commands — see commands/README.md)
│   ├── README.md
│   ├── owasp-audit.md       (vulnerability audit; cite cheat sheets)
│   ├── owasp-asvs.md        (ASVS verification; IndexASVS mapping)
│   ├── owasp-scenarios.md   (edge cases, severity, mitigations, coverage)
│   └── owasp-cheatsheet.md  (look up / apply a specific cheat sheet)
├── evals/
│   └── evals.json
├── references/
│   ├── IndexASVS.md         (ASVS V1–V17 → cheat sheets; use TOC to jump)
│   ├── New_CheatSheet.md
│   ├── cheatsheet-index.md  (topic index for cheatsheets/ + cheatsheets_draft/)
│   ├── cheatsheets/         (published; see README.md for categories)
│   └── cheatsheets_draft/   (draft; see README.md for categories)
└── assets/
    └── (diagrams, media)
```

## Bundled resources — when to read

- **`references/cheatsheet-index.md`** — Find cheat sheets by vulnerability/theme (e.g. injection, auth, session, file upload). Use when mapping a feature or area to “what to check.”
- **`references/IndexASVS.md`** — Map verification areas (V1–V17) to cheat sheets. Use when the user is aligning to ASVS or wants a checklist of what could be wrong in a given area. Long file; use the TOC.
- **`references/New_CheatSheet.md`** — Only when drafting new OWASP-style content.
- **`assets/`** — When explaining attack flows or architectures (auth, authorization, segmentation).

When running **inside this repository**, you can also use the project root paths for the same content.

## How to use (finding vulnerabilities)

1. **Map area to vulnerability types**  
   Use `references/cheatsheet-index.md` to pick the right cheat sheet(s) for the code or flow (e.g. login → Authentication + Session Management; user input → Input Validation + Injection Prevention; file upload → File Upload). Name concrete vulnerability types (e.g. SQLi, XSS, IDOR, session fixation) and where they typically appear.

2. **Say what to look for and how to test**  
   From the relevant cheat sheet(s), extract: common failure modes, missing controls, and test ideas (e.g. “Check that …”, “Try …”). Cite the sheet so the user can run the checks and read full guidance.

3. **Tie findings to remediation**  
   For each vulnerability or risk, point to the OWASP guidance that describes how to fix or prevent it (same or related cheat sheet). Prefer allowlisting, defense in depth, and “validate early / encode on output” as in the series.

4. **Use ASVS when doing verification**  
   If the user is verifying against ASVS, use `references/IndexASVS.md` to list which cheat sheets cover each requirement and what to verify; frame as “what’s missing or weak” for that requirement.

## Conventions (from the series)

- Cheat sheets focus on actionable guidance: what goes wrong and how to prevent or detect it.
- Allowlisting is preferred over denylisting; input validation supports but does not replace encoding and injection controls.
- Cross-link between related topics (e.g. Input Validation ↔ XSS/SQL Injection prevention).

## Output expectations

- **When helping find vulnerabilities:** Name specific vulnerability types, where to look (component/flow/input), and which OWASP cheat sheet(s) to use for checks and fixes. Include concrete test ideas or failure modes from the sheets.
- Cite cheat sheets by filename or title (e.g. “Per [Input Validation Cheat Sheet](cheatsheets/Input_Validation_Cheat_Sheet.md)…”).
- For ASVS-related answers, mention the ASVS section and the IndexASVS-listed cheat sheets.

### Scenario-style analysis (edge cases and failure modes)

When the user asks for edge cases, failure modes, or scenario-style analysis:

1. **Group by category** — Use at least two of: Inputs (null, types, overflow, encoding), API/usage (missing params, auth, races), System (network, disk, time), Business (boundaries, workflows), Security (injection, replay, privilege).
2. **Severity** — Assign Critical / High / Medium / Low per item.
3. **Mitigations** — For each finding, give mitigations or test ideas; **include short code examples** (e.g. parameterized query, encoding call, validation snippet) where they clarify the fix. Cite the relevant OWASP cheat sheet.
4. **Simplified summary** — Provide a short, simplified version of the output: e.g. a compact table or bullet list (main categories, counts, top risks) so the user can scan quickly.
5. **Weights and coverage** — Optionally assign weights to categories (e.g. Security 40%, Inputs 30%) and a **coverage score** (e.g. percentage of areas or checks covered) so the user can see where analysis is strongest or missing.

## Using subagents (when available)

When the scope is **large** (full repo, many modules, or broad ASVS verification), use subagents if your environment supports them so work runs in parallel and finishes faster.

**When to split:**
- **Audit:** Scope spans multiple distinct areas (e.g. auth, input validation, file upload, APIs, crypto). Split by area: one subagent per area, each with this skill and a focused task (e.g. “Audit auth/session in [paths] using OWASP; cite cheat sheets; findings + remediation”).
- **ASVS verification:** User wants verification across many ASVS sections (e.g. V4–V8). Split by section or by logical group (e.g. V4+V5, V6+V7, V8); each subagent uses `references/IndexASVS.md` and the skill for its section(s).

**How to run:**
- Spawn one subagent per area or ASVS slice; give each the path to this skill (e.g. `owasp/SKILL.md`) and the specific scope (files/folders or ASVS section). Run them in parallel (e.g. up to 4 at a time).
- Each subagent follows the same workflow: map to vulnerability types, cite cheat sheets, list findings and remediation.

**After they finish:**
- Aggregate: merge findings from all subagents, deduplicate by issue type and location, then assign overall severity (Critical/High/Medium/Low) and a single risk or coverage summary for the user.
- If subagents are not available, do the same workflow yourself sequentially by area or ASVS section.
