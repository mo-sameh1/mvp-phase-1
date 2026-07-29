from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

from agents.schema import ModelElement
from backend.config.settings import Settings
from backend.gitops.local_git import GitRunner, show_file_at_ref


def read_model_element_from_git(
    settings: Settings,
    *,
    commit_sha: str,
    git_path: str,
) -> ModelElement:
    content = read_model_json_from_git(settings, commit_sha=commit_sha, git_path=git_path)
    payload = json.loads(content)
    return ModelElement(**payload)


def read_model_json_from_git(
    settings: Settings,
    *,
    commit_sha: str,
    git_path: str,
) -> str:
    runner = GitRunner(
        Path(settings.model_repo_checkout).expanduser().resolve(),
        settings.github_model_repo,
        settings.github_token,
    )
    return show_file_at_ref(runner, commit_sha, git_path)


def build_model_json_url(
    *,
    github_model_repo: str,
    commit_sha: str,
    git_path: str,
) -> str:
    repo = _normalize_github_repo(github_model_repo)
    encoded_path = "/".join(quote(part, safe="") for part in git_path.split("/"))
    return f"https://github.com/{repo}/blob/{quote(commit_sha, safe='')}/{encoded_path}"


def _normalize_github_repo(value: str) -> str:
    repo = value.strip()
    repo = repo.removeprefix("https://github.com/")
    repo = repo.removeprefix("http://github.com/")
    repo = repo.removesuffix(".git")
    return repo.strip("/")
