from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from pydantic import ValidationError

from agents.ingestion.model_io import append_relationship, write_model_element
from agents.runtime.filesystem import RuntimePaths
from agents.schema import ModelElement, RelationshipRef
from backend.config.settings import get_settings


def validate_model_element_payload(payload: dict[str, Any]) -> ModelElement:
    """Validate an LLM-proposed element before it is allowed onto disk."""
    return ModelElement(**payload)


@tool
def write_model_element_tool(
    element: dict[str, Any],
    systems_root: str | None = None,
    system_id: str | None = None,
) -> dict[str, Any]:
    """Validate and write one agents.schema.ModelElement JSON file.

    systems_root is optional, but when supplied it must be the exact absolute path ending in
    /systems from the task prompt. Do not pass /, /systems/, or a virtual DeepAgents path.
    """
    try:
        validated = validate_model_element_payload(element)
        if validated.relationships:
            return {
                "status": "rejected",
                "written": False,
                "reason": (
                    "write_model_element_tool accepts element facts only. Set relationships to [] "
                    "and use append_model_relationship_tool after all target IDs exist."
                ),
            }
        resolved_systems_root, resolved_system_id = _resolve_tool_context(
            systems_root=systems_root,
            system_id=system_id,
        )
        path = write_model_element(resolved_systems_root, resolved_system_id, validated)
    except (ValidationError, ValueError) as exc:
        return {
            "status": "rejected",
            "written": False,
            "reason": str(exc),
        }

    return {
        "status": "written",
        "written": True,
        "id": validated.id,
        "layer": validated.layer,
        "archimate_type": validated.archimate_type,
        "path": str(path),
    }


@tool
def append_model_relationship_tool(
    source_id: str,
    relationship: dict[str, Any],
    systems_root: str | None = None,
    system_id: str | None = None,
) -> dict[str, Any]:
    """Validate and append one evidence-cited relationship to an existing model element.

    systems_root is optional, but when supplied it must be the exact absolute path ending in
    /systems from the task prompt. Do not pass /, /systems/, or a virtual DeepAgents path.
    """
    try:
        validated = RelationshipRef(**relationship)
        resolved_systems_root, resolved_system_id = _resolve_tool_context(
            systems_root=systems_root,
            system_id=system_id,
        )
        decision = append_relationship(
            systems_root=resolved_systems_root,
            system_id=resolved_system_id,
            source_id=source_id,
            relationship=validated,
        )
    except (ValidationError, ValueError) as exc:
        return {
            "status": "rejected",
            "written": False,
            "source_id": source_id,
            "reason": str(exc),
        }

    return {
        "status": "written" if decision.written else "skipped",
        "written": decision.written,
        "source_id": decision.source_id,
        "target_id": decision.target_id,
        "relationship_type": decision.relationship_type,
        "reason": decision.reason,
        "citation": decision.citation,
    }


def _resolve_tool_context(
    *,
    systems_root: str | None,
    system_id: str | None,
) -> tuple[Path, str]:
    settings = get_settings()
    configured_systems_root = RuntimePaths.from_settings(settings).systems_root.resolve()
    resolved_systems_root = (
        Path(systems_root).expanduser().resolve() if systems_root else configured_systems_root
    )
    if resolved_systems_root.name != "systems":
        raise ValueError(
            "systems_root must point to the model repository systems directory. "
            "Omit systems_root or pass the exact .../systems value from the orchestration prompt."
        )
    return resolved_systems_root, system_id or settings.model_repo_system_id
