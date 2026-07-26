from __future__ import annotations

import os

TRACE_ENV = [
    "LANGCHAIN_TRACING_V2",
    "LANGCHAIN_API_KEY",
    "LANGCHAIN_PROJECT",
]

PROVIDER_ENV = {
    "ollama": ["OLLAMA_MODEL"],
    "groq": ["GROQ_API_KEY", "GROQ_MODEL"],
    "anthropic": ["ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"],
}


def selected_provider() -> str:
    return os.getenv("LLM_PROVIDER", "ollama").strip().lower()


def supported_providers() -> list[str]:
    return sorted(PROVIDER_ENV)


def required_env(provider: str) -> list[str]:
    if provider not in PROVIDER_ENV:
        supported = ", ".join(supported_providers())
        raise ValueError(f"Unsupported LLM_PROVIDER '{provider}'. Choose one of: {supported}")
    return TRACE_ENV + PROVIDER_ENV[provider]


def missing_required_env(provider: str) -> list[str]:
    return [name for name in required_env(provider) if not os.getenv(name)]


def build_chat_model(provider: str | None = None):
    provider = provider or selected_provider()

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
        )

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(model=os.environ["GROQ_MODEL"], temperature=0)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=os.environ["ANTHROPIC_MODEL"], temperature=0)

    supported = ", ".join(supported_providers())
    raise ValueError(f"Unsupported LLM_PROVIDER '{provider}'. Choose one of: {supported}")
