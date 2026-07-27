# Architecture Contracts

These are project-level decisions future work must preserve unless the user explicitly changes direction.

## Repository Boundaries

- This repo is the engineering application repo.
- A separate GitHub model repo stores generated architecture artifacts.
- Do not mix source evidence, generated model artifacts, and application code in the same authority boundary.

## MVP System Identity

- Initial system id: `demo-legacy-system`.
- Required model repo layout:

```text
systems/demo-legacy-system/as-is/motivation/.gitkeep
systems/demo-legacy-system/as-is/strategy/.gitkeep
systems/demo-legacy-system/as-is/business/.gitkeep
systems/demo-legacy-system/as-is/application/.gitkeep
systems/demo-legacy-system/as-is/technology/.gitkeep
```

## Traceability Contract

- Every future model element must include at least one evidence citation.
- Evidence citations should include source type, locator, and excerpt.
- Code evidence locators should use file path plus line range where possible.
- `artifact_versions` is the join between generated artifacts, git commits, PR approval, and agent run tracing.
- `artifact_versions.pr_number` and `artifact_versions.pr_url` exist now because Epic G and Epic I need direct PR traceability.

## Database Authority

- The model repo is the source of truth for full model content.
- The database stores indexes, statuses, and links for fast application queries.
- Avoid duplicating full model JSON into relational tables unless a later task explicitly requires it.

## Schema Design

- Current MVP is single-tenant and intentionally has no `tenant_id` columns.
- Names and data-access boundaries should remain easy to extend to tenant-scoped access later.
- Use Alembic migrations for all schema changes.
- Do not hand-run schema changes outside migrations.

## Agent Runtime Direction

- The orchestrator owns long-lived phase runs and interview loops.
- Subagents are specialized and stateless task calls.
- Agent runtime integration must go through `agents/runtime/` adapters rather than direct `create_deep_agent` calls scattered through feature code.
- LLM provider selection must remain configurable through `LLM_PROVIDER` with supported providers `ollama`, `groq`, and `anthropic`.
- Deep Agent filesystem access is split into `/evidence/` for read-only source material, `/systems/` for writable model artifacts, and `/skills/` for read-only project skills.
- The ArchiMate metamodel skill must ground later ingestion, reconciliation, and validation.
- `agents/skills/archimate-metamodel/data/*.json` is the deterministic validator authority; `SKILL.md` is the agent-readable guide.
- Relationship pairs not marked `review_status = "approved"` must fail closed until supported by the official ArchiMate 3.2 material or the accepted 7Bots ArchiMate learning PDF.
- Epic E ingestion profiles live under `agents/ingestion/`; prompts may extract candidates, but schema validation, ArchiMate validation, target-ID checks, and path conventions decide what is accepted.
- Ingestion writes one JSON file per element under `/systems/<system-id>/as-is/<layer>/<id>.json`.
- The integration mapper may append relationships only to existing model elements and must report unsupported or unapproved candidates as skipped.
- Epic F assembly uses real `reconciler` and `validator` subagents, but deterministic Python tools are the authority for merge and validation decisions.
- Reconciler MVP merges only exact normalized-name duplicates within the same layer and ArchiMate type; ambiguous near-misses are review items, not auto-merges.
- Validator reports are committed artifacts for later PR review. Hard validation failures should halt progression before GitHub PR creation.

## Security Contract

- Secrets live in `.env` or deployment secret stores, never in git.
- `.env.example` may contain placeholders only.
- GitHub PAT for the model repo must be fine-grained and scoped only to that repo.
- Future webhook endpoints must verify GitHub signatures before marking artifacts approved.
