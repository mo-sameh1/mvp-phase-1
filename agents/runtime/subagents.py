from __future__ import annotations

from typing import Any

from agents.runtime.deep_agent import create_base_agent

PLACEHOLDER_SUBAGENT_NAMES = [
    "strategy-analyst",
    "business-analyst",
    "code-analyzer",
    "infra-analyzer",
    "integration-mapper",
]

PLACEHOLDER_SYSTEM_PROMPT = "Respond with exactly: stub-ok"


def build_placeholder_subagents() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": f"Epic D placeholder for the future Epic E {name} ingestion subagent.",
            "system_prompt": PLACEHOLDER_SYSTEM_PROMPT,
        }
        for name in PLACEHOLDER_SUBAGENT_NAMES
    ]


def create_placeholder_orchestrator():
    return create_base_agent(subagents=build_placeholder_subagents())
