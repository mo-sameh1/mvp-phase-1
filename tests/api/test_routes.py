from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api import routes
from backend.api.app import create_app
from backend.config.settings import Settings, get_settings
from backend.database.session import get_session
from backend.repository.artifacts import create_artifact_version
from backend.repository.jobs import create_job
from backend.repository.model_elements import upsert_model_element_index
from backend.repository.systems import create_legacy_system


def test_api_rejects_missing_and_wrong_api_key(session, tmp_path: Path) -> None:
    client = _client(session, _settings(tmp_path))

    missing = client.get("/jobs/job-1")
    wrong = client.get("/jobs/job-1", headers={"X-API-Key": "wrong"})

    assert missing.status_code == 401
    assert wrong.status_code == 401


def test_api_rejects_placeholder_api_key(session, tmp_path: Path) -> None:
    client = _client(session, Settings(backend_api_key="backend_api_key_placeholder"))

    response = client.get("/jobs/job-1", headers={"X-API-Key": "backend_api_key_placeholder"})

    assert response.status_code == 503


def test_trigger_ingestion_returns_queued_job(session, monkeypatch, tmp_path: Path) -> None:
    calls = []
    monkeypatch.setattr(
        routes,
        "run_as_is_job",
        lambda **kwargs: calls.append(kwargs),
    )
    settings = _settings(tmp_path)
    client = _client(session, settings)

    response = client.post("/systems/demo/ingest", headers=_headers())

    assert response.status_code == 202
    payload = response.json()
    assert payload["system_id"] == "demo"
    assert payload["phase"] == "as-is"
    assert payload["status"] == "queued"
    assert payload["run_id"] == f"as-is-{payload['job_id']}"
    assert calls[0]["system_id"] == "demo"
    assert calls[0]["evidence_path"] == settings.evidence_root


def test_read_job_returns_status_and_404(session, tmp_path: Path) -> None:
    create_legacy_system(session, system_id="demo", name="Demo")
    job = create_job(session, system_id="demo", phase="as-is", status="queued", run_id="run-1")
    client = _client(session, _settings(tmp_path))

    ok = client.get(f"/jobs/{job.id}", headers=_headers())
    missing = client.get("/jobs/missing", headers=_headers())

    assert ok.status_code == 200
    assert ok.json()["run_id"] == "run-1"
    assert missing.status_code == 404


def test_read_model_elements_filters_by_layer_and_requires_system(session, tmp_path: Path) -> None:
    create_legacy_system(session, system_id="demo", name="Demo")
    upsert_model_element_index(
        session,
        element_id="app-service",
        system_id="demo",
        layer="application",
        archimate_type="Application Service",
        name="App Service",
        git_path="systems/demo/as-is/application/app-service.json",
        current_commit="sha",
    )
    upsert_model_element_index(
        session,
        element_id="business-process",
        system_id="demo",
        layer="business",
        archimate_type="Business Process",
        name="Business Process",
        git_path="systems/demo/as-is/business/business-process.json",
        current_commit="sha",
    )
    client = _client(session, _settings(tmp_path))

    ok = client.get("/systems/demo/elements?layer=application", headers=_headers())
    missing = client.get("/systems/missing/elements", headers=_headers())

    assert ok.status_code == 200
    assert [item["id"] for item in ok.json()] == ["app-service"]
    assert missing.status_code == 404


def test_read_element_detail_loads_git_backed_json(session, monkeypatch, tmp_path: Path) -> None:
    create_legacy_system(session, system_id="demo", name="Demo")
    upsert_model_element_index(
        session,
        element_id="app-service",
        system_id="demo",
        layer="application",
        archimate_type="Application Service",
        name="App Service",
        git_path="systems/demo/as-is/application/app-service.json",
        current_commit="sha",
    )
    monkeypatch.setattr(
        routes,
        "show_file_at_ref",
        lambda runner, ref, path: json.dumps(_model_payload()),
    )
    client = _client(session, _settings(tmp_path))

    ok = client.get("/elements/app-service", headers=_headers())
    missing = client.get("/elements/missing", headers=_headers())

    assert ok.status_code == 200
    assert ok.json()["element"]["evidence"][0]["excerpt"] == "Source evidence."
    assert missing.status_code == 404


def test_read_artifact_versions_returns_pr_status_and_requires_system(
    session,
    tmp_path: Path,
) -> None:
    create_legacy_system(session, system_id="demo", name="Demo")
    create_artifact_version(
        session,
        system_id="demo",
        commit_sha="sha",
        phase="as-is",
        author_type="agent",
        run_id="run-1",
        approval_status="pending",
        pr_number=3,
        pr_url="https://github.com/example/repo/pull/3",
    )
    client = _client(session, _settings(tmp_path))

    ok = client.get("/systems/demo/artifact-versions", headers=_headers())
    missing = client.get("/systems/missing/artifact-versions", headers=_headers())

    assert ok.status_code == 200
    assert ok.json()[0]["pr_url"] == "https://github.com/example/repo/pull/3"
    assert ok.json()[0]["approval_status"] == "pending"
    assert missing.status_code == 404


def _client(session, settings: Settings) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        evidence_root=str(tmp_path / "evidence"),
        model_repo_checkout=str(tmp_path / "model"),
        github_model_repo="example/repo",
        github_token="token",
        backend_api_key="api-key",
    )


def _headers() -> dict[str, str]:
    return {"X-API-Key": "api-key"}


def _model_payload() -> dict:
    return {
        "id": "app-service",
        "layer": "application",
        "archimate_type": "Application Service",
        "name": "App Service",
        "documentation": "Application service detail.",
        "confidence": "observed",
        "evidence": [
            {
                "source_type": "code",
                "locator": "src/app.py:1",
                "excerpt": "Source evidence.",
            }
        ],
        "relationships": [],
    }
