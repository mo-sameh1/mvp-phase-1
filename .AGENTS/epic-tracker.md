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

Next likely epic. Requires authoring `archimate-metamodel/SKILL.md` from the official ArchiMate 3.2 specification and later smoke-testing it with a minimal Deep Agent.

Important: this is domain-critical. Do not invent ArchiMate rules from memory; cite and structure the official metamodel.

### Epic D - Deep Agent Core Scaffold

Requires common model/evidence Pydantic schema, filesystem backend configuration, base `create_deep_agent`, and placeholder subagent wiring.

Depends on A/B and partly on C.

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

- Create a fine-grained GitHub PAT scoped only to that repo.
- Fill `.env` with real GitHub and LangSmith values, plus Ollama, Groq, or Anthropic model settings.
- Run `make langsmith-smoke` after real secrets are available.
