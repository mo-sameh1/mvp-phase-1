import json
from pathlib import Path

import pytest

from backend.config.settings import Settings
from backend.gitops import operations
from backend.gitops.local_git import GitCommandError
from backend.gitops.operations import (
    CommitToModelResult,
    branch_name,
    commit_message,
    commit_to_model,
    open_pull_request,
)
from backend.repository import create_legacy_system, list_artifact_versions


def test_branch_name_and_commit_message_are_deterministic() -> None:
    assert branch_name("demo", "run-1") == "feature/ingest-demo-run-1"
    assert commit_message("demo", "run-1") == "feat(as-is): update demo model for run-1"


def test_commit_to_model_returns_existing_branch_idempotently(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(operations, "remote_branch_commit", lambda runner, branch: "abc123")

    result = commit_to_model(_settings(tmp_path), "demo", "run-1")

    assert result.status == "existing_branch"
    assert result.pushed is True
    assert result.commit_sha == "abc123"


def test_commit_to_model_no_changes_returns_noop(monkeypatch, tmp_path: Path) -> None:
    calls = []
    monkeypatch.setattr(operations, "remote_branch_commit", lambda runner, branch: None)
    monkeypatch.setattr(operations, "checkout_base_branch", lambda runner, base: calls.append(base))
    monkeypatch.setattr(operations, "staged_or_worktree_changes", lambda runner, path: False)
    monkeypatch.setattr(operations, "current_commit", lambda runner: "base123")

    result = commit_to_model(_settings(tmp_path), "demo", "run-1")

    assert calls == ["main"]
    assert result.status == "no_changes"
    assert result.pushed is False
    assert result.commit_sha == "base123"


def test_commit_to_model_stages_only_system_path_and_pushes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls = {}
    monkeypatch.setattr(operations, "remote_branch_commit", lambda runner, branch: None)
    monkeypatch.setattr(operations, "checkout_base_branch", lambda runner, base: None)
    monkeypatch.setattr(operations, "staged_or_worktree_changes", lambda runner, path: True)
    monkeypatch.setattr(operations, "checkout_branch", lambda runner, branch, start_point: None)

    def fake_commit(runner, pathspec, message):
        calls["pathspec"] = pathspec
        calls["message"] = message
        return "commit123"

    monkeypatch.setattr(operations, "commit_all_for_path", fake_commit)
    monkeypatch.setattr(
        operations,
        "push_branch",
        lambda runner, branch: calls.setdefault("branch", branch),
    )

    result = commit_to_model(_settings(tmp_path), "demo", "run-1")

    assert calls["pathspec"] == "systems/demo"
    assert calls["message"] == "feat(as-is): update demo model for run-1"
    assert calls["branch"] == "feature/ingest-demo-run-1"
    assert result.status == "pushed"


def test_git_command_error_redacts_authorization_value() -> None:
    error = GitCommandError(["git", "-c", "Authorization: bearer secret"], "boom")

    assert "secret" not in str(error)
    assert "<redacted>" in str(error)


def test_open_pull_request_creates_pending_artifact(session, monkeypatch, tmp_path: Path) -> None:
    create_legacy_system(session, system_id="demo", name="Demo")
    _write_reports(tmp_path)
    FakeGitHubClient.prs = []
    monkeypatch.setattr(operations, "GitHubClient", FakeGitHubClient)

    result = open_pull_request(
        _settings(tmp_path),
        session,
        _commit_result(),
        tmp_path / "validation-report.json",
        tmp_path / "reconciliation-report.json",
    )
    repeated = open_pull_request(
        _settings(tmp_path),
        session,
        _commit_result(),
        tmp_path / "validation-report.json",
        tmp_path / "reconciliation-report.json",
    )

    artifacts = list_artifact_versions(session, system_id="demo")
    assert result.pr_number == 42
    assert result.status == "created"
    assert repeated.status == "reused"
    assert len(artifacts) == 1
    assert artifacts[0].approval_status == "pending"
    assert artifacts[0].commit_sha == "commit123"
    assert artifacts[0].pr_number == 42


def test_open_pull_request_rejects_unpushed_commit(session, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unpushed"):
        open_pull_request(
            _settings(tmp_path),
            session,
            CommitToModelResult("demo", "run-1", "branch", "sha", "no_changes", False, "noop"),
            tmp_path / "validation-report.json",
            tmp_path / "reconciliation-report.json",
        )


class FakeGitHubClient:
    prs: list[dict] = []

    def __init__(self, repo: str, token: str) -> None:
        self.repo = repo
        self.token = token

    def list_open_pull_requests(self, *, head: str, base: str = "main") -> list[dict]:
        return self.prs

    def create_pull_request(self, *, title: str, head: str, base: str, body: str) -> dict:
        assert "Validation status" in body
        self.prs = [{"number": 42, "html_url": "https://github.com/example/repo/pull/42"}]
        FakeGitHubClient.prs = self.prs
        return self.prs[0]


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        model_repo_checkout=str(tmp_path),
        github_model_repo="example/repo",
        github_token="token",
    )


def _commit_result() -> CommitToModelResult:
    return CommitToModelResult(
        system_id="demo",
        run_id="run-1",
        branch="feature/ingest-demo-run-1",
        commit_sha="commit123",
        status="pushed",
        pushed=True,
        message="pushed",
    )


def _write_reports(tmp_path: Path) -> None:
    (tmp_path / "validation-report.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "total_elements": 2,
                "total_relationships": 1,
                "counts_by_layer": {"business": 2},
                "violations": [],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "reconciliation-report.json").write_text(
        json.dumps({"merge_decisions": [], "ambiguous_conflicts": []}),
        encoding="utf-8",
    )
