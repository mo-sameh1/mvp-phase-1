from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from pydantic import ValidationError

from agents.archimate_metamodel import list_element_types
from agents.ingestion.model_io import append_relationship, slugify, write_model_element
from agents.runtime.filesystem import RuntimePaths
from agents.schema import ModelElement, RelationshipRef
from backend.config.settings import get_settings


def validate_model_element_payload(payload: dict[str, Any]) -> ModelElement:
    """Validate an LLM-proposed element before it is allowed onto disk."""
    return ModelElement(**payload)


@tool
def write_model_element_tool(
    element: dict[str, Any],
    run_id: str,
    systems_root: str | None = None,
    system_id: str | None = None,
) -> dict[str, Any]:
    """Validate and write one agents.schema.ModelElement JSON file.

    systems_root is optional, but when supplied it must be the exact absolute path ending in
    /systems from the task prompt. Do not pass /, /systems/, or a virtual DeepAgents path.
    """
    try:
        resolved_systems_root, resolved_system_id = _resolve_tool_context(
            systems_root=systems_root,
            system_id=system_id,
        )
        validated = validate_model_element_payload(_canonicalize_element_payload(element))
    except (ValidationError, ValueError) as exc:
        result = {
            "status": "rejected",
            "written": False,
            "reason": str(exc),
        }
        if "resolved_systems_root" in locals() and "resolved_system_id" in locals():
            _record_ingestion_tool_event(
                systems_root=resolved_systems_root,
                system_id=resolved_system_id,
                run_id=run_id,
                tool_name="write_model_element_tool",
                result=result,
            )
        raise ValueError(f"Ingestion tool rejected candidate: {exc}") from exc

    if validated.relationships:
        reason = (
            "write_model_element_tool accepts element facts only. Set relationships to [] "
            "and use append_model_relationship_tool after all target IDs exist."
        )
        result = {"status": "rejected", "written": False, "reason": reason}
        _record_ingestion_tool_event(
            systems_root=resolved_systems_root,
            system_id=resolved_system_id,
            run_id=run_id,
            tool_name="write_model_element_tool",
            result=result,
        )
        raise ValueError(f"Ingestion tool rejected candidate: {reason}")

    path = write_model_element(resolved_systems_root, resolved_system_id, validated)

    result = {
        "status": "written",
        "written": True,
        "id": validated.id,
        "layer": validated.layer,
        "archimate_type": validated.archimate_type,
        "path": str(path),
    }
    _record_ingestion_tool_event(
        systems_root=resolved_systems_root,
        system_id=resolved_system_id,
        run_id=run_id,
        tool_name="write_model_element_tool",
        result=result,
    )
    return result


@tool
def append_model_relationship_tool(
    source_id: str,
    relationship: dict[str, Any],
    run_id: str,
    systems_root: str | None = None,
    system_id: str | None = None,
) -> dict[str, Any]:
    """Validate and append one evidence-cited relationship to an existing model element.

    systems_root is optional, but when supplied it must be the exact absolute path ending in
    /systems from the task prompt. Do not pass /, /systems/, or a virtual DeepAgents path.
    """
    try:
        canonical_source_id = slugify(source_id)
        validated = RelationshipRef(**_canonicalize_relationship_payload(relationship))
        resolved_systems_root, resolved_system_id = _resolve_tool_context(
            systems_root=systems_root,
            system_id=system_id,
        )
        decision = append_relationship(
            systems_root=resolved_systems_root,
            system_id=resolved_system_id,
            source_id=canonical_source_id,
            relationship=validated,
        )
    except (ValidationError, ValueError) as exc:
        result = {
            "status": "rejected",
            "written": False,
            "source_id": source_id,
            "reason": str(exc),
        }
        if "resolved_systems_root" in locals() and "resolved_system_id" in locals():
            _record_ingestion_tool_event(
                systems_root=resolved_systems_root,
                system_id=resolved_system_id,
                run_id=run_id,
                tool_name="append_model_relationship_tool",
                result=result,
            )
        raise ValueError(f"Ingestion tool rejected candidate: {exc}") from exc

    result = {
        "status": "written" if decision.written else "skipped",
        "written": decision.written,
        "source_id": decision.source_id,
        "target_id": decision.target_id,
        "relationship_type": decision.relationship_type,
        "reason": decision.reason,
        "citation": decision.citation,
    }
    _record_ingestion_tool_event(
        systems_root=resolved_systems_root,
        system_id=resolved_system_id,
        run_id=run_id,
        tool_name="append_model_relationship_tool",
        result=result,
    )
    return result


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


def _canonicalize_element_payload(payload: dict[str, Any]) -> dict[str, Any]:
    canonical = dict(payload)
    if isinstance(canonical.get("id"), str):
        canonical["id"] = slugify(canonical["id"])
    if isinstance(canonical.get("layer"), str) and isinstance(canonical.get("archimate_type"), str):
        canonical["archimate_type"] = _canonicalize_archimate_type(
            layer=canonical["layer"],
            archimate_type=canonical["archimate_type"],
        )
    return canonical


def _canonicalize_relationship_payload(payload: dict[str, Any]) -> dict[str, Any]:
    canonical = dict(payload)
    if isinstance(canonical.get("target_id"), str):
        canonical["target_id"] = slugify(canonical["target_id"])
    return canonical


def _canonicalize_archimate_type(*, layer: str, archimate_type: str) -> str:
    requested = _compact_name(archimate_type)
    for valid_type in list_element_types(layer):
        if _compact_name(valid_type) == requested:
            return valid_type
    return archimate_type


def _compact_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _record_ingestion_tool_event(
    *,
    systems_root: Path,
    system_id: str,
    run_id: str,
    tool_name: str,
    result: dict[str, Any],
) -> None:
    if not run_id or "/" in run_id or "\\" in run_id or run_id in {".", ".."}:
        raise ValueError("run_id must be a non-empty path-safe run identifier")
    path = systems_root / system_id / "reports" / run_id / "ingestion-tool-events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {"tool": tool_name, **result}
    path.open("a", encoding="utf-8").write(json.dumps(event, sort_keys=True) + "\n")
