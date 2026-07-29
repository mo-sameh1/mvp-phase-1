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

Status: implemented as source-grounded subagent contracts with deterministic fixture validation.

Five subagents:

- `strategy-analyst`
- `business-analyst`
- `code-analyzer`
- `infra-analyzer`
- `integration-mapper`

Implemented behavior:

- E1 reads strategy/motivation evidence and writes Motivation plus Strategy elements.
- E2 reads business evidence and writes Business elements.
- E3 reads code/schema/API evidence and writes Application elements with file/line evidence.
- E4 reads infrastructure evidence and writes Technology elements with file/line evidence where applicable.
- E5 appends evidence-cited relationships only when endpoint IDs exist and the Epic C metamodel
  marks the source-target pair approved.
- Unsupported relationship candidates are reported as skipped instead of being guessed into the model.

Verification:

- `make test`
- `make epic-e-smoke`
- `make epic-e-smoke EPIC_E_REPEAT=2`

### Epic F - Reconciler + Validator

Status: implemented as two Deep Agent assembly subagents backed by deterministic tools.

- F1 `reconciler`: merges exact normalized-name duplicates in place, retains evidence, rewrites
  relationship targets to canonical IDs, and reports ambiguous near-misses for human review.
- F2 `validator`: tolerantly scans reconciled model JSON, validates schema/evidence and Epic C
  ArchiMate rules, and writes JSON/Markdown reports.
- Reports are written under `systems/<system-id>/reports/<run-id>/`.

Verification:

- `make test`
- `make epic-f-smoke` requires real provider and LangSmith environment values.

### Epic G - Git Versioning & PR Automation

Status: implemented for GitHub-backed MVP model repo automation.

- G1 `commit_to_model`: creates/reuses `feature/ingest-<system-id>-<run-id>`, stages only
  `systems/<system-id>/`, commits, and pushes with token-backed HTTPS.
- G2 `open_pull_request`: creates/reuses a PR against `main`, builds the PR body from Epic F reports,
  and records a pending `artifact_versions` row with PR metadata.
- G3 webhook handler: verifies GitHub HMAC signatures, maps closed-unmerged PRs to `rejected`,
  maps reopened rejected PRs back to `pending`, approves merged PR artifacts idempotently, and
  refreshes `model_element_index` only after approval.

Verification:

- `make test`
- `make epic-g-smoke` created/reused a real GitHub PR when DB and GitHub env were available.

Current demo hygiene:

- The live Epic G demo PR branch and merge commit were cleaned from the model repo after recording.
- Demo application DB rows were cleared while preserving Alembic migration metadata.

### Epic H - Orchestration & Backend API

Status: implemented as the async Phase 1 backend entrypoint.

Implemented behavior:

- H1 `run_as_is_ingestion`: runs live Epic E ingestion, Epic F assembly/validation, then Epic G
  commit/PR automation only when validation passes.
- H2 background runner: uses FastAPI `BackgroundTasks` and the existing `jobs` table with
  `queued -> running -> succeeded/failed` status transitions.
- H3 REST API: exposes the five frontend-facing endpoints protected by `X-API-Key`.
- `GET /elements/{element_id}` reads full model JSON from the git-backed model repo using the
  indexed commit/path instead of duplicating full content into Postgres.

Verification:

- `make test`
- `make epic-h-smoke` is available for live API orchestration and may create a real GitHub PR.

### Epic I - Frontend Model Viewer

Status: implemented as a React/Vite/TypeScript reviewer UI.

Implemented behavior:

- I1 frontend scaffold: feature-oriented `frontend/src/` structure with typed API client, browser
  routing, shared components, env-based API config, and Vite `/api` proxy.
- I2 run/status screen: triggers As-Is ingestion, polls job status, persists the last job id per
  system in `localStorage`, and renders backend failure messages.
- I3 model browser/detail: lists indexed elements grouped by ArchiMate layer, filters/searches them,
  reads git-backed detail JSON, displays evidence citations as text, and links relationships to
  target element detail routes.
- I4 artifact versions: lists commit/run/approval metadata and opens GitHub PR links externally.

Verification:

- `make frontend-build`
- `make frontend-test`

## Pending

### Epic J - End-to-End Validation

Status: in progress.

Implemented behavior:

- J1 synthetic fixture: `test-fixtures/epic-j/` contains invalid and approved evidence variants for
  the same fictional permit modernization system. Both variants cover the five ingestion subagent
  source types and document duplicate, unsupported relationship, and invalid-reference edge cases.

Manual work remaining:

- J2 acceptance: run the invalid halt demo and the approved full flow from the frontend twice from a
  clean DB/model repo state.
- J3 runbook: finalize after J2 has been recorded and any manual discoveries have been folded back
  into `README.md`.

## External Actions Still Needed

- Fill `.env` with real GitHub and LangSmith values, plus Ollama, Groq, or Anthropic model settings.
- Run `make langsmith-smoke` after real secrets are available.
- Obtain the official ArchiMate 3.2 Specification if broad Appendix B relationship coverage is required beyond the accepted 7Bots learning PDF examples.
