# Epic Tracker

## Done

### Epic A - Environment & Tooling Setup

Status: partially complete where external manual setup is required, otherwise implemented.

- A1 Repository & Python environment scaffolding: done.
- A2 PostgreSQL database setup: done.
- A3 GitHub model repository setup: model repo exists at `mo-sameh1/mvp-phase1-model` with the required layer layout; fine-grained PAT has been configured aswell, done.
- A4 LangSmith tracing setup: env contract and smoke script added; real trace requires user-provided LangSmith settings plus Ollama, Groq, or Anthropic model access.

Implemented in:

```text
28f2d34 feat: scaffold epics a-b foundation
```

### Epic B - Data Layer

Status: implemented.

- B1 Core database schema and migrations: done.
- B2 Data access layer repository functions: done.

Verification already performed during implementation:

- `uv sync`
- `make lint`
- `make test`
- `uv run alembic upgrade head`
- `uv run alembic downgrade -1`
- `uv run alembic upgrade head`
- `psql` table listing as `mvp_app`

## Pending

### Epic C - ArchiMate Knowledge Base

Status: implemented as a conservative source-grounded metamodel foundation.

- `agents/skills/archimate-metamodel/SKILL.md` added.
- Structured element and relationship type tables added.
- Deterministic Python query utilities added under `agents.archimate_metamodel`.
- Tests verify valid elements, wrong-layer failures, unknown failures, approved specialization, 7Bots PDF-backed relationship examples, and fail-closed unsupported relationship pairs.

Important: broad relationship validation remains intentionally conservative. Add only relationship pairs explicitly backed by the official ArchiMate 3.2 material or the accepted 7Bots ArchiMate learning PDF.

### Epic D - Deep Agent Core Scaffold

Status: implemented as the runtime foundation for Epic E.

- D0 common model/evidence Pydantic schema: done in `agents/schema.py`.
- D1 filesystem backend configuration: done in `agents/runtime/filesystem.py`.
- D2 base `create_deep_agent` instantiation: done in `agents/runtime/deep_agent.py`.
- D3 placeholder subagent wiring smoke test: done in `agents/runtime/subagents.py` and `scripts/deepagent_subagent_smoke.py`.

Runtime contracts:

- `LLM_PROVIDER` supports `ollama`, `groq`, and `anthropic`.
- `/evidence/` is agent-readable and agent-write-denied.
- `/systems/` maps to the model repo checkout's `systems/` tree and is writable.
- `/skills/` exposes project skills and is agent-write-denied.
- Epic E subagent names are fixed as `strategy-analyst`, `business-analyst`, `code-analyzer`, `infra-analyzer`, and `integration-mapper`.

Verification:

- `make test` covers schema, filesystem routing, and mocked Deep Agent construction.
- `make epic-d-smoke` requires real provider and LangSmith environment values.

### Epic E - Ingestion Subagents

Five subagents:

- `strategy-analyst`
- `business-analyst`
- `code-analyzer`
- `infra-analyzer`
- `integration-mapper`

All must output schema-valid, evidence-cited elements.

### Epic F - Reconciler + Validator

MVP reconciler should be deterministic normalized-name matching. Validator must enforce schema/metamodel/evidence rules and halt on hard violations.

### Epic G - Git Versioning & PR Automation

Requires deterministic GitHub branch, commit, PR, and merge-webhook handling. Uses `artifact_versions.pr_number` and `artifact_versions.pr_url`.

### Epic H - Orchestration & Backend API

Wraps the ingestion pipeline in background jobs and exposes API endpoints needed by the frontend.

### Epic I - Frontend Model Viewer

React/Vite frontend for triggering runs, viewing job status, browsing model elements, and viewing artifact PR status.

### Epic J - End-to-End Validation

Synthetic demo evidence set and full acceptance test. This is the MVP finish line.

## External Actions Still Needed

- Fill `.env` with real GitHub and LangSmith values, plus Ollama, Groq, or Anthropic model settings.
- Run `make langsmith-smoke` after real secrets are available.
- Obtain the official ArchiMate 3.2 Specification if broad Appendix B relationship coverage is required beyond the accepted 7Bots learning PDF examples.
