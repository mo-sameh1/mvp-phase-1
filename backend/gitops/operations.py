from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from backend.config.settings import Settings
from backend.gitops.github_client import GitHubClient
from backend.gitops.local_git import (
    GitRunner,
    ModelRepoTransaction,
    branch_exists_locally,
    checkout_branch,
    commit_all_for_path,
    delete_local_branch,
    push_branch,
    remote_branch_commit,
    repository_has_changes,
    staged_or_worktree_changes,
)
from backend.gitops.pr_description import build_pr_description
from backend.repository.artifacts import create_or_get_artifact_version


@dataclass(frozen=True)
class CommitToModelResult:
    system_id: str
    run_id: str
    branch: str
    commit_sha: str
    status: str
    pushed: bool
    message: str


@dataclass(frozen=True)
class PullRequestResult:
    system_id: str
    run_id: str
    branch: str
    commit_sha: str
    pr_number: int
    pr_url: str
    artifact_version_id: str
    status: str


def branch_name(system_id: str, run_id: str) -> str:
    return f"feature/ingest-{system_id}-{run_id}"


def commit_message(system_id: str, run_id: str) -> str:
    return f"feat(as-is): update {system_id} model for {run_id}"


def commit_to_model(
    settings: Settings,
    system_id: str,
    run_id: str,
    *,
    transaction: ModelRepoTransaction,
    base_branch: str = "main",
) -> CommitToModelResult:
    repo = Path(settings.model_repo_checkout).expanduser().resolve()
    branch = branch_name(system_id, run_id)
    runner = transaction.runner
    if runner.repo != repo or transaction.base_branch != base_branch:
        raise ValueError("Model commit must use the active transaction checkout and base branch.")
    remote_commit = remote_branch_commit(runner, branch)
    if remote_commit is not None:
        return CommitToModelResult(
            system_id=system_id,
            run_id=run_id,
            branch=branch,
            commit_sha=remote_commit,
            status="existing_branch",
            pushed=True,
            message="Remote branch already exists for this run.",
        )

    pathspec = f"systems/{system_id}"
    if not staged_or_worktree_changes(runner, pathspec):
        if repository_has_changes(runner):
            raise RuntimeError(f"Model repository has unexpected changes outside {pathspec}.")
        return CommitToModelResult(
            system_id=system_id,
            run_id=run_id,
            branch=branch,
            commit_sha=transaction.base_commit,
            status="no_changes",
            pushed=False,
            message=f"No changes under {pathspec}.",
        )

    if branch_exists_locally(runner, branch):
        delete_local_branch(runner, branch)
    checkout_branch(runner, branch, start_point=transaction.base_commit)
    transaction.register_local_branch(branch)
    commit_sha = commit_all_for_path(runner, pathspec, commit_message(system_id, run_id))
    if repository_has_changes(runner):
        raise RuntimeError(f"Model commit left unexpected changes outside {pathspec}.")
    push_branch(runner, branch)
    transaction.register_pushed_branch(branch)
    return CommitToModelResult(
        system_id=system_id,
        run_id=run_id,
        branch=branch,
        commit_sha=commit_sha,
        status="pushed",
        pushed=True,
        message="Model changes committed and pushed.",
    )


def model_repo_transaction(
    settings: Settings,
    *,
    base_branch: str = "main",
) -> ModelRepoTransaction:
    repo = Path(settings.model_repo_checkout).expanduser().resolve()
    runner = GitRunner(repo, settings.github_model_repo, settings.github_token)
    return ModelRepoTransaction(runner=runner, base_branch=base_branch)


def open_pull_request(
    settings: Settings,
    session: Session,
    commit_result: CommitToModelResult,
    validation_report_path: Path,
    reconciliation_report_path: Path,
    *,
    base_branch: str = "main",
) -> PullRequestResult:
    if not commit_result.pushed:
        raise ValueError("Cannot open a pull request for an unpushed model commit.")

    client = GitHubClient(settings.github_model_repo, settings.github_token)
    owner = settings.github_model_repo.split("/", 1)[0]
    head = f"{owner}:{commit_result.branch}"
    title = f"As-Is model update for {commit_result.system_id} ({commit_result.run_id})"
    body = build_pr_description(
        system_id=commit_result.system_id,
        run_id=commit_result.run_id,
        commit_sha=commit_result.commit_sha,
        validation_report_path=validation_report_path,
        reconciliation_report_path=reconciliation_report_path,
    )
    existing = client.list_open_pull_requests(head=head, base=base_branch)
    pr = (
        existing[0]
        if existing
        else client.create_pull_request(
            title=title,
            head=commit_result.branch,
            base=base_branch,
            body=body,
        )
    )
    artifact = create_or_get_artifact_version(
        session,
        system_id=commit_result.system_id,
        commit_sha=commit_result.commit_sha,
        phase="as-is",
        author_type="agent",
        run_id=commit_result.run_id,
        approval_status="pending",
        pr_number=int(pr["number"]),
        pr_url=str(pr["html_url"]),
    )
    return PullRequestResult(
        system_id=commit_result.system_id,
        run_id=commit_result.run_id,
        branch=commit_result.branch,
        commit_sha=commit_result.commit_sha,
        pr_number=int(pr["number"]),
        pr_url=str(pr["html_url"]),
        artifact_version_id=artifact.id,
        status="reused" if existing else "created",
    )
