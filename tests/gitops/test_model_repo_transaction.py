from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from backend.config.settings import Settings
from backend.gitops import operations
from backend.gitops.local_git import GitCommandError, GitRunner
from backend.gitops.operations import commit_to_model, model_repo_transaction


def test_transaction_removes_staged_and_untracked_output_after_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    remote, checkout = _create_model_repo(tmp_path)
    settings = _settings(checkout)
    monkeypatch.setattr(GitRunner, "auth_remote", lambda self: str(remote))

    with pytest.raises(RuntimeError, match="agent failed"):
        with model_repo_transaction(settings) as transaction:
            generated = checkout / "systems" / "demo" / "as-is" / "business" / "process.json"
            generated.parent.mkdir(parents=True)
            generated.write_text("{}\n", encoding="utf-8")
            transaction.runner.run("add", "--", "systems/demo")
            raise RuntimeError("agent failed")

    _assert_clean_main(checkout)
    assert not (checkout / "systems").exists()


def test_transaction_removes_local_commit_and_branch_after_push_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    remote, checkout = _create_model_repo(tmp_path)
    settings = _settings(checkout)
    branch = "feature/ingest-demo-run-1"
    monkeypatch.setattr(GitRunner, "auth_remote", lambda self: str(remote))

    def fail_push(runner, branch_name):
        raise GitCommandError(["git", "push", branch_name], "simulated push failure")

    monkeypatch.setattr(operations, "push_branch", fail_push)

    with pytest.raises(GitCommandError, match="simulated push failure"):
        with model_repo_transaction(settings) as transaction:
            generated = checkout / "systems" / "demo" / "as-is" / "business" / "process.json"
            generated.parent.mkdir(parents=True)
            generated.write_text("{}\n", encoding="utf-8")
            commit_to_model(settings, "demo", "run-1", transaction=transaction)

    _assert_clean_main(checkout)
    assert _git(checkout, "branch", "--list", branch).stdout.strip() == ""
    assert _git(remote, "for-each-ref", "--format=%(refname)", f"refs/heads/{branch}").stdout == ""


def _create_model_repo(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    seed = tmp_path / "seed"
    checkout = tmp_path / "checkout"
    _git(tmp_path, "init", "--bare", "--initial-branch=main", str(remote))
    seed.mkdir()
    _git(seed, "init", "--initial-branch=main")
    _git(seed, "config", "user.name", "Test Bot")
    _git(seed, "config", "user.email", "test@example.com")
    _git(seed, "commit", "--allow-empty", "-m", "chore: initialize empty model repo")
    _git(seed, "remote", "add", "origin", str(remote))
    _git(seed, "push", "-u", "origin", "main")
    _git(tmp_path, "clone", str(remote), str(checkout))
    _git(checkout, "config", "user.name", "Test Bot")
    _git(checkout, "config", "user.email", "test@example.com")
    return remote, checkout


def _settings(checkout: Path) -> Settings:
    return Settings(
        model_repo_checkout=str(checkout),
        github_model_repo="example/repo",
        github_token="",
    )


def _assert_clean_main(checkout: Path) -> None:
    assert _git(checkout, "branch", "--show-current").stdout.strip() == "main"
    assert _git(checkout, "status", "--porcelain").stdout == ""
    assert _git(checkout, "diff", "--cached", "--name-only").stdout == ""
    assert _git(checkout, "stash", "list").stdout == ""


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
