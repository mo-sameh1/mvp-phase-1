import io
from urllib.error import HTTPError

import pytest

from backend.gitops import github_client
from backend.gitops.github_client import GitHubClient, GitHubClientError


def test_github_client_adds_auth_header_and_parses_json(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["authorization"] = request.headers["Authorization"]
        captured["timeout"] = timeout
        return FakeResponse(b'{"ok": true}')

    monkeypatch.setattr(github_client, "urlopen", fake_urlopen)

    result = GitHubClient("example/repo", "secret-token").request("GET", "/example")

    assert result == {"ok": True}
    assert captured["authorization"] == "Bearer secret-token"
    assert captured["timeout"] == 30


def test_github_client_error_does_not_include_token(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        raise HTTPError(
            url="https://api.github.com/example",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(b'{"message": "bad credentials"}'),
        )

    monkeypatch.setattr(github_client, "urlopen", fake_urlopen)

    with pytest.raises(GitHubClientError) as exc:
        GitHubClient("example/repo", "secret-token").request("GET", "/example")

    assert "secret-token" not in str(exc.value)
    assert "bad credentials" in str(exc.value)


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.body
