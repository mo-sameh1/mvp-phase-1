from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class GitHubClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitHubClient:
    repo: str
    token: str
    api_base_url: str = "https://api.github.com"

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
    ) -> Any:
        url = f"{self.api_base_url.rstrip('/')}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, method=method)
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        request.add_header("User-Agent", "7bots-mvp-phase1")
        request.add_header("Authorization", "Bearer <redacted>")
        request.headers["Authorization"] = f"Bearer {self.token}"
        if body is not None:
            request.add_header("Content-Type", "application/json")

        try:
            with urlopen(request, timeout=30) as response:
                content = response.read().decode("utf-8")
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise GitHubClientError(
                f"GitHub API {method} {path} failed with {exc.code}: {details}"
            ) from exc
        if not content:
            return None
        return json.loads(content)

    def list_open_pull_requests(self, *, head: str, base: str = "main") -> list[dict[str, Any]]:
        return self.request(
            "GET",
            f"/repos/{self.repo}/pulls",
            query={"state": "open", "head": head, "base": base},
        )

    def create_pull_request(
        self,
        *,
        title: str,
        head: str,
        base: str,
        body: str,
    ) -> dict[str, Any]:
        return self.request(
            "POST",
            f"/repos/{self.repo}/pulls",
            payload={"title": title, "head": head, "base": base, "body": body},
        )
