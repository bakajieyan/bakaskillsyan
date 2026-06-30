---
name: bakaknowledgeyan
description: Creates, reads, validates, and maintains Open Knowledge Format (OKF) knowledge bundles — markdown + YAML frontmatter for agent-readable system context. Works on ANY repository (discover_okf.py locates the bundle; not tied to knowledge/ or a stack). ALWAYS use for knowledge bundles, agent wikis, Google knowledge-catalog-style docs, progressive disclosure, concept docs with frontmatter, linked tables/APIs/playbooks, codebase enrichment, "turn this repo into knowledge", OKF conformance, validate_okf.py fixes, or answering from an existing OKF bundle without reading every file — even if the user never says "OKF". Run query_okf.py or discover_okf.py before bulk-loading bundle markdown. Not for OWASP-only audits, OpenAPI/spec generation, single-file READMEs, ADRs, ER diagrams, vector/embedding KBs, explain-only chat, caveman/prose compress, git commit messages, prettier/formatting-only, or ORM migrations.
---

# Bakaknowledgeyan — OKF

OKF = `.md` + YAML frontmatter tree. No schema registry. No required tooling.

## Modes (token routing)

| Task | Load | Skip |
|------|------|------|
| **Answer from bundle** | `AGENTS.md` consume + `query_okf.py` + 1–3 concepts | Full SKILL, okf-spec, log, bulk indexes |
| **Author / enrich** | Workflows 1–2, 4 | Consume § unless also Q&A |
| **Validate / conformance** | Validation § + `okf-spec.md` if unsure | Whole bundle |

**Spec:** [references/okf-spec.md](references/okf-spec.md) — author/validate/conformance only.

---

## Any repository

Not tied to this repo. Any codebase, monorepo, or standalone OKF git repo.

| What | Rule |
|------|------|
| **Bundle** | Any OKF `.md` dir — name not required `knowledge/` |
| **Scripts** | `<skill-root>/scripts/` — bundle lives in target repo only |
| **Domain** | Tables, APIs, playbooks, services — project-specific |
| **Links** | Bundle-relative `/path/concept.md`; `resource` = path/URL in that repo |

### Resolve bundle root

1. User path → use it (`docs/architecture/`, `./okf/`, repo root if standalone).
2. Else discover:

```bash
python <skill-root>/scripts/discover_okf.py <repo-root>
python <skill-root>/scripts/discover_okf.py <repo-root> --deep   # non-standard layout
```

3. Multiple hits → user hint, or highest `confidence` + concept count; confirm if ambiguous.
4. None → Workflow 1 or ask user.

**Common:** `knowledge/`, `docs/knowledge/`, `okf/`, `docs/okf/`, repo root (standalone).

### Skill scripts

`<skill-root>` = folder with this `SKILL.md` (Cursor skill, symlink, or `bakaknowledgeyan/`).

```bash
python <skill-root>/scripts/discover_okf.py .
python <skill-root>/scripts/query_okf.py <bundle-root> --catalog
python <skill-root>/scripts/query_okf.py --repo . "auth rbac"
python <skill-root>/scripts/validate_okf.py <bundle-root>
```

Windows: `py` if `python` missing.

---

## OKF vs other formats

| Need | OKF | Else |
|------|-----|------|
| Agent/human system context | ✅ | |
| Linked concepts (tables, APIs, playbooks) | ✅ | |
| Machine API contracts | | OpenAPI, Protobuf |
| Column schema registry | | Avro, DB migrations |
| Long prose docs | | README, ADRs |

OKF references domain schemas; not replace.

---

## Terms

| Term | Meaning |
|------|---------|
| **Knowledge Bundle** | Self-contained OKF tree — distribution unit |
| **Concept** | One `.md` — frontmatter + body |
| **Concept ID** | Path sans `.md` (e.g. `tables/users`) |
| **Link** | Markdown link between concepts |
| **Citation** | External source for claim |

---

## Bundle layout

```
path/to/bundle/
├── index.md              # optional — dir listing
├── log.md                # optional — update history
├── <concept>.md
└── <subdir>/
    ├── index.md
    └── <concept>.md
```

**Reserved** (never concept filenames): `index.md`, `log.md`.

Group by domain (`tables/`, `apis/`, `playbooks/`). Producers pick structure; consumers tolerate partial trees.

---

## Concept format

YAML frontmatter → markdown body.

### Required frontmatter

```yaml
---
type: <Type name>    # REQUIRED — e.g. "PostgreSQL Table", "API Endpoint", "Playbook", "Metric"
---
```

### Recommended (priority order)

