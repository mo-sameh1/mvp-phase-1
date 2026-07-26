import sys

from langchain_core.messages import HumanMessage

from agents.runtime.llm import (
    build_chat_model,
    missing_required_env,
    required_env,
    selected_provider,
)

__all__ = ["required_env", "selected_provider"]


def main() -> int:
    provider = selected_provider()
    try:
        missing = missing_required_env(provider)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        return 1

    model = build_chat_model(provider)
    response = model.invoke([HumanMessage(content="Reply with exactly: langsmith-smoke-ok")])
    print(response.content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
