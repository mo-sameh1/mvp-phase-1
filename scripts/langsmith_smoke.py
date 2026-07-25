import os
import sys

from langchain_core.messages import HumanMessage

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


def required_env(provider: str) -> list[str]:
    if provider not in PROVIDER_ENV:
        supported = ", ".join(sorted(PROVIDER_ENV))
        raise ValueError(f"Unsupported LLM_PROVIDER '{provider}'. Choose one of: {supported}")
    return TRACE_ENV + PROVIDER_ENV[provider]


def build_model(provider: str):
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

    supported = ", ".join(sorted(PROVIDER_ENV))
    raise ValueError(f"Unsupported LLM_PROVIDER '{provider}'. Choose one of: {supported}")


def main() -> int:
    provider = selected_provider()
    try:
        missing = [name for name in required_env(provider) if not os.getenv(name)]
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        return 1

    model = build_model(provider)
    response = model.invoke([HumanMessage(content="Reply with exactly: langsmith-smoke-ok")])
    print(response.content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
