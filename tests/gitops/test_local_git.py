from pathlib import Path

from backend.gitops.local_git import GitRunner


def test_git_runner_uses_extraheader_auth_without_tokenized_remote() -> None:
    runner = GitRunner(Path("/tmp/model"), "example/repo", "github_pat_example")

    assert runner.auth_remote() == "https://github.com/example/repo.git"
    env = runner._env()
    assert env["GIT_CONFIG_KEY_0"] == "http.https://github.com/.extraheader"
    assert env["GIT_CONFIG_VALUE_0"] == "AUTHORIZATION: bearer github_pat_example"
