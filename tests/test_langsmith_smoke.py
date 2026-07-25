import pytest

from scripts.langsmith_smoke import required_env, selected_provider


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
