#!/usr/bin/env bash
set -euo pipefail

: "${MODEL_REPO_CHECKOUT:?MODEL_REPO_CHECKOUT env var is required}"
: "${GITHUB_MODEL_REPO:?GITHUB_MODEL_REPO env var is required}"
: "${GITHUB_TOKEN:?GITHUB_TOKEN env var is required}"

MODEL_REPO_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_MODEL_REPO}.git"

export GIT_AUTHOR_NAME="${GIT_AUTHOR_NAME:-7bots MVP Bot}"
export GIT_AUTHOR_EMAIL="${GIT_AUTHOR_EMAIL:-bot@7bots.ai}"
export GIT_COMMITTER_NAME="${GIT_COMMITTER_NAME:-7bots MVP Bot}"
export GIT_COMMITTER_EMAIL="${GIT_COMMITTER_EMAIL:-bot@7bots.ai}"

if [ -d "${MODEL_REPO_CHECKOUT}/.git" ]; then
  echo "Model repo exists, pulling latest..."
  git -C "${MODEL_REPO_CHECKOUT}" fetch origin main
  git -C "${MODEL_REPO_CHECKOUT}" reset --hard origin/main
else
  echo "Cloning model repo..."
  git clone --branch main "${MODEL_REPO_URL}" "${MODEL_REPO_CHECKOUT}"
fi

echo "Running database migrations..."
uv run alembic upgrade head

echo "Starting backend..."
exec uv run uvicorn backend.api.app:create_app --factory --host 0.0.0.0 --port "${PORT:-8000}"
