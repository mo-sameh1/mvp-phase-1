from __future__ import annotations

import base64
import fcntl
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO


class GitCommandError(RuntimeError):
    def __init__(self, command: list[str], stderr: str) -> None:
        redacted = ["<redacted>" if "Authorization:" in part else part for part in command]
        super().__init__(f"git command failed: {' '.join(redacted)}: {stderr.strip()}")


class ModelRepoTransactionError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitRunner:
    repo: Path
    github_repo: str
    token: str

    @property
    def https_remote_url(self) -> str:
        return f"https://github.com/{self.github_repo}.git"

    def run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        command = ["git", *args]
        result = subprocess.run(
            command,
            cwd=self.repo,
            env=self._env(),
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            raise GitCommandError(command, result.stderr)
        return result

    def auth_remote(self) -> str:
        return self.https_remote_url

    def _env(self) -> dict[str, str]:
        env = os.environ.copy()
        if self.token:
            basic_credentials = base64.b64encode(f"x-access-token:{self.token}".encode()).decode(
                "ascii"
            )
            env["GIT_CONFIG_COUNT"] = "1"
            env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
            env["GIT_CONFIG_VALUE_0"] = f"AUTHORIZATION: basic {basic_credentials}"
        return env


def current_commit(runner: GitRunner, ref: str = "HEAD") -> str:
    return runner.run("rev-parse", ref).stdout.strip()


def branch_exists_locally(runner: GitRunner, branch: str) -> bool:
    result = runner.run("show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False)
    return result.returncode == 0


def remote_branch_commit(runner: GitRunner, branch: str) -> str | None:
    result = runner.run(
        "ls-remote",
        "--heads",
        runner.auth_remote(),
        branch,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return result.stdout.split()[0]


def checkout_branch(runner: GitRunner, branch: str, *, start_point: str | None = None) -> None:
    if branch_exists_locally(runner, branch):
        runner.run("checkout", branch)
        return
    if start_point is None:
        runner.run("checkout", "-b", branch)
    else:
        runner.run("checkout", "-b", branch, start_point)


def fetch_branch(runner: GitRunner, branch: str) -> None:
    runner.run("fetch", runner.auth_remote(), branch)


def checkout_base_branch(runner: GitRunner, base_branch: str) -> None:
    fetch_branch(runner, base_branch)
    checkout_branch(runner, base_branch)
    runner.run("pull", "--ff-only", runner.auth_remote(), base_branch)


def current_branch(runner: GitRunner) -> str:
    return runner.run("branch", "--show-current").stdout.strip()


def repository_has_changes(runner: GitRunner) -> bool:
    return bool(runner.run("status", "--porcelain").stdout.strip())


def discard_repository_changes(runner: GitRunner) -> None:
    runner.run("reset", "--hard")
    runner.run("clean", "-fd")


def delete_local_branch(runner: GitRunner, branch: str) -> None:
    if branch_exists_locally(runner, branch):
        runner.run("branch", "-D", branch)


def delete_remote_branch(runner: GitRunner, branch: str) -> None:
    runner.run("push", runner.auth_remote(), "--delete", branch)


def staged_or_worktree_changes(runner: GitRunner, pathspec: str) -> bool:
    result = runner.run("status", "--porcelain", "--", pathspec)
    return bool(result.stdout.strip())


def commit_all_for_path(runner: GitRunner, pathspec: str, message: str) -> str:
    runner.run("add", "--", pathspec)
    runner.run("commit", "-m", message)
    return current_commit(runner)


def push_branch(runner: GitRunner, branch: str) -> None:
    runner.run("push", "-u", runner.auth_remote(), branch)


def show_file_at_ref(runner: GitRunner, ref: str, path: str) -> str:
    return runner.run("show", f"{ref}:{path}").stdout


@dataclass
class ModelRepoTransaction:
    runner: GitRunner
    base_branch: str = "main"
    _base_commit: str | None = field(default=None, init=False)
    _local_branches: set[str] = field(default_factory=set, init=False)
    _pushed_branches: set[str] = field(default_factory=set, init=False)
    _lock_handle: IO[str] | None = field(default=None, init=False)
    _active: bool = field(default=False, init=False)

    @property
    def base_commit(self) -> str:
        if self._base_commit is None:
            raise ModelRepoTransactionError("Model repository transaction has not started.")
        return self._base_commit

    def __enter__(self) -> ModelRepoTransaction:
        self._acquire_lock()
        try:
            # The model checkout is machine-owned. Clear abandoned output from an interrupted run.
            discard_repository_changes(self.runner)
            checkout_base_branch(self.runner, self.base_branch)
            discard_repository_changes(self.runner)
            if repository_has_changes(self.runner):
                raise ModelRepoTransactionError(
                    "Model repository could not be prepared with a clean working tree."
                )
            self._base_commit = current_commit(self.runner)
            self._active = True
            return self
        except Exception as exc:
            cleanup_errors = self._restore_local_checkout()
            self._release_lock()
            if cleanup_errors:
                raise ModelRepoTransactionError(
                    "Model repository setup failed and cleanup was incomplete: "
                    + "; ".join(cleanup_errors)
                ) from exc
            raise

    def __exit__(self, exc_type, exc, traceback) -> bool:
        cleanup_errors: list[str] = []
        if exc_type is not None:
            for branch in sorted(self._pushed_branches):
                try:
                    delete_remote_branch(self.runner, branch)
                except Exception as cleanup_exc:
                    cleanup_errors.append(f"could not delete remote branch {branch}: {cleanup_exc}")
        cleanup_errors.extend(self._restore_local_checkout())
        self._active = False
        self._release_lock()
        if cleanup_errors:
            raise ModelRepoTransactionError(
                "Model repository transaction cleanup failed: " + "; ".join(cleanup_errors)
            ) from exc
        return False

    def register_local_branch(self, branch: str) -> None:
        self._require_active()
        self._local_branches.add(branch)

    def register_pushed_branch(self, branch: str) -> None:
        self._require_active()
        self._pushed_branches.add(branch)

    def _acquire_lock(self) -> None:
        git_dir_value = self.runner.run("rev-parse", "--absolute-git-dir").stdout.strip()
        lock_path = Path(git_dir_value) / "7bots-model-transaction.lock"
        self._lock_handle = lock_path.open("a+", encoding="utf-8")
        fcntl.flock(self._lock_handle.fileno(), fcntl.LOCK_EX)

    def _release_lock(self) -> None:
        if self._lock_handle is None:
            return
        fcntl.flock(self._lock_handle.fileno(), fcntl.LOCK_UN)
        self._lock_handle.close()
        self._lock_handle = None

    def _restore_local_checkout(self) -> list[str]:
        errors: list[str] = []
        try:
            discard_repository_changes(self.runner)
        except Exception as exc:
            errors.append(f"could not discard generated changes: {exc}")

        if self._base_commit is not None:
            try:
                checkout_branch(self.runner, self.base_branch)
                self.runner.run("reset", "--hard", self._base_commit)
                self.runner.run("clean", "-fd")
            except Exception as exc:
                errors.append(f"could not restore {self.base_branch}: {exc}")

        for branch in sorted(self._local_branches):
            try:
                if current_branch(self.runner) != branch:
                    delete_local_branch(self.runner, branch)
            except Exception as exc:
                errors.append(f"could not delete local branch {branch}: {exc}")

        try:
            if repository_has_changes(self.runner):
                errors.append("working tree or index is not clean after cleanup")
        except Exception as exc:
            errors.append(f"could not verify repository status: {exc}")
        return errors

    def _require_active(self) -> None:
        if not self._active:
            raise ModelRepoTransactionError("Model repository transaction is not active.")
