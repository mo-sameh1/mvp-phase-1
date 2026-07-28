# Development Workflow

## Working Directory

Use:

```bash
cd /home/mo-sameh1/Documents/GitHub/mvp-phase-1
```

The user asked to keep work on `master` for now.

## Setup

```bash
cp .env.example .env
uv sync
make db-up
make db-migrate
```

The local Postgres container publishes on host port `5433` by default because `5432` was already occupied on the user's machine during initial validation.

## Quality Gates

Run the relevant checks before committing:

```bash
make lint
make test
```

For database changes, also run:

```bash
make db-up
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
```

Stop Postgres when finished:

```bash
make db-down
```

## Commit Style

Use conventional commits:

- `feat:` for new project capability.
- `fix:` for bug fixes.
- `docs:` for documentation-only changes.
- `test:` for tests.
- `refactor:` for behavior-preserving code reshapes.
- `chore:` for tooling, dependency, or maintenance updates.

Prefer small, traceable commits. Mention verification in the final handoff.

## Code Style

- Python code is formatted with Black and linted with Ruff.
- Keep DB access behind `backend/repository/` functions.
- Keep settings in `backend/config/settings.py`.
- Use SQLAlchemy ORM models in `backend/database/models.py`.
- Use Alembic migrations for schema evolution.
- Keep comments sparse and useful.

## Secrets And Sensitive Data

Never read, print, or commit real `.env` files, API keys, GitHub tokens, LangSmith keys, or client evidence.

Allowed:

- Create or update `.env.example` placeholders.
- Document required environment variables.
- Run checks that do not expose secret values.

Not allowed:

- Copy secret-bearing `.env` files into the repo.
- Log token values.
- Commit generated evidence or client data unless explicitly instructed and sanitized.

## Backend API

Epic H frontend-facing endpoints require `X-API-Key` matching `BACKEND_API_KEY`. Keep this key
separate from GitHub and LangSmith credentials. Health, OpenAPI docs, and GitHub webhooks use their
own access patterns.
