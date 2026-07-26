# MVP Phase 1

Engineering repository for the 7bots.ai legacy modernization MVP. This repo is the application codebase. It is separate from the GitHub model repository that will store generated ArchiMate output.

The current implementation covers Epics A and B: local tooling, Postgres, configuration, Alembic migrations, and data access functions.

## Local Setup

1. Install `uv` and Docker.
2. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

3. Install Python dependencies:

   ```bash
   uv sync
   ```

4. Start Postgres:

   ```bash
   make db-up
   ```

   The Docker container listens on host port `5433` by default to avoid clashing with an existing local Postgres on `5432`.

5. Run migrations:

   ```bash
   make db-migrate
   ```

6. Run checks:

   ```bash
   make lint
   make test
   ```

## Manual GitHub Model Repo Setup

Epic A3 requires a separate GitHub repository for generated model artifacts. Create it manually for now, then add this directory layout:

```text
systems/demo-legacy-system/as-is/motivation/.gitkeep
systems/demo-legacy-system/as-is/strategy/.gitkeep
systems/demo-legacy-system/as-is/business/.gitkeep
systems/demo-legacy-system/as-is/application/.gitkeep
systems/demo-legacy-system/as-is/technology/.gitkeep
```

Create a fine-grained GitHub personal access token scoped only to that model repo with contents and pull-request read/write permissions. Put the repo name and token in `.env`:

```bash
MODEL_REPO_SYSTEM_ID=demo-legacy-system
EVIDENCE_ROOT=reference/evidence
MODEL_REPO_CHECKOUT=../mvp-phase1-model
GITHUB_MODEL_REPO=mo-sameh1/mvp-phase1-model
GITHUB_TOKEN=github_pat_...
```

## LangSmith Smoke Test

Fill these values in `.env`:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=7bots-mvp-phase1-dev
```

Then choose one model provider:

```bash
# Local Ollama
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Or hosted Groq
LLM_PROVIDER=groq
GROQ_API_KEY=...
GROQ_MODEL=llama-3.3-70b-versatile

# Or hosted Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-3-5-haiku-latest
```

Then run:

```bash
make langsmith-smoke
```

The script should create one visible trace in the configured LangSmith project. For Ollama, make sure `ollama serve` is running and the selected model has already been pulled.

## Common Commands

```bash
make sync          # install dependencies
make lint          # ruff + black check
make test          # pytest
make db-up         # start local Postgres
make db-down       # stop local Postgres
make db-migrate    # alembic upgrade head
make db-downgrade  # alembic downgrade -1
make archimate-smoke
make epic-d-smoke  # requires real LLM provider env
```

## ArchiMate Metamodel Skill

Epic C adds a source-grounded ArchiMate 3.2 metamodel foundation:

```text
agents/skills/archimate-metamodel/
agents/archimate_metamodel/
```

The structured JSON files are the deterministic validator authority. `SKILL.md` is the agent-readable guide. Relationship validation fails closed unless a rule is marked approved from an official source.

Run the deterministic smoke test with:

```bash
make archimate-smoke
```

## Deep Agent Runtime Scaffold

Epic D adds the shared model-element schema and Deep Agent runtime scaffold:

```text
agents/schema.py
agents/runtime/
```

The runtime keeps provider selection, filesystem routing, base agent construction, and placeholder
subagent registration in separate modules. `LLM_PROVIDER` may be `ollama`, `groq`, or `anthropic`.

The agent-visible filesystem is split into three routes:

```text
/evidence/  read-only local evidence from EVIDENCE_ROOT
/systems/   writable model repo checkout under MODEL_REPO_CHECKOUT/systems
/skills/    read-only project skills from agents/skills
```

Run the Deep Agent smoke checks after real provider and LangSmith env vars are set:

```bash
make deepagent-smoke
make deepagent-subagent-smoke
make epic-d-smoke
```

`deepagent-subagent-smoke` verifies the five Epic E placeholder subagents:

```text
strategy-analyst
business-analyst
code-analyzer
infra-analyzer
integration-mapper
```
