from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends.protocol import BackendProtocol
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

from agents.runtime.filesystem import (
    RuntimePaths,
    build_runtime_backend,
    ensure_runtime_directories,
    filesystem_permissions,
)
from agents.runtime.llm import build_chat_model
from backend.config.settings import Settings

ARCHIMATE_SKILLS_PATH = "/skills/"

BASE_SYSTEM_PROMPT = """You are the 7bots.ai Phase 1 as-is architecture agent.

Use the ArchiMate metamodel skill whenever classifying or validating architecture elements.
Every architecture fact must be traceable to evidence. If the skill or structured validator does not
establish an ArchiMate rule, fail closed instead of guessing.
"""


def create_base_agent(
    *,
    model: str | BaseChatModel | None = None,
    backend: BackendProtocol | None = None,
    subagents: Sequence[dict[str, Any]] | None = None,
    tools: Sequence[BaseTool | Any] | None = None,
    settings: Settings | None = None,
    system_prompt: str = BASE_SYSTEM_PROMPT,
    name: str = "phase1-base-agent",
):
    paths = RuntimePaths.from_settings(settings)
    ensure_runtime_directories(paths)
    return create_deep_agent(
        model=model or build_chat_model(),
        tools=tools,
        backend=backend or build_runtime_backend(paths),
        skills=[ARCHIMATE_SKILLS_PATH],
        permissions=filesystem_permissions(),
        subagents=subagents,
        system_prompt=system_prompt,
        name=name,
    )
