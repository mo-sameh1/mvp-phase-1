UV ?= uv
POSTGRES_HOST_PORT ?= 5433
POSTGRES_APP_USER ?= mvp_app
POSTGRES_APP_PASSWORD ?= mvp_app_password
POSTGRES_APP_DB ?= mvp_phase1
EPIC_E_REPEAT ?= 1
EPIC_F_ARGS ?=
EPIC_G_ARGS ?=
EPIC_H_ARGS ?=

ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: sync lint format test frontend-install frontend-dev frontend-build frontend-test db-up db-down db-migrate db-downgrade langsmith-smoke archimate-smoke deepagent-smoke deepagent-subagent-smoke epic-d-smoke epic-e-smoke epic-f-smoke epic-g-smoke epic-h-smoke

sync:
	$(UV) sync

lint:
	$(UV) run ruff check .
	$(UV) run black --check .

format:
	$(UV) run ruff check --fix .
	$(UV) run black .

test:
	$(UV) run pytest

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-test:
	cd frontend && npm run test:run

db-up:
	docker compose up -d postgres
	@until PGPASSWORD="$(POSTGRES_APP_PASSWORD)" psql "postgresql://$(POSTGRES_APP_USER)@localhost:$(POSTGRES_HOST_PORT)/$(POSTGRES_APP_DB)" -c "select 1" >/dev/null 2>&1; do \
		echo "Waiting for Postgres on localhost:$(POSTGRES_HOST_PORT)..."; \
		sleep 1; \
	done

db-down:
	docker compose down

db-migrate:
	$(UV) run alembic upgrade head

db-downgrade:
	$(UV) run alembic downgrade -1

langsmith-smoke:
	$(UV) run python scripts/langsmith_smoke.py

archimate-smoke:
	$(UV) run python scripts/archimate_metamodel_smoke.py

deepagent-smoke:
	$(UV) run python scripts/deepagent_smoke.py

deepagent-subagent-smoke:
	$(UV) run python scripts/deepagent_subagent_smoke.py

epic-d-smoke: deepagent-smoke deepagent-subagent-smoke

epic-e-smoke:
	$(UV) run python scripts/epic_e_smoke.py --repeat $(EPIC_E_REPEAT)

epic-f-smoke:
	$(UV) run python scripts/epic_f_smoke.py $(EPIC_F_ARGS)

epic-g-smoke:
	$(UV) run python scripts/epic_g_smoke.py $(EPIC_G_ARGS)

epic-h-smoke:
	$(UV) run python scripts/epic_h_smoke.py $(EPIC_H_ARGS)
