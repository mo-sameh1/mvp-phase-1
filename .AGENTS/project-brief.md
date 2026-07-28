# Project Brief

## Company And Product Context

7bots.ai is a Saudi-based agentic AI startup building tooling to help teams modernize legacy systems with agentic AI. This repository is the application codebase for the first MVP slice of that platform.

The MVP proves the Phase 1 As-Is loop:

```text
evidence -> agent-extracted ArchiMate model -> traceable git commit -> human PR review -> viewable model
```

This engineering repo is separate from the GitHub model repository that will store generated ArchiMate artifacts.

## Source Documents

The project was planned from three user-provided PDFs:

- `01 - CluadeCode - Multi-Agent architecture design for legacy systems 01.pdf`
- `02 - CluadeCode - Multi-Agent architecture design for legacy systems 02.pdf`
- `03 - CluadeCode - mvp-phase1-development-tasks.pdf`

The first two documents define the platform architecture. The third turns the architecture into epics and tasks for the MVP.

## Architecture Direction

- ArchiMate is the source of truth.
- UML and C4 are later derived views, not independently extracted source models.
- The platform should be traceable, gap-aware, incrementally validated, and human-approved.
- Agents should extract structured JSON artifacts with evidence citations, not unsupported prose.
- Human-in-the-loop approval happens through GitHub PR review for the MVP.
- The long-term platform must support multi-tenancy, cloud/on-prem deployment, swappable model providers, swappable git/storage/observability providers, and auditability.

## Four-Phase Methodology

- Phase 1: As-Is architecture extraction.
- Phase 2: 133-dimension assessment across 9 perspectives.
- Phase 3: Target architecture and gap analysis.
- Phase 4: Modernization roadmap.

The current repository foundation is only for the single-tenant Phase 1 MVP.

## MVP Technology Choices

- Backend: Python 3.11+ with FastAPI.
- Dependency management: `uv`.
- Database: PostgreSQL with SQLAlchemy ORM and Alembic migrations.
- Agent framework later: `deepagents` / LangGraph / LangChain.
- LLM provider for MVP smoke testing: configurable through LangChain. Supported providers are Ollama, Groq, and Anthropic.
- Observability for MVP: LangSmith.
- Model repo host for MVP: GitHub.
- Job execution: FastAPI `BackgroundTasks` plus the `jobs` table.
- Frontend later: React + Vite + TypeScript.
