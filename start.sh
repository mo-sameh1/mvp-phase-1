#!/usr/bin/env bash
set -euo pipefail

: "${MODEL_REPO_CHECKOUT:?MODEL_REPO_CHECKOUT env var is required}"
: "${GITHUB_MODEL_REPO:?GITHUB_MODEL_REPO env var is required}"
: "${GITHUB_TOKEN:?GITHUB_TOKEN env var is required}"

strip_secret_wrappers() {
  local value="$1"
  value="${value//$'\r'/}"
  value="${value//$'\n'/}"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  if [[ "${value}" == \"*\" && "${value}" == *\" ]]; then
    value="${value:1:${#value}-2}"
  elif [[ "${value}" == \'*\' && "${value}" == *\' ]]; then
    value="${value:1:${#value}-2}"
  fi
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "${value}"
}

clean_secret() {
  local value
  value="$(strip_secret_wrappers "$1")"
  value="${value#GITHUB_TOKEN=}"
  value="$(strip_secret_wrappers "${value}")"
  value="${value#Bearer }"
  value="${value#bearer }"
  value="${value#token }"
  value="$(strip_secret_wrappers "${value}")"
  printf '%s' "${value}"
}

export GITHUB_TOKEN="$(clean_secret "${GITHUB_TOKEN}")"
if [[ -z "${GITHUB_TOKEN}" ]]; then
  echo "GITHUB_TOKEN is empty after normalization." >&2
  exit 1
fi

MODEL_REPO_URL="https://github.com/${GITHUB_MODEL_REPO}.git"

github_git() {
  GIT_CONFIG_COUNT=1 \
    GIT_CONFIG_KEY_0="http.https://github.com/.extraheader" \
    GIT_CONFIG_VALUE_0="AUTHORIZATION: bearer ${GITHUB_TOKEN}" \
    git "$@"
}

if [ -d "${MODEL_REPO_CHECKOUT}/.git" ]; then
  echo "Model repo exists, pulling latest..."
  github_git -C "${MODEL_REPO_CHECKOUT}" remote set-url origin "${MODEL_REPO_URL}"
  github_git -C "${MODEL_REPO_CHECKOUT}" fetch origin main
  github_git -C "${MODEL_REPO_CHECKOUT}" reset --hard origin/main
else
  echo "Cloning model repo..."
  mkdir -p "$(dirname "${MODEL_REPO_CHECKOUT}")"
  github_git clone --branch main "${MODEL_REPO_URL}" "${MODEL_REPO_CHECKOUT}"
  github_git -C "${MODEL_REPO_CHECKOUT}" remote set-url origin "${MODEL_REPO_URL}"
fi

echo "Running database migrations..."
uv run alembic upgrade head

echo "Starting backend..."
exec uv run uvicorn backend.api.app:create_app --factory --host 0.0.0.0 --port "${PORT:-8000}"
