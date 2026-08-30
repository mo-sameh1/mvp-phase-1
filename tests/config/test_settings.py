from backend.config.settings import Settings


def test_secret_settings_strip_deployment_paste_wrappers() -> None:
    settings = Settings(
        github_token='"GITHUB_TOKEN=Bearer github_pat_example"',
        backend_api_key="\n'BACKEND_API_KEY=api-key'\r",
        github_webhook_secret="  GITHUB_WEBHOOK_SECRET=webhook-secret  ",
    )

    assert settings.github_token == "github_pat_example"
    assert settings.backend_api_key == "api-key"
    assert settings.github_webhook_secret == "webhook-secret"


def test_github_token_setting_strips_assignment_wrapped_quoted_token() -> None:
    settings = Settings(github_token='GITHUB_TOKEN="github_pat_example"')

    assert settings.github_token == "github_pat_example"
