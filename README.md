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
GITHUB_MODEL_REPO=owner/model-repo
GITHUB_TOKEN=github_pat_...
```

## LangSmith Smoke Test

Fill these values in `.env`:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=7bots-mvp-phase1-dev
ANTHROPIC_API_KEY=...
```

Then run:

```bash
make langsmith-smoke
```

The script should create one visible trace in the configured LangSmith project.

## Common Commands

```bash
make sync          # install dependencies
make lint          # ruff + black check
make test          # pytest
make db-up         # start local Postgres
make db-down       # stop local Postgres
make db-migrate    # alembic upgrade head
make db-downgrade  # alembic downgrade -1
```
