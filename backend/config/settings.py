from functools import lru_cache

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://mvp_app:mvp_app_password@localhost:5433/mvp_phase1"
    test_database_url: str = (
        "postgresql+psycopg://mvp_app:mvp_app_password@localhost:5433/mvp_phase1_test"
    )
    model_repo_system_id: str = "demo-legacy-system"
    evidence_root: str = "reference/evidence"
    model_repo_checkout: str = "../mvp-phase1-model"
    github_model_repo: str = "mo-sameh1/mvp-phase1-model"
    github_token: str = "github_pat_placeholder"
    github_webhook_secret: str = "github_webhook_secret_placeholder"
    backend_api_key: str = "backend_api_key_placeholder"
    cors_allowed_origins: str = ""
    langchain_tracing_v2: str = "true"
    langchain_api_key: str = "langsmith_api_key_placeholder"
    langchain_project: str = "7bots-mvp-phase1-dev"
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_api_key: str = "ollama_api_key_placeholder"
    ollama_model: str = "llama3.1"
    groq_api_key: str = "groq_api_key_placeholder"
    groq_model: str = "llama-3.3-70b-versatile"
    anthropic_api_key: str = "anthropic_api_key_placeholder"
    anthropic_model: str = "claude-3-5-haiku-latest"

    @field_validator(
        "github_token",
        "github_webhook_secret",
        "backend_api_key",
        "langchain_api_key",
        "ollama_api_key",
        "groq_api_key",
        "anthropic_api_key",
        mode="before",
    )
    @classmethod
    def normalize_secret_value(cls, value: object, info: ValidationInfo) -> object:
        if not isinstance(value, str):
            return value

        normalized = _strip_secret_wrappers(value)
        assignment_prefix = f"{info.field_name.upper()}="
        if normalized.startswith(assignment_prefix):
            normalized = _strip_secret_wrappers(normalized.removeprefix(assignment_prefix))

        if info.field_name == "github_token":
            for prefix in ("Bearer ", "bearer ", "token "):
                if normalized.startswith(prefix):
                    normalized = _strip_secret_wrappers(normalized.removeprefix(prefix))

        return normalized


def _strip_secret_wrappers(value: str) -> str:
    normalized = value.replace("\r", "").replace("\n", "").strip()
    if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {"'", '"'}:
        normalized = normalized[1:-1].strip()
    return normalized


@lru_cache
def get_settings() -> Settings:
    return Settings()
