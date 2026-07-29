from backend.api.model_content import build_model_json_url


def test_build_model_json_url_normalizes_repo_and_escapes_path() -> None:
    url = build_model_json_url(
        github_model_repo="https://github.com/example/repo.git",
        commit_sha="abc123",
        git_path="systems/demo system/as-is/application/app service.json",
    )

    assert (
        url == "https://github.com/example/repo/blob/abc123/"
        "systems/demo%20system/as-is/application/app%20service.json"
    )
