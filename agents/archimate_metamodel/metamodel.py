from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

SKILL_DATA_DIR = Path(__file__).resolve().parents[1] / "skills" / "archimate-metamodel" / "data"


def normalize_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()
    return re.sub(r"\s+", " ", normalized)


def load_json(filename: str) -> dict[str, Any]:
    path = SKILL_DATA_DIR / filename
    with path.open(encoding="utf-8") as file:
        return json.load(file)


@dataclass(frozen=True)
class ArchiMateMetamodel:
    elements: dict[str, Any]
    relationships: dict[str, Any]
    sources: dict[str, Any]

    @classmethod
    def load(cls) -> ArchiMateMetamodel:
        return cls(
            elements=load_json("elements.json"),
            relationships=load_json("relationships.json"),
            sources=load_json("sources.json"),
        )

    def list_element_types(self, layer: str) -> list[str]:
        layer_data = self._layer_data(layer)
        if layer_data is None:
            return []
        return [element["name"] for element in layer_data["elements"]]

    def list_relationship_types(self) -> list[str]:
        return [relationship["name"] for relationship in self.relationships["relationship_types"]]

    def is_valid_element_type(self, layer: str, archimate_type: str) -> bool:
        return self.explain_element_rule(layer, archimate_type)["valid"]

    def is_valid_relationship(
        self, source_type: str, relationship_type: str, target_type: str
    ) -> bool:
        return self.explain_relationship_rule(source_type, relationship_type, target_type)["valid"]

    def explain_element_rule(self, layer: str, archimate_type: str) -> dict[str, Any]:
        layer_key = normalize_name(layer)
        type_key = normalize_name(archimate_type)
        layer_data = self._layer_data(layer)

        if layer_data is None:
            return {
                "valid": False,
                "status": "invalid",
                "reason": f"Unknown ArchiMate layer: {layer}",
                "citation": None,
            }

        for element in layer_data["elements"]:
            if normalize_name(element["name"]) == type_key:
                return {
                    "valid": True,
                    "status": "valid",
                    "layer": layer_key,
                    "archimate_type": element["name"],
                    "summary": element["summary"],
                    "citation": layer_data["citation"],
                }

        actual_layer = self._layer_for_element(type_key)
        if actual_layer is not None:
            return {
                "valid": False,
                "status": "invalid",
                "reason": f"{archimate_type} belongs to layer '{actual_layer}', not '{layer_key}'",
                "citation": self.elements["layers"][actual_layer]["citation"],
            }

        return {
            "valid": False,
            "status": "invalid",
            "reason": f"Unknown ArchiMate element type: {archimate_type}",
            "citation": None,
        }

    def explain_relationship_rule(
        self, source_type: str, relationship_type: str, target_type: str
    ) -> dict[str, Any]:
        source_key = normalize_name(source_type)
        relationship_key = normalize_name(relationship_type)
        target_key = normalize_name(target_type)

        relationship = self._relationship_type(relationship_key)
        if relationship is None:
            return {
                "valid": False,
                "status": "invalid",
                "reason": f"Unknown ArchiMate relationship type: {relationship_type}",
                "citation": None,
            }

        source = self._element_by_name(source_key)
        if source is None:
            return {
                "valid": False,
                "status": "invalid",
                "reason": f"Unknown source element type: {source_type}",
                "citation": None,
            }

        target = self._element_by_name(target_key)
        if target is None:
            return {
                "valid": False,
                "status": "invalid",
                "reason": f"Unknown target element type: {target_type}",
                "citation": None,
            }

        for rule in self.relationships["validation_rules"]:
            if normalize_name(rule["relationship_type"]) != relationship_key:
                continue
            if rule["mode"] == "same_element_type" and source_key == target_key:
                return {
                    "valid": True,
                    "status": "valid",
                    "relationship_type": relationship["name"],
                    "source_type": source["name"],
                    "target_type": target["name"],
                    "rule_id": rule["id"],
                    "citation": rule["citation"],
                }
            if (
                rule["mode"] == "explicit_pair"
                and normalize_name(rule["source_type"]) == source_key
                and normalize_name(rule["target_type"]) == target_key
            ):
                return {
                    "valid": True,
                    "status": "valid",
                    "relationship_type": relationship["name"],
                    "source_type": source["name"],
                    "target_type": target["name"],
                    "rule_id": rule["id"],
                    "citation": rule["citation"],
                }

        candidate = self._candidate_relationship(source_key, relationship_key, target_key)
        if candidate is not None:
            return {
                "valid": False,
                "status": "needs_review",
                "relationship_type": relationship["name"],
                "source_type": source["name"],
                "target_type": target["name"],
                "reason": "Candidate example is not approved against official Appendix B.",
                "citation": candidate["citation"],
            }

        return {
            "valid": False,
            "status": "unknown",
            "relationship_type": relationship["name"],
            "source_type": source["name"],
            "target_type": target["name"],
            "reason": "Relationship pair is not established by the ArchiMate metamodel skill.",
            "citation": self.sources["sections"]["normative_relationships"],
        }

    def explain_rule(
        self,
        *,
        layer: str | None = None,
        archimate_type: str | None = None,
        source_type: str | None = None,
        relationship_type: str | None = None,
        target_type: str | None = None,
    ) -> dict[str, Any]:
        if layer is not None and archimate_type is not None:
            return self.explain_element_rule(layer, archimate_type)
        if source_type is not None and relationship_type is not None and target_type is not None:
            return self.explain_relationship_rule(source_type, relationship_type, target_type)
        raise ValueError(
            "Provide either layer + archimate_type, "
            "or source_type + relationship_type + target_type."
        )

    def _layer_data(self, layer: str) -> dict[str, Any] | None:
        return self.elements["layers"].get(normalize_name(layer))

    def _layer_for_element(self, normalized_type: str) -> str | None:
        for layer, layer_data in self.elements["layers"].items():
            for element in layer_data["elements"]:
                if normalize_name(element["name"]) == normalized_type:
                    return layer
        return None

    def _element_by_name(self, normalized_type: str) -> dict[str, Any] | None:
        layer = self._layer_for_element(normalized_type)
        if layer is None:
            return None
        for element in self.elements["layers"][layer]["elements"]:
            if normalize_name(element["name"]) == normalized_type:
                return element
        return None

    def _relationship_type(self, normalized_type: str) -> dict[str, Any] | None:
        for relationship in self.relationships["relationship_types"]:
            if normalize_name(relationship["name"]) == normalized_type:
                return relationship
        return None

    def _candidate_relationship(
        self, source_key: str, relationship_key: str, target_key: str
    ) -> dict[str, Any] | None:
        for candidate in self.relationships["candidate_examples"]:
            if (
                normalize_name(candidate["source_type"]) == source_key
                and normalize_name(candidate["relationship_type"]) == relationship_key
                and normalize_name(candidate["target_type"]) == target_key
            ):
                return candidate
        return None


@lru_cache
def get_default_metamodel() -> ArchiMateMetamodel:
    return ArchiMateMetamodel.load()


def list_element_types(layer: str) -> list[str]:
    return get_default_metamodel().list_element_types(layer)


def list_relationship_types() -> list[str]:
    return get_default_metamodel().list_relationship_types()


def is_valid_element_type(layer: str, archimate_type: str) -> bool:
    return get_default_metamodel().is_valid_element_type(layer, archimate_type)


def is_valid_relationship(source_type: str, relationship_type: str, target_type: str) -> bool:
    return get_default_metamodel().is_valid_relationship(
        source_type, relationship_type, target_type
    )


def explain_rule(
    *,
    layer: str | None = None,
    archimate_type: str | None = None,
    source_type: str | None = None,
    relationship_type: str | None = None,
    target_type: str | None = None,
) -> dict[str, Any]:
    return get_default_metamodel().explain_rule(
        layer=layer,
        archimate_type=archimate_type,
        source_type=source_type,
        relationship_type=relationship_type,
        target_type=target_type,
    )
