from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://mvp_app:mvp_app_password@localhost:5433/mvp_phase1"
    test_database_url: str = (
        "postgresql+psycopg://mvp_app:mvp_app_password@localhost:5433/mvp_phase1_test"
    )
    model_repo_system_id: str = "demo-legacy-system"
    github_model_repo: str = "mo-sameh1/mvp-phase1-model"
    github_token: str = "github_pat_placeholder"
    langchain_tracing_v2: str = "true"
    langchain_api_key: str = "langsmith_api_key_placeholder"
    langchain_project: str = "7bots-mvp-phase1-dev"
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    groq_api_key: str = "groq_api_key_placeholder"
    groq_model: str = "llama-3.3-70b-versatile"
    anthropic_api_key: str = "anthropic_api_key_placeholder"
    anthropic_model: str = "claude-3-5-haiku-latest"


@lru_cache
def get_settings() -> Settings:
    return Settings()
