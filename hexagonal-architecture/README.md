# Hexagonal Architecture (skill)

Agent skill for designing and implementing Hexagonal Architecture (Ports & Adapters) in backend systems.

## Contents

| Path | Description |
|------|-------------|
| `SKILL.md` | Skill definition: when to trigger, concepts, workflow, examples table |
| `references/` | Reference docs (LAYERS, HEXAGONAL, DDD-STRATEGIC, DDD-TACTICAL, CQRS-EVENTS, TESTING, CHEATSHEET). Sourced from [robust-skills/clean-ddd-hexagonal/references](https://github.com/ccheney/robust-skills/tree/main/skills/clean-ddd-hexagonal/references) |
| `examples/` | Framework-specific guides (NestJS, ElysiaJS, Hono) |
| `evals/` | Test prompts (`evals.json`) and trigger-eval set for description optimization (`trigger_eval_set.json`) |
| `NOTICE` | Third-party and external material attribution |

## Usage

The skill is loaded by the agent when the description matches (e.g. designing backend structure, ports and adapters, refactoring toward clean architecture). For evals and iteration, use the **skill-creator** skill; see the “Skill maintenance” section at the end of `SKILL.md`.

## License

This skill is part of the repository and is subject to the **LICENSE** in the repository root (MIT License). See [NOTICE](NOTICE) for third-party and external material attribution.
