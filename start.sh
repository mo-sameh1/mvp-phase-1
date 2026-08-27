#!/usr/bin/env bash
set -euo pipefail

: "${MODEL_REPO_CHECKOUT:?MODEL_REPO_CHECKOUT env var is required}"
: "${GITHUB_MODEL_REPO:?GITHUB_MODEL_REPO env var is required}"
: "${GITHUB_TOKEN:?GITHUB_TOKEN env var is required}"

MODEL_REPO_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_MODEL_REPO}.git"

if [ -d "${MODEL_REPO_CHECKOUT}/.git" ]; then
  echo "Model repo exists, pulling latest..."
  git -C "${MODEL_REPO_CHECKOUT}" fetch origin main
  git -C "${MODEL_REPO_CHECKOUT}" reset --hard origin/main
else
  echo "Cloning model repo..."
  git clone --branch main "${MODEL_REPO_URL}" "${MODEL_REPO_CHECKOUT}"
fi

echo "Starting backend..."
exec uv run uvicorn backend.api.app:create_app --factory --host 0.0.0.0 --port "${PORT:-8000}"
