from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitCommandError(RuntimeError):
    def __init__(self, command: list[str], stderr: str) -> None:
        redacted = ["<redacted>" if "Authorization:" in part else part for part in command]
        super().__init__(f"git command failed: {' '.join(redacted)}: {stderr.strip()}")


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
            env["GIT_CONFIG_COUNT"] = "1"
            env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
            env["GIT_CONFIG_VALUE_0"] = f"AUTHORIZATION: bearer {self.token}"
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


def staged_or_worktree_changes(runner: GitRunner, pathspec: str) -> bool:
    result = runner.run("status", "--porcelain", "--", pathspec)
    return bool(result.stdout.strip())


def commit_all_for_path(runner: GitRunner, pathspec: str, message: str) -> str:
    runner.run("add", "--", pathspec)
    runner.run("commit", "-m", message)
    return current_commit(runner)


def push_branch(runner: GitRunner, branch: str) -> None:
    runner.run("push", "-u", runner.auth_remote(), branch)
