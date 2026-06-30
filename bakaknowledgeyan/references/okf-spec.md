# OKF Reference — v0.1 Draft

Source: [GCP knowledge-catalog OKF SPEC](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)

OKF = markdown dir + YAML frontmatter. Metadata/context around data/systems.

---

## Goals / non-goals

| Goals | Non-goals |
|-------|-----------|
| Enrichment agents write target | Fixed concept taxonomy |
| Consumption agents read/traverse | Storage/query infra |
| Cross-org exchange | Replace Avro/Protobuf/OpenAPI — OKF references only |
| Min required fields only | |

---

## Terms

| Term | Def |
|------|-----|
| Knowledge Bundle | Self-contained doc hierarchy |
| Concept | One `.md` unit |
| Concept ID | Path minus `.md` |
| Frontmatter | YAML between `---` |
| Body | After frontmatter |
| Link | Concept → concept |
| Citation | Concept → external source |

---

## Bundle structure

```
path/to/bundle/
├── index.md
├── log.md
├── <concept>.md
└── <subdirectory>/ …
```

Dist: git (preferred), tarball, subdir in larger repo.

| Reserved | Purpose |
|----------|---------|
| `index.md` | Dir listing |
| `log.md` | Update history |

Other `.md` = concepts.

---

## Concept

### Frontmatter

```yaml
---
type: <Type name>                  # REQUIRED
title: <Optional display name>
description: <Optional one-line summary>
resource: <Optional canonical URI>
tags: [<tag>, …]
timestamp: <ISO 8601 datetime>
# … producer-defined extensions
---
```

**Required:** `type`. **Recommended:** `title`, `description`, `resource`, `tags`, `timestamp`. **Extensions:** producers MAY add; consumers preserve.

### Body sections

| Heading | Purpose |
|---------|---------|
| `# Schema` | Columns/fields |
| `# Examples` | Usage |
| `# Citations` | External sources |

---

## Links

**Bundle-relative absolute (preferred):**

```markdown
[customers](/tables/customers.md)
```

**Relative:**

```markdown
[neighbor](./other.md)
```

Relationship from prose. Directed untyped edges. Broken links tolerated.

---

## Index

No frontmatter (bundle-root MAY `okf_version: "0.1"`).

```markdown
# Section Heading

* [Title](relative-url) - description from concept frontmatter
```

Synthesize if absent.

---

## Log

Newest first. Date `YYYY-MM-DD`.

```markdown
## 2026-05-22
* **Update**: Added [concept](/path/concept.md).
* **Creation**: Established [playbook](/playbooks/x.md).
```

---

## Citations

```markdown
# Citations

[1] [Source title](https://example.com/...)
```

---

## Conformance v0.1

1. Non-reserved `.md` → parseable frontmatter
2. Non-empty `type`
3. Reserved files follow index/log structure

Don't reject: missing optional fields, unknown types/keys, broken links, missing indexes.

---

## Versioning

Minor = backward-compatible. Major = breaking. Bundle-root `index.md` MAY declare `okf_version: "0.1"`.

---

## Example

See `SKILL.md` § Example. Full GCP samples: upstream SPEC Appendix A.
