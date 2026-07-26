import sys
from typing import Any

from agents.runtime.deep_agent import create_base_agent
from agents.runtime.llm import missing_required_env, selected_provider


def latest_text(result: Any) -> str:
    messages = result.get("messages", []) if isinstance(result, dict) else []
    if not messages:
        return ""
    latest = messages[-1]
    content = (
        latest.get("content", "") if isinstance(latest, dict) else getattr(latest, "content", "")
    )
    if isinstance(content, str):
        return content
    return str(content)


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

    try:
        agent = create_base_agent()
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Reply with exactly: deepagent-smoke-ok",
                    }
                ]
            },
            config={"configurable": {"thread_id": "epic-d-base-smoke"}},
        )
    except Exception as exc:
        print(f"Deep Agent smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    text = latest_text(result)
    print(text)
    return 0 if "deepagent-smoke-ok" in text else 1


if __name__ == "__main__":
    raise SystemExit(main())
