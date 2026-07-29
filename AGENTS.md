# Agent Guide

This repository is the engineering codebase for the 7bots.ai MVP Phase 1 legacy modernization platform. Start here before making changes.

## Read First

1. `.AGENTS/project-brief.md` - product context, source documents, and phase model.
2. `.AGENTS/architecture-contracts.md` - decisions that later epics must preserve.
3. `.AGENTS/development-workflow.md` - local setup, quality gates, secrets, and git rules.
4. `.AGENTS/epic-tracker.md` - what is done, what is pending, and the next likely work.

## Current State

Epics A-I are implemented on `master`.

The current codebase contains the Python/DB foundation, ArchiMate metamodel skill, Deep Agent
runtime scaffold, Epic E ingestion subagent contracts, Epic F assembly subagents, and Epic G GitHub
PR automation. Epic H adds the async Phase 1 backend API and owns live ingestion order in Python
while invoking the real Epic E subagents. Epic I adds the React/Vite model viewer. The full
end-to-end demo fixture is intentionally still a future epic.

## Non-Negotiables

- Keep work on `master` until the user asks for branches.
- Use conventional commit messages such as `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, and `chore:`.
- Never commit `.env`, API keys, GitHub tokens, LangSmith keys, real client evidence, or generated virtualenv/build/cache directories.
- Preserve traceability: every future architecture fact must point to evidence and every artifact version must link to its run/commit/PR state.
- Run the relevant verification commands before committing and mention anything that could not be verified.

## Fast Checks

```bash
uv sync
make lint
make test
make frontend-build
make frontend-test
make archimate-smoke
make epic-e-smoke
make epic-f-smoke
make epic-g-smoke
make epic-h-smoke
make db-up
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
make db-down
```
