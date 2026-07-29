from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents.ingestion.profiles import IngestionSubagentProfile, list_ingestion_profiles
from agents.runtime.deep_agent import create_base_agent
from backend.config.settings import Settings

DEFAULT_PROVIDER_RETRY_ATTEMPTS = 2


class IngestionRuntimeError(RuntimeError):
    """Raised when live ingestion subagent execution cannot complete."""


@dataclass(frozen=True)
class IngestionSubagentRun:
    name: str
    attempts: int
    result: Any


def run_ingestion_subagents(
    *,
    system_id: str,
    run_id: str,
    evidence_route: str,
    systems_root: Path,
    settings: Settings,
    trace_config_factory: Callable[[str], dict[str, Any]],
    retry_attempts: int = DEFAULT_PROVIDER_RETRY_ATTEMPTS,
) -> list[IngestionSubagentRun]:
    """Run Epic E subagents in Python-owned order while keeping each subagent live."""
    results: list[IngestionSubagentRun] = []
    for profile in list_ingestion_profiles():
        agent = create_base_agent(
            settings=settings,
            system_prompt=profile.system_prompt,
            tools=profile.tools,
            name=f"epic-e-{profile.name}",
        )
        result, attempts = _invoke_with_provider_retry(
            agent=agent,
            payload={
                "messages": [
                    {
                        "role": "user",
                        "content": _subagent_prompt(
                            profile=profile,
                            system_id=system_id,
                            run_id=run_id,
                            evidence_route=evidence_route,
                            systems_root=systems_root,
                        ),
                    }
                ]
            },
            config=trace_config_factory(profile.name),
            subagent_name=profile.name,
            retry_attempts=retry_attempts,
        )
        results.append(IngestionSubagentRun(name=profile.name, attempts=attempts, result=result))
    return results


def _subagent_prompt(
    *,
    profile: IngestionSubagentProfile,
    system_id: str,
    run_id: str,
    evidence_route: str,
    systems_root: Path,
) -> str:
    relationship_instruction = (
        "Append only relationships whose source and target IDs already exist. Use "
        "append_model_relationship_tool for every accepted relationship candidate."
        if profile.name == "integration-mapper"
        else (
            "Write accepted elements with write_model_element_tool. Pass relationships: [] on "
            "every element; relationship creation is owned by integration-mapper."
        )
    )
    return f"""
Run only the Epic E {profile.name} task.

Do not call task. Do not call write_todos. The Python orchestrator owns run order and progress.

Inputs:
- system_id: {system_id}
- run_id: {run_id}
- evidence root selected for this run: {evidence_route}
- allowed evidence roots for this subagent: {", ".join(profile.evidence_roots)}
- writable model output route: /systems/{system_id}/as-is/
- deterministic systems_root for ingestion tools: {systems_root}

Instructions:
- Read only the allowed evidence roots above.
- Use the archimate-metamodel skill before choosing any ArchiMate type or relationship.
- {relationship_instruction}
- Do not call write_file or edit_file for model JSON.
- If a candidate lacks exact evidence, report it as skipped.
- If a tool returns rejected or skipped, report the reason and continue only when the evidence
  supports a corrected retry.

When finished, summarize written IDs and skipped candidates in a concise final response.
"""


def _invoke_with_provider_retry(
    *,
    agent: Any,
    payload: dict[str, Any],
    config: dict[str, Any],
    subagent_name: str,
    retry_attempts: int,
) -> tuple[Any, int]:
    last_error: Exception | None = None
    for attempt in range(1, retry_attempts + 1):
        try:
            return agent.invoke(payload, config=config), attempt
        except Exception as exc:  # noqa: BLE001 - provider packages use different exception types.
            last_error = exc
            if attempt >= retry_attempts or not _is_transient_provider_error(exc):
                break
    assert last_error is not None
    raise IngestionRuntimeError(
        f"{subagent_name} failed after {retry_attempts} attempt(s): "
        f"{type(last_error).__name__}: {_sanitize_error_message(str(last_error))}"
    ) from last_error


def _is_transient_provider_error(exc: Exception) -> bool:
    message = str(exc).casefold()
    return any(
        marker in message
        for marker in (
            "internal server error",
            "status code: 500",
            "temporarily unavailable",
            "timeout",
            "timed out",
            "connection reset",
        )
    )


def _sanitize_error_message(message: str) -> str:
    return message.replace("\n", " ")[:500]
