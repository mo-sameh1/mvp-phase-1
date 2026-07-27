import pytest

from agents.runtime.llm import missing_required_env, ollama_base_url, ollama_client_kwargs
from scripts.langsmith_smoke import required_env, selected_provider

TRACE_ENV = {
    "LANGCHAIN_TRACING_V2": "true",
    "LANGCHAIN_API_KEY": "langsmith-key",
    "LANGCHAIN_PROJECT": "project",
}


def test_selected_provider_defaults_to_ollama(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    assert selected_provider() == "ollama"


def test_required_env_for_ollama():
    assert required_env("ollama") == [
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_PROJECT",
        "OLLAMA_MODEL",
    ]


def test_required_env_for_groq():
    assert required_env("groq") == [
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_PROJECT",
        "GROQ_API_KEY",
        "GROQ_MODEL",
    ]


def test_required_env_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        required_env("unknown")


def test_ollama_local_does_not_require_api_key(monkeypatch):
    for name, value in TRACE_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)

    assert missing_required_env("ollama") == []
    assert ollama_base_url() == "http://localhost:11434"
    assert ollama_client_kwargs() == {}


def test_ollama_cloud_uses_base_url_and_api_key(monkeypatch):
    for name, value in TRACE_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
    monkeypatch.setenv("OLLAMA_BASE_URL", "https://ollama.com")
    monkeypatch.setenv("OLLAMA_API_KEY", "ollama-key")

    assert missing_required_env("ollama") == []
    assert ollama_base_url() == "https://ollama.com"
    assert ollama_client_kwargs() == {"headers": {"Authorization": "Bearer ollama-key"}}


def test_ollama_api_key_can_be_used_with_custom_host(monkeypatch):
    for name, value in TRACE_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
    monkeypatch.setenv("OLLAMA_BASE_URL", "https://ollama.internal.example")
    monkeypatch.setenv("OLLAMA_API_KEY", "custom-key")

    assert missing_required_env("ollama") == []
    assert ollama_base_url() == "https://ollama.internal.example"
    assert ollama_client_kwargs() == {"headers": {"Authorization": "Bearer custom-key"}}
