import json

from fastapi.testclient import TestClient

from backend.api import app as app_module
from backend.api.app import create_app
from backend.config.settings import Settings
from backend.database.session import get_session
from backend.gitops import webhooks
from backend.gitops.webhook_security import sign_github_body, verify_github_signature
from backend.gitops.webhooks import WebhookResult
from backend.repository import (
    create_artifact_version,
    create_legacy_system,
    get_artifact_version,
)


def test_verify_github_signature_accepts_only_matching_signature() -> None:
    body = b'{"ok": true}'
    signature = sign_github_body("secret", body)

    assert verify_github_signature("secret", body, signature)
    assert not verify_github_signature("secret", body, "sha256=bad")
    assert not verify_github_signature("secret", body, None)


def test_handle_pull_request_webhook_approves_artifact_idempotently(
    session,
    monkeypatch,
    tmp_path,
) -> None:
    create_legacy_system(session, system_id="demo", name="Demo")
    artifact = create_artifact_version(
        session,
        system_id="demo",
        commit_sha="sha",
        phase="as-is",
        author_type="agent",
        run_id="run-1",
        pr_number=42,
        pr_url="https://github.com/example/repo/pull/42",
    )
    calls = []
    monkeypatch.setattr(
        webhooks,
        "refresh_model_element_index",
        lambda *args, **kwargs: calls.append(kwargs["system_id"]) or 3,
    )
    settings = Settings(
        model_repo_checkout=str(tmp_path),
        github_model_repo="example/repo",
        github_token="token",
    )

    result = webhooks.handle_pull_request_webhook(session, _merged_payload(), settings)
    repeated = webhooks.handle_pull_request_webhook(session, _merged_payload(), settings)

    assert result.status == "approved"
    assert repeated.status == "already_approved"
    assert calls == ["demo"]
    assert get_artifact_version(session, artifact.id).approval_status == "approved"
    assert get_artifact_version(session, artifact.id).approved_by == "reviewer"


def test_handle_pull_request_webhook_ignores_non_merged_event(session, tmp_path) -> None:
    create_legacy_system(session, system_id="demo", name="Demo")
    artifact = create_artifact_version(
        session,
        system_id="demo",
        commit_sha="sha",
        phase="as-is",
        author_type="agent",
        run_id="run-1",
        pr_number=42,
        pr_url="https://github.com/example/repo/pull/42",
    )
    settings = Settings(model_repo_checkout=str(tmp_path), github_model_repo="example/repo")

    result = webhooks.handle_pull_request_webhook(
        session,
        {"action": "closed", "pull_request": {"number": 42, "merged": False}},
        settings,
    )

    assert result.status == "rejected"
    assert result.approved is False
    assert get_artifact_version(session, artifact.id).approval_status == "rejected"


def test_handle_pull_request_webhook_reopens_rejected_artifact(session, tmp_path) -> None:
    create_legacy_system(session, system_id="demo", name="Demo")
    artifact = create_artifact_version(
        session,
        system_id="demo",
        commit_sha="sha",
        phase="as-is",
        author_type="agent",
        run_id="run-1",
        approval_status="rejected",
        pr_number=42,
        pr_url="https://github.com/example/repo/pull/42",
    )
    settings = Settings(model_repo_checkout=str(tmp_path), github_model_repo="example/repo")

    result = webhooks.handle_pull_request_webhook(
        session,
        {"action": "reopened", "pull_request": {"number": 42, "merged": False}},
        settings,
    )

    assert result.status == "pending"
    assert result.approved is False
    assert get_artifact_version(session, artifact.id).approval_status == "pending"


def test_handle_pull_request_webhook_keeps_approved_artifact_final(
    session,
    monkeypatch,
    tmp_path,
) -> None:
    create_legacy_system(session, system_id="demo", name="Demo")
    artifact = create_artifact_version(
        session,
        system_id="demo",
        commit_sha="sha",
        phase="as-is",
        author_type="agent",
        run_id="run-1",
        approval_status="approved",
        pr_number=42,
        pr_url="https://github.com/example/repo/pull/42",
    )
    monkeypatch.setattr(webhooks, "refresh_model_element_index", lambda *args, **kwargs: 0)
    settings = Settings(model_repo_checkout=str(tmp_path), github_model_repo="example/repo")

    closed = webhooks.handle_pull_request_webhook(
        session,
        {"action": "closed", "pull_request": {"number": 42, "merged": False}},
        settings,
    )
    reopened = webhooks.handle_pull_request_webhook(
        session,
        {"action": "reopened", "pull_request": {"number": 42, "merged": False}},
        settings,
    )
    merged = webhooks.handle_pull_request_webhook(session, _merged_payload(), settings)

    assert closed.status == "already_approved"
    assert reopened.status == "already_approved"
    assert merged.status == "already_approved"
    assert get_artifact_version(session, artifact.id).approval_status == "approved"


def test_github_webhook_endpoint_rejects_missing_or_wrong_signature(session, tmp_path) -> None:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    client = TestClient(app)

    response = client.post("/webhooks/github", json={})

    assert response.status_code == 401


def test_health_check_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"health": "OK"}


def test_github_webhook_endpoint_accepts_valid_signature(session, monkeypatch, tmp_path) -> None:
    app = create_app()
    settings = Settings(
        github_webhook_secret="secret",
        model_repo_checkout=str(tmp_path),
        github_model_repo="example/repo",
        github_token="token",
    )
    monkeypatch.setattr(
        app_module,
        "handle_pull_request_webhook",
        lambda session, payload, settings: WebhookResult(status="approved", approved=True),
    )
    app.dependency_overrides[get_session] = lambda: session
    from backend.config.settings import get_settings

    app.dependency_overrides[get_settings] = lambda: settings
    body = json.dumps(_merged_payload()).encode("utf-8")
    client = TestClient(app)

    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": sign_github_body("secret", body),
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def _merged_payload() -> dict:
    return {
        "action": "closed",
        "pull_request": {"number": 42, "merged": True},
        "sender": {"login": "reviewer"},
    }
