from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from pydantic import ValidationError

from agents.ingestion.model_io import append_relationship, write_model_element
from agents.schema import ModelElement, RelationshipRef


def validate_model_element_payload(payload: dict[str, Any]) -> ModelElement:
    """Validate an LLM-proposed element before it is allowed onto disk."""
    return ModelElement(**payload)


@tool
def write_model_element_tool(
    systems_root: str,
    system_id: str,
    element: dict[str, Any],
) -> dict[str, Any]:
    """Validate and write one agents.schema.ModelElement JSON file."""
    try:
        validated = validate_model_element_payload(element)
        path = write_model_element(Path(systems_root), system_id, validated)
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
    systems_root: str,
    system_id: str,
    source_id: str,
    relationship: dict[str, Any],
) -> dict[str, Any]:
    """Validate and append one evidence-cited relationship to an existing model element."""
    try:
        validated = RelationshipRef(**relationship)
        decision = append_relationship(
            systems_root=Path(systems_root),
            system_id=system_id,
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
