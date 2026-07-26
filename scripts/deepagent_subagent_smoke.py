import sys
from typing import Any

from agents.runtime.llm import missing_required_env, selected_provider
from agents.runtime.subagents import PLACEHOLDER_SUBAGENT_NAMES, create_placeholder_orchestrator


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

    names = ", ".join(PLACEHOLDER_SUBAGENT_NAMES)
    prompt = (
        "Use the task tool once for each of these subagents, in this exact order: "
        f"{names}. For each delegated task, ask only: 'Return your exact stub response.' "
        "After all five finish, reply with one line in the format "
        "strategy-analyst=stub-ok; business-analyst=stub-ok; code-analyzer=stub-ok; "
        "infra-analyzer=stub-ok; integration-mapper=stub-ok"
    )

    try:
        agent = create_placeholder_orchestrator()
        result = agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config={"configurable": {"thread_id": "epic-d-subagent-smoke"}},
        )
    except Exception as exc:
        print(f"Deep Agent subagent smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    text = latest_text(result)
    print(text)
    missing_names = [name for name in PLACEHOLDER_SUBAGENT_NAMES if f"{name}=stub-ok" not in text]
    if missing_names:
        print(
            f"Missing expected subagent smoke markers: {', '.join(missing_names)}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
