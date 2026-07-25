import os
import sys

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

REQUIRED_ENV = [
    "LANGCHAIN_TRACING_V2",
    "LANGCHAIN_API_KEY",
    "LANGCHAIN_PROJECT",
    "ANTHROPIC_API_KEY",
]


def main() -> int:
    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        return 1

    model = ChatAnthropic(model="claude-3-5-haiku-latest", temperature=0)
    response = model.invoke([HumanMessage(content="Reply with exactly: langsmith-smoke-ok")])
    print(response.content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
