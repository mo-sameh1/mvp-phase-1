from backend.config.settings import Settings
from scripts import epic_h_smoke


def test_epic_h_smoke_reports_missing_live_config(monkeypatch):
    monkeypatch.setattr(epic_h_smoke, "selected_provider", lambda: "groq")
    monkeypatch.setattr(epic_h_smoke, "missing_required_env", lambda provider: [])

    settings = Settings(
        backend_api_key="backend_api_key_placeholder",
        github_token="github_pat_placeholder",
    )

    missing = epic_h_smoke._missing_live_config(settings)

    assert "BACKEND_API_KEY" in missing
    assert "GITHUB_TOKEN" in missing
