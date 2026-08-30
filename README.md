# 7bots.ai MVP Phase 1

<p align="center">
  <img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img alt="React Vite" src="https://img.shields.io/badge/frontend-React%20%2B%20Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/database-PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white">
  <img alt="LangSmith" src="https://img.shields.io/badge/tracing-LangSmith-1C3C3C?style=for-the-badge">
</p>

<p align="center">
  <strong>Agentic AI pipeline for extracting, validating, reviewing, and browsing evidence-grounded ArchiMate As-Is models.</strong>
</p>

---

## What This Repo Is

This repository is the application codebase for the 7bots.ai Phase 1 MVP. It proves the As-Is modernization loop for one legacy system:

```text
Evidence -> ingestion subagents -> ArchiMate model JSON -> reconciliation + validation
         -> GitHub pull request -> human approval -> indexed model viewer
```

The generated architecture model is intentionally stored in a separate GitHub model repository. This application repo contains the backend, agents, frontend, tests, fixtures, and developer runbook.

## Current Scope

The implemented MVP covers Epics A through J:

| Epic | Area | Status |
| --- | --- | --- |
| A | Environment, tooling, model repo setup, LangSmith setup | Implemented, with manual secret setup |
| B | PostgreSQL schema, Alembic migrations, repository helpers | Implemented |
| C | Source-grounded ArchiMate 3.2 metamodel skill | Implemented |
| D | Deep Agent runtime scaffold and shared schema | Implemented |
| E | Five ingestion subagents | Implemented |
| F | Reconciler and validator assembly subagents | Implemented |
| G | Git commit, GitHub PR automation, webhook approval | Implemented |
| H | Async backend orchestration and API | Implemented |
| I | React/Vite frontend model viewer | Implemented |
| J | End-to-end fixture, acceptance flow, README runbook | Implemented by this runbook |

## Repository Map

```text
agents/
  archimate_metamodel/      Deterministic ArchiMate lookup utilities.
  assembly/                 Epic F reconciler and validator subagents/tools.
  ingestion/                Epic E ingestion subagent profiles and write tools.
  runtime/                  Deep Agent provider, filesystem, and base-agent wiring.
  skills/archimate-metamodel/
                            Agent-readable skill plus structured metamodel data.

backend/
  api/                      FastAPI app, protected API routes, webhook route.
  config/                   Settings loaded from .env.
  database/                 SQLAlchemy models and session setup.
  gitops/                   Local git, GitHub HTTP, PR body, webhook, index refresh.
  orchestration/            Async Phase 1 job runner and pipeline orchestration.
  repository/               Database access helpers.

frontend/
  src/api/                  Typed API client.
  src/app/                  App shell and routes.
  src/features/             Run, model element, and artifact-version screens.
  src/components/           Reusable UI components.

test-fixtures/
  epic-e/                   Deterministic ingestion fixture.
  epic-f/                   Reconciliation and validator fixtures.
  epic-j/                   Final invalid and approved acceptance fixtures.

tests/                      Backend, agent, gitops, orchestration, and API tests.
```

## Architecture Boundaries

Keep these boundaries clear:

| Boundary | Source of truth |
| --- | --- |
| Application code | This repo |
| Full generated model JSON | Separate model repo, under `systems/<system-id>/as-is/` |
| Fast query indexes and run state | PostgreSQL |
| Human approval | GitHub pull request review |
| Agent traces | LangSmith |
| Source evidence | Local `EVIDENCE_ROOT`, never real client data in git |

The database stores statuses, artifact metadata, and model indexes. It does not own the full model content; the model repo does.

## Prerequisites

Install these before starting from a clean checkout:

| Tool | Why it is needed |
| --- | --- |
| Git | Clone this repo and the model repo. |
| Python 3.11+ | Backend, agents, scripts, tests. |
| `uv` | Python dependency and command runner. |
| Docker Desktop or Docker Engine | Local PostgreSQL. |
| Node.js 20+ and npm | Frontend development and tests. |
| `psql` client | DB smoke checks and cleanup commands. |
| Cloudflare Tunnel or another HTTPS tunnel | Local GitHub webhook delivery for the final demo. |

Check versions:

```bash
git --version
python3 --version
uv --version
docker --version
node --version
npm --version
psql --version
```

## Clone Layout

Use this sibling-folder layout because the default `MODEL_REPO_CHECKOUT` points one directory up from this repo:

