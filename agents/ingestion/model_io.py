from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from agents.archimate_metamodel import explain_rule
from agents.schema import ModelElement, RelationshipRef


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    if not slug:
        raise ValueError("Cannot create a slug from an empty value")
    return slug


def model_relative_path(system_id: str, layer: str, element_id: str) -> Path:
    return Path(system_id) / "as-is" / layer / f"{element_id}.json"


def model_file_path(systems_root: Path, system_id: str, layer: str, element_id: str) -> Path:
    return systems_root / model_relative_path(system_id, layer, element_id)


def write_model_element(systems_root: Path, system_id: str, element: ModelElement) -> Path:
    path = model_file_path(systems_root, system_id, element.layer, element.id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(element.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def load_model_element(path: Path) -> ModelElement:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    try:
        return ModelElement(**payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid model element in {path}: {exc}") from exc


def load_model_elements(systems_root: Path, system_id: str) -> dict[str, ModelElement]:
    elements: dict[str, ModelElement] = {}
    system_root = systems_root / system_id / "as-is"
    if not system_root.exists():
        return elements
    for path in sorted(system_root.glob("*/*.json")):
        element = load_model_element(path)
        if element.id in elements:
            raise ValueError(f"Duplicate model element id '{element.id}' in {path}")
        elements[element.id] = element
    return elements


def validate_model_tree(systems_root: Path, system_id: str) -> dict[str, ModelElement]:
    return load_model_elements(systems_root, system_id)


@dataclass(frozen=True)
class RelationshipDecision:
    written: bool
    source_id: str
    target_id: str
    relationship_type: str
    reason: str
    citation: Any | None = None


def append_relationship(
    *,
    systems_root: Path,
    system_id: str,
    source_id: str,
    relationship: RelationshipRef,
) -> RelationshipDecision:
    elements = load_model_elements(systems_root, system_id)
    if source_id not in elements:
        raise ValueError(f"Relationship source id '{source_id}' does not exist")
    if relationship.target_id not in elements:
        raise ValueError(f"Relationship target id '{relationship.target_id}' does not exist")

    source = elements[source_id]
    target = elements[relationship.target_id]
    rule = explain_rule(
        source_type=source.archimate_type,
        relationship_type=relationship.type,
        target_type=target.archimate_type,
    )
    if not rule["valid"]:
        return RelationshipDecision(
            written=False,
            source_id=source_id,
            target_id=relationship.target_id,
            relationship_type=relationship.type,
            reason=rule["reason"],
            citation=rule.get("citation"),
        )

    if _relationship_exists(source, relationship):
        return RelationshipDecision(
            written=False,
            source_id=source_id,
            target_id=relationship.target_id,
            relationship_type=relationship.type,
            reason="Relationship already exists",
            citation=rule.get("citation"),
        )

    updated = source.model_copy(update={"relationships": [*source.relationships, relationship]})
    write_model_element(systems_root, system_id, updated)
    return RelationshipDecision(
        written=True,
        source_id=source_id,
        target_id=relationship.target_id,
        relationship_type=relationship.type,
        reason="Relationship written",
        citation=rule.get("citation"),
    )


def _relationship_exists(source: ModelElement, relationship: RelationshipRef) -> bool:
    return any(
        existing.target_id == relationship.target_id and existing.type == relationship.type
        for existing in source.relationships
    )