```yaml
---
type: API Endpoint
title: Create transaction
description: One-line summary for indexes and search snippets.
resource: https://api.example.com/v1/transactions   # Canonical URI for the underlying asset
tags: [billing, transactions]
timestamp: 2026-07-01T12:00:00Z                     # ISO 8601 last meaningful change
---
```

Producers MAY add keys. Consumers MUST preserve unknown keys; MUST NOT reject unknown fields.

### Body sections (conventional, optional)

| Heading | Purpose |
|---------|---------|
| `# Schema` | Columns, fields, req/res shape |
| `# Examples` | Usage (fenced code) |
| `# Citations` | Numbered external sources |

Structure (headings, lists, tables, code) over prose.

### Prose style (token save)

Concept **body** = caveman terse. Min tokens on load; keep retrieval signal.

**Drop:** articles, filler (`just`, `basically`), hedging, pleasantries, redundant lines.

**Keep exact:** frontmatter, `# Schema` tables, fenced code, `` `symbols` ``, links, paths, URLs, enums, constraints.

**Prefer:**
- Bullets over paragraphs
- Short labels (`# Purpose`, `# Rules`, `# Related`)
- One line per index `description`
- Playbook: `**Verb** — action.`
- **Max ~25 words** per non-list paragraph; `# Model` / `# Enforcement` → bullets only

**Don't compress:** frontmatter `description` (indexes/search — one clear sentence OK).

Example — before:
> A customer account represents an end user who can place orders. Customer-level settings apply across all storefronts unless overridden.

After:
> End-user account. Settings apply all storefronts unless storefront overrides.

---

## Cross-linking

**Preferred — bundle-relative absolute** (stable on move):

```markdown
See [customers](/tables/customers.md) for the join key.
```

**Also valid — relative:**

```markdown
See [neighbor](./other.md).
```

Links = relationships; type from prose. Broken links OK (target may not exist).

---

## Index (`index.md`)

No frontmatter (bundle-root MAY set `okf_version: "0.1"`).

```markdown
# Tables

* [Users](users.md) - Platform admin accounts scoped to tenants.
* [Transactions](transactions.md) - One row per completed payment.

# Related

* [APIs](../apis/) - REST endpoints that read/write these tables.
```

Entries SHOULD use linked concept `description`. Generate if missing.

---

## Log (`log.md`)

Optional. Newest first. Dates ISO `YYYY-MM-DD`.

```markdown
# Directory Update Log

## 2026-07-01
* **Update**: Added [transactions](/tables/transactions.md) schema.
* **Creation**: Initialized [tables](/tables/index.md) directory.

## 2026-06-15
* **Initialization**: Created bundle structure.
```

---

## Citations

External backing → doc bottom. `.mdc`, source code, URLs — **not** in-body markdown links (never append `.md` to non-markdown paths).

```markdown
# Citations

[1] [PostgreSQL docs — UUID type](https://www.postgresql.org/docs/current/datatype-uuid.html)
[2] [Schema source](src/db/migrations/001_orders.sql)
[3] [Module boundaries](.cursor/rules/module-boundaries.mdc)
```

---

## Workflows

### 1. New bundle

1. Pick root — any path or standalone git repo whose root **is** bundle.
2. Subdirs by domain (`tables/`, `apis/`, `services/`, `playbooks/`…).
3. Root `index.md` + `okf_version: "0.1"` + section listings.
4. Concepts — one asset/idea per file; required `type`; recommend `title`/`description`.
5. Cross-link `/path/to/concept.md` (bundle root, not repo root unless same).
6. Root `log.md` — **Initialization**.
7. Validate (below).

### 2. Enrich codebase

1. Explore target repo — schema, APIs, services, config, workflows (any stack).
2. Tangible assets → concepts + `resource` URIs (repo paths, OpenAPI URLs, console links).
3. Abstract knowledge (playbooks, conventions) → concepts sans `resource`.
4. Start high-value: auth, core entities, critical integrations, deployment.
5. Link concepts; cite under `# Citations`.
6. Update parent `index.md`; append `log.md`.

### 3. Consume bundle (default for Q&A)

**Never bulk-read bundle.** Progressive disclosure: indexes → ranked paths → targeted reads.

#### Load budget

| Step | Read | Skip |
|------|------|------|
| Orient | Root `index.md` (~30 lines) | Subdir indexes, concepts, `log.md` |
| Find | `query_okf.py` metadata | Full bodies |
| Answer | 1–3 matched concepts | Rest |
| Deep dive | Linked concepts one at a time | Siblings, upstream SPEC |

**Skip unless author/validate:** `okf-spec.md`, full `SKILL.md`, `log.md`, every `index.md`.