```text
~/Documents/GitHub/
  mvp-phase-1/          this application repo
  mvp-phase1-model/     separate generated-model repo
```

Clone the application repo:

```bash
cd ~/Documents/GitHub
git clone git@github.com:mo-sameh1/mvp-phase-1.git
cd mvp-phase-1
```

Clone or create the model repo:

```bash
cd ~/Documents/GitHub
git clone git@github.com:mo-sameh1/mvp-phase1-model.git
cd mvp-phase-1
```

If the model repo is brand new, initialize this layout in `mvp-phase1-model` and push it:

```bash
cd ~/Documents/GitHub/mvp-phase1-model
mkdir -p systems/demo-legacy-system/as-is/{motivation,strategy,business,application,technology}
touch systems/demo-legacy-system/as-is/{motivation,strategy,business,application,technology}/.gitkeep
git add systems
git commit -m "chore: initialize clean model repository"
git branch -M main
git push -u origin main
```

## Environment Setup

Copy the examples:

```bash
cd ~/Documents/GitHub/mvp-phase-1
cp .env.example .env
cp frontend/.env.example frontend/.env
```

### Required Backend Values

Use `.env` at the repo root.

| Variable | Example | Where to get it |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://mvp_app:mvp_app_password@localhost:5433/mvp_phase1` | Keep the example for local Docker Postgres. |
| `TEST_DATABASE_URL` | `postgresql+psycopg://mvp_app:mvp_app_password@localhost:5433/mvp_phase1_test` | Keep the example for tests. |
| `MODEL_REPO_SYSTEM_ID` | `demo-legacy-system` | Keep this for the MVP unless the demo system id changes. |
| `EVIDENCE_ROOT` | `test-fixtures/epic-j/approved/evidence` | Set to the fixture or a local evidence folder. Real client evidence stays out of git. |
| `MODEL_REPO_CHECKOUT` | `../mvp-phase1-model` | Local path to the model repo checkout. |
| `GITHUB_MODEL_REPO` | `mo-sameh1/mvp-phase1-model` | GitHub owner/repo for the model repo. |
| `GITHUB_TOKEN` | `github_pat_...` | Fine-grained GitHub PAT scoped only to the model repo. |
| `GITHUB_WEBHOOK_SECRET` | random hex string | Generate locally with `openssl rand -hex 32`. |
| `BACKEND_API_KEY` | random app secret | Generate locally with `openssl rand -hex 32`. |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,https://front-production-9849.up.railway.app` | Comma-separated browser origins allowed to call the backend directly. Required when frontend and backend are deployed on different domains. |
| `LANGCHAIN_API_KEY` | `lsv2_...` | LangSmith account settings. |
| `LANGCHAIN_PROJECT` | `7bots-mvp-phase1-dev` | LangSmith project name. |
| `LLM_PROVIDER` | `ollama`, `groq`, or `anthropic` | Pick one provider. |

### GitHub Token Setup

Create a fine-grained GitHub personal access token:

1. Open GitHub settings.
2. Go to Developer settings -> Personal access tokens -> Fine-grained tokens.
3. Create a token scoped only to `mo-sameh1/mvp-phase1-model`.
4. Grant repository permissions:
   - Contents: Read and write.
   - Pull requests: Read and write.
   - Metadata: Read-only, automatically included.
5. Put it in `.env` as `GITHUB_TOKEN`.

Do not reuse this token as the frontend or backend API key.

In deployment secret stores, set the variable name to `GITHUB_TOKEN` and the value to the token
itself, for example `github_pat_...`. Do not paste the full assignment
`GITHUB_TOKEN=github_pat_...` as the value. The backend normalizes common wrappers such as accidental
quotes or `Bearer ` prefixes, but the token must still be active, unexpired, and scoped to the model
repo.

### GitHub Webhook Secret

Generate a secret:

```bash
openssl rand -hex 32
```

Put the value in `.env`:

```bash
GITHUB_WEBHOOK_SECRET=<generated-value>
```

This secret is used only by GitHub webhooks. GitHub signs each webhook request with this secret, and the backend verifies the signature before changing artifact approval state.

### Backend API Key

Generate a separate app key:

```bash
openssl rand -hex 32
```

Put it in `.env`:

```bash
BACKEND_API_KEY=<generated-value>
```

Set the same value in `frontend/.env`:

```bash
VITE_API_KEY=<same-value-as-BACKEND_API_KEY>
```

This is MVP-level API protection. It is browser-visible and not production auth, but it gives the MVP a consistent authenticated API contract.

### Split-Domain Deployment

Local frontend development uses the Vite proxy: browser calls go to `/api/*` on
`http://127.0.0.1:5173`, and Vite forwards them to the backend. A deployed static frontend does not
have that dev proxy, so it must call the backend service directly.

For the current Railway deployment, configure the backend service with:

```bash
BACKEND_API_KEY=<generated-value>
CORS_ALLOWED_ORIGINS=https://front-production-9849.up.railway.app
```

Configure the frontend service with:

```bash
VITE_API_BASE_PATH=https://mvp-phase-1-production.up.railway.app
VITE_API_KEY=<same-value-as-BACKEND_API_KEY>
```

`VITE_API_BASE_PATH` may be `/api` for local dev, a full `https://...` URL for deployment, or a bare
hostname such as `mvp-phase-1-production.up.railway.app`, which the frontend normalizes to HTTPS.
Because Vite environment variables are compiled into the frontend bundle, redeploy the frontend
after changing any `VITE_*` value.

If deployed frontend requests fail before a job is created, check these first:

- Browser requests should target the backend host, not a path on the frontend host.
- Backend preflight requests should return CORS headers for the frontend origin.
- `VITE_API_KEY` and `BACKEND_API_KEY` must match exactly.

Missing LLM or LangSmith credentials are a separate live-run issue. They can make an ingestion job
fail after it starts, but they should not prevent the frontend from reaching the backend.

### LangSmith Setup

Create or use a LangSmith account, then:

1. Open LangSmith.
2. Create or choose a project, for example `7bots-mvp-phase1-dev`.
3. Create an API key from account settings.
4. Set:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<langsmith-key>
LANGCHAIN_PROJECT=7bots-mvp-phase1-dev
```

Every live agent run should appear as a connected trace using the Phase 1 run id.

### Model Provider Setup

Pick exactly one provider in `.env`.

#### Option A: Ollama Cloud

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_API_KEY=<ollama-cloud-api-key>
OLLAMA_MODEL=llama3.1:8b-cloud
```

For stronger runs, you can choose a stronger Ollama Cloud model if your quota allows it. Restart the backend after changing any provider variable.

#### Option B: Local Ollama

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_API_KEY=
OLLAMA_MODEL=llama3.1
```

Start Ollama and pull the model:

```bash
ollama serve
ollama pull llama3.1
```

#### Option C: Groq

```bash
LLM_PROVIDER=groq
GROQ_API_KEY=<groq-api-key>
GROQ_MODEL=llama-3.3-70b-versatile
```

Get the key from the Groq console.

#### Option D: Anthropic

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=<anthropic-api-key>
ANTHROPIC_MODEL=claude-3-5-haiku-latest
```

Get the key from the Anthropic console.

## Install And Verify From A Clean Checkout

Run from the application repo root:

```bash
cd ~/Documents/GitHub/mvp-phase-1
uv sync
npm install --prefix frontend
make db-up
make db-migrate
make lint
make test
make frontend-build
make frontend-test
```

Expected result:

- `make lint` passes Ruff and Black checks.
- `make test` passes the backend and agent suite.
- `make frontend-build` passes TypeScript and Vite build.
- `make frontend-test` passes frontend component and API-client tests.

## Running The App Locally

Open three terminals.

### Terminal 1: Backend