#### Query first

Resolve `<bundle-root>` (§ Any repository):

```bash
python <skill-root>/scripts/discover_okf.py <repo-root>
python <skill-root>/scripts/query_okf.py <bundle-root> --catalog
python <skill-root>/scripts/query_okf.py --repo <repo-root> "auth rbac"
python <skill-root>/scripts/query_okf.py <bundle-root> --type "PostgreSQL Table"
python <skill-root>/scripts/query_okf.py <bundle-root> --tag billing
python <skill-root>/scripts/query_okf.py <bundle-root> --path apis/create-order.md --links
```

Prints `~Ntok` per concept. Prefer matches **<800 tok** before following links.

#### Read order

1. Root `index.md` — pick domain section.
2. `query_okf.py` with question keywords (+ `--type` / `--tag` if obvious).
3. **Read** top 1–3 matched `.md` only (not dirs).
4. Neighbor? `--path <file> --links` → read **one** link, not all.
5. Subdir `index.md` only when browsing domain without query.

Artifacts (`query_log.txt`): **full script command** first line — auditable runs.

#### Stop rules

- Enough context → **stop**.
- Duplicate info → keep higher-scored path only.
- External link (`resource`, citation) → fetch only if body insufficient.
- Unknown `type` → generic concept; don't scan bundle for type docs.

#### Anti-patterns (consume)

- `rg` / glob all `**/*.md` into context
- Assume `knowledge/` without discover
- Read whole subdir because index lists them
- Load `okf-spec.md` or authoring SKILL for Q&A
- Follow every outbound link preemptively

### 4. Update concept

1. Edit body/frontmatter; bump `timestamp` on meaningful change.
2. Append dated `log.md`.
3. Refresh `index.md` if `description` changed.
4. Re-validate.

---

## Type names

Not centrally registered. Descriptive:

| Domain | Examples |
|--------|----------|
| Database | `PostgreSQL Table`, `PostgreSQL Enum`, `Database Migration` |
| API | `API Endpoint`, `API Service`, `Webhook` |
| Code | `NestJS Module`, `Package`, `Service` |
| Ops | `Playbook`, `Runbook`, `Alert` |
| Business | `Metric`, `Business Process`, `Domain Rule` |

Consumers tolerate unknown types.

---

## Conformance (OKF v0.1)

1. Every non-reserved `.md` → parseable YAML frontmatter.
2. Every frontmatter → non-empty `type`.
3. Reserved files follow index/log structure when present.

Soft (don't reject): missing optional fields, unknown types, broken links, missing indexes.

---

## Validation

After create/edit:

```bash
python <skill-root>/scripts/validate_okf.py <bundle-root>
```

Fix errors. Warnings (broken links, missing recommended fields) = informational.

---

## Example: PostgreSQL table

```markdown
---
type: PostgreSQL Table
title: orders
description: One row per customer order with line-item totals.
resource: src/db/migrations/001_orders.sql
tags: [billing, orders]
timestamp: 2026-07-01T10:00:00Z
---

# Schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `customer_id` | UUID | FK to [customers](/tables/customers.md) |
| `status` | enum | `pending`, `paid`, `shipped`, `cancelled` |
| `total` | NUMERIC(18,2) | Must equal sum of line items |

# Relationships

- Belongs to [customer](/tables/customers.md) via `customer_id`.
- Has many [order_items](/tables/order-items.md).

# Citations

[1] [Schema source](src/db/migrations/001_orders.sql)
```

---

## Anti-patterns

- `index.md` / `log.md` as concept filenames
- Concept without frontmatter or `type`
- Full OpenAPI/SQL dump — summarize + link
- Flat bundle, no indexes
- Fragile `../` chains vs `/bundle-root/` paths
- `.md` on non-markdown `resource` (e.g. `.mdc.md`) — cite in `# Citations` only

---

## Output (user asks for OKF)

1. Bundle dir structure — not one monolith unless asked.
2. `index.md` at root + each new subdir.
3. Root `log.md` — today init/update.
4. Run validator; report results.
5. Summarize: concept count, layout, next concepts.
6. Body prose = terse (§ Prose style). Tables/schema untouched.

---

## Scripts (bundled)

| Script | Purpose |
|--------|---------|
| `discover_okf.py` | Find bundle roots in any repo |
| `query_okf.py` | Catalog/search without loading bodies |
| `validate_okf.py` | OKF v0.1 conformance |
| `okf_bundle.py` | Shared discovery (imported) |

Eval (maintainers): `grade_eval.py`, `aggregate_benchmark.py`, `generate_review_static.py` — `evals/README.md`.