```bash
cd ~/Documents/GitHub/mvp-phase-1
uv run uvicorn backend.api.app:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Check health:

```bash
curl http://127.0.0.1:8000/
```

Expected:

```json
{"health":"OK"}
```

API docs:

```text
http://127.0.0.1:8000/docs
```

Important: backend settings are cached when the process starts. If you change `.env`, fully stop and restart uvicorn. Do not expect a running process to reread `EVIDENCE_ROOT`, `OLLAMA_MODEL`, keys, or provider settings.

### Terminal 2: Frontend

```bash
cd ~/Documents/GitHub/mvp-phase-1
make frontend-dev
```

Open:

```text
http://127.0.0.1:5173
```

The frontend calls `/api/*`; Vite proxies those requests to `VITE_DEV_API_PROXY_TARGET`, defaulting to `http://127.0.0.1:8000`.

For deployed static frontend builds, set `VITE_API_BASE_PATH` to the full backend URL instead of
`/api`, and configure the backend `CORS_ALLOWED_ORIGINS` to include the deployed frontend origin.

### Terminal 3: Webhook Tunnel

For the final GitHub webhook demo, expose the backend:

```bash
cloudflared tunnel --url http://localhost:8000
```

Use the generated HTTPS URL as the GitHub webhook payload URL.

## GitHub Webhook Configuration

Open the model repo settings in GitHub:

```text
https://github.com/mo-sameh1/mvp-phase1-model/settings/hooks
```

Create or update a webhook:

| Setting | Value |
| --- | --- |
| Payload URL | `https://<cloudflared-domain>/webhooks/github` |
| Content type | `application/json` |
| Secret | Same value as `GITHUB_WEBHOOK_SECRET` |
| SSL verification | Enable SSL verification |
| Events | Select individual events, then choose Pull requests |
| Active | Checked |

Expected behavior:

| GitHub action | Backend result |
| --- | --- |
| PR opened by the pipeline | Artifact version is `pending`. |
| PR closed without merge | Artifact version becomes `rejected`. |
| Rejected PR reopened | Artifact version becomes `pending`. |
| PR merged | Artifact version becomes `approved`, and `model_element_index` is refreshed. |

The Model page lists elements only after a PR is merged and the webhook has refreshed the index. A pending PR is intentionally not shown as approved model content.

## API Contract

Frontend-facing endpoints require:

```text
X-API-Key: <BACKEND_API_KEY>
```

Endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/systems/{system_id}/ingest` | Queue an As-Is ingestion run. |
| `GET` | `/jobs/{job_id}` | Read queued/running/succeeded/failed status. |
| `GET` | `/systems/{system_id}/elements?layer=application` | List indexed model elements, optionally filtered by layer. |
| `GET` | `/elements/{element_id}` | Read full git-backed element JSON plus model JSON URL. |
| `GET` | `/systems/{system_id}/artifact-versions` | List PR/artifact approval records. |

Unkeyed endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Health check. |
| `GET` | `/docs` | FastAPI docs. |
| `POST` | `/webhooks/github` | GitHub signed webhook receiver. |

## Epic J Acceptance Flow

J2 is the MVP finish line. It proves the connected product loop:

```text
frontend trigger -> backend job -> live ingestion agents -> assembly agents
-> validation report -> GitHub PR -> manual merge -> webhook approval
-> model index refresh -> frontend model viewer
```

Run the acceptance flow twice from a clean DB and clean model repo state for the reliability criterion.

### Clean State Before Each Demo

Stop backend, frontend, and tunnel processes.

Reset application DB rows:

```bash
PGPASSWORD=mvp_app_password psql 'postgresql://mvp_app@localhost:5433/mvp_phase1' \
  -v ON_ERROR_STOP=1 \
  -c 'truncate table artifact_versions, evidence_sources, jobs, model_element_index, legacy_systems restart identity cascade;'
```

Reset the model repo:

```bash
cd ~/Documents/GitHub/mvp-phase1-model
git switch main
git fetch origin main
git reset --hard origin/main
git clean -fd systems
```

Clear the frontend's saved last job id in the browser console:

```js
localStorage.removeItem("mvp-phase1:last-job:demo-legacy-system")
```

### Part 1: Invalid Fixture Must Fail Closed

Set `.env`:

```bash
EVIDENCE_ROOT=test-fixtures/epic-j/invalid/evidence
```

Restart the backend after editing `.env`.

In the frontend:

1. Open `http://127.0.0.1:5173/systems/demo-legacy-system/run`.
2. Leave the evidence-path field empty.
3. Click Run.
4. Wait for the job to reach `failed`.
5. Confirm the UI shows the backend error message.
6. Confirm no GitHub PR was opened for that failed run.

Why this matters:

- The invalid fixture includes a relationship candidate that points to a missing target.
- The ingestion/validation path must reject that rather than inventing a target or opening a PR.
- This proves fail-closed behavior before human review.

Useful DB check:

```bash
PGPASSWORD=mvp_app_password psql 'postgresql://mvp_app@localhost:5433/mvp_phase1' \
  -c "select id, run_id, status, left(coalesce(error_message,''), 500) as error_message from jobs order by started_at desc nulls last;"
```

Expected:

- One failed job.
- Zero artifact versions for the failed run.

### Part 2: Approved Fixture Opens A PR

Clean state again.

Set `.env`:

```bash
EVIDENCE_ROOT=test-fixtures/epic-j/approved/evidence
```

Restart the backend after editing `.env`.

In the frontend:

1. Open the Run screen.
2. Leave the evidence-path field empty.
3. Click Run.
4. Watch status move through `queued`, `running`, and `succeeded`.
5. Open the Versions screen.
6. Confirm there is a `pending` artifact version with a GitHub PR URL.
7. Open the PR.

In GitHub:

1. Read the PR body.
2. Confirm it includes run id, commit SHA, validation status, element counts, relationship count, and reconciliation notes.
3. Merge the PR.

Expected after merge:

- GitHub sends a `pull_request.closed` webhook with `merged=true`.
- Backend verifies the signature using `GITHUB_WEBHOOK_SECRET`.
- `artifact_versions.approval_status` becomes `approved`.
- `model_element_index` refreshes from the merged model repo `main` branch.
- The frontend Versions page shows `approved`.
- The frontend Model page lists indexed ArchiMate elements grouped by layer.
- Element detail pages show documentation, evidence citations, relationships, commit SHA, git path, and model JSON link.

Useful DB checks:

```bash
PGPASSWORD=mvp_app_password psql 'postgresql://mvp_app@localhost:5433/mvp_phase1' \
  -c "select run_id, approval_status, pr_number, pr_url, approved_by, approved_at from artifact_versions order by created_at desc;"
```

```bash
PGPASSWORD=mvp_app_password psql 'postgresql://mvp_app@localhost:5433/mvp_phase1' \
  -c "select layer, count(*) from model_element_index group by layer order by layer;"
```

Expected:

- Latest artifact version is `approved`.
- `model_element_index` has rows across the ArchiMate layers represented by the accepted run.

## Frontend Demo Flow

Use these screens during recording:

| Screen | URL | What to show |
| --- | --- | --- |
| Run | `/systems/demo-legacy-system/run` | Trigger run, job id, status polling, failure message or success. |
| Versions | `/systems/demo-legacy-system/versions` | Pending, rejected, or approved artifact versions and PR links. |
| Model | `/systems/demo-legacy-system/elements` | Elements grouped by ArchiMate layer after approval. |
| Detail | `/systems/demo-legacy-system/elements/<element-id>` | Evidence citations, relationships, commit SHA, git path, model JSON link. |

Clickable external links are intentionally limited to GitHub PR URLs and backend-provided model JSON URLs. Evidence locators are displayed as traceability text until a later source-controlled evidence URL convention exists.

## Smoke Commands

Run deterministic and local checks any time:

```bash
make lint
make test
make frontend-build
make frontend-test
make archimate-smoke
make epic-e-smoke
make epic-e-smoke EPIC_E_REPEAT=2
```

Run live checks only when provider, LangSmith, GitHub, DB, and model repo settings are ready:

```bash
make langsmith-smoke
make deepagent-smoke
make deepagent-subagent-smoke
make epic-d-smoke
make epic-f-smoke
make epic-g-smoke
make epic-h-smoke
```

Side effect warning:

- `make epic-g-smoke` may create a real GitHub PR.
- `make epic-h-smoke` may run live agents and create a real GitHub PR.
- The frontend Run button uses the same live backend pipeline.

## Provider And Environment Troubleshooting

### `.env` Changed But The Run Used Old Values

Cause: FastAPI settings are cached in the running Python process.

Fix:

```bash
# Stop uvicorn fully with Ctrl+C, then restart:
uv run uvicorn backend.api.app:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Use this after changing:

- `EVIDENCE_ROOT`
- `LLM_PROVIDER`
- `OLLAMA_MODEL`
- `OLLAMA_BASE_URL`
- `GROQ_MODEL`
- `ANTHROPIC_MODEL`
- any API key or secret

### Model Page Is Empty

This is expected before approval. The Model page reads `model_element_index`, and the index refreshes only after a PR is merged and the GitHub webhook succeeds.

Check artifact status:

```bash
PGPASSWORD=mvp_app_password psql 'postgresql://mvp_app@localhost:5433/mvp_phase1' \
  -c "select run_id, approval_status, pr_url from artifact_versions order by created_at desc;"
```

### Artifact Stayed Pending After Closing A PR

If you close without merging, the webhook should mark it `rejected`. If it stays `pending`, GitHub probably did not reach the local backend.

Check:

1. Cloudflare Tunnel is running.
2. GitHub webhook Payload URL points to the current tunnel URL.
3. Webhook secret matches `GITHUB_WEBHOOK_SECRET`.
4. Event type includes Pull requests.
5. Backend process was restarted after changing `.env`.

### Approved Fixture Fails During Ingestion

Check LangSmith first. Common causes:

- Running backend still has stale `.env` values.
- Provider model is too weak or is not following tool-call schemas.
- Provider quota or cloud API failed.
- The model repo was not reset and contains stale partial output.

The ingestion tools normalize common formatting issues, but they still reject invalid model facts, unsupported relationships, missing evidence, and unsafe paths.

### No PR Was Created

Check the latest job:

```bash
PGPASSWORD=mvp_app_password psql 'postgresql://mvp_app@localhost:5433/mvp_phase1' \
  -c "select id, run_id, status, left(coalesce(error_message,''), 500) as error_message from jobs order by started_at desc nulls last;"
```

If validation failed, the pipeline intentionally halts before Epic G.

### GitHub Push Fails

Check:

- `GITHUB_TOKEN` is a fine-grained token.
- Deployment secret value is the token itself, not `GITHUB_TOKEN=<token>`.
- Token has no leading/trailing spaces or accidental quotes in the deployment UI.
- Token is active and has not expired or been revoked.
- Token is scoped to `mo-sameh1/mvp-phase1-model`.
- Contents permission is Read and write.
- Pull requests permission is Read and write.
- `MODEL_REPO_CHECKOUT` points to a real local checkout.
- Local model repo is on `main` and can fetch from `origin`.

The container startup script authenticates Git with an ephemeral `Authorization` header and keeps
the model repo `origin` URL as `https://github.com/<owner>/<repo>.git`. This avoids stale tokenized
remotes when deployment secrets are rotated.

## Manual Cleanup Commands

Stop local app processes:

```bash
pkill -f "uvicorn backend.api.app:create_app" || true
pkill -f "vite --host" || true
pkill -f "cloudflared tunnel" || true
```

Clear application DB demo rows:

```bash
PGPASSWORD=mvp_app_password psql 'postgresql://mvp_app@localhost:5433/mvp_phase1' \
  -v ON_ERROR_STOP=1 \
  -c 'truncate table artifact_versions, evidence_sources, jobs, model_element_index, legacy_systems restart identity cascade;'
```

Reset model repo to clean `main`:

```bash
cd ~/Documents/GitHub/mvp-phase1-model
git switch main
git fetch origin main
git reset --hard origin/main
git clean -fd systems
```

Delete a remote feature branch if a demo branch should be removed:

```bash
git push origin --delete feature/ingest-demo-legacy-system-<run-id>
```

## Development Workflow

Install:

```bash
uv sync
npm install --prefix frontend
```

Format:

```bash
make format
```

Verify:

```bash
make lint
make test
make frontend-build
make frontend-test
```

Database migrations:

```bash
make db-up
make db-migrate
make db-downgrade
make db-migrate
```

Commit style:

```text
feat: add new capability
fix: correct behavior or harden runtime
docs: update documentation
test: add or improve tests
refactor: improve structure without behavior change
chore: tooling or maintenance
```

## Security Notes

- Never commit `.env`.
- Never commit real client evidence.
- Never print GitHub, LangSmith, Groq, Anthropic, or Ollama keys in logs.
- Keep `BACKEND_API_KEY`, `GITHUB_TOKEN`, and `GITHUB_WEBHOOK_SECRET` separate.
- Use the minimum-scoped GitHub PAT possible.
- The MVP frontend API key is browser-visible and is not production-grade authentication.
- GitHub webhook approval changes must always verify the HMAC signature.

## Source Of Truth For Future Agents

Future development agents should read:

```text
AGENTS.md
.AGENTS/project-brief.md
.AGENTS/architecture-contracts.md
.AGENTS/development-workflow.md
.AGENTS/epic-tracker.md
agents/skills/archimate-metamodel/SKILL.md
```

The key rule is simple: agents may extract candidates, but deterministic schema validation, ArchiMate metamodel validation, git history, PR review, and evidence citations decide what becomes accepted model content.
