from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from agents.ingestion.model_io import (
    RelationshipDecision,
    append_relationship,
    load_model_elements,
    write_model_element,
)
from agents.ingestion.profiles import INGESTION_SUBAGENT_NAMES
from agents.schema import EvidenceCitation, ModelElement, RelationshipRef


@dataclass(frozen=True)
class FixtureRunResult:
    system_id: str
    systems_root: Path
    repeat_index: int
    element_count: int
    element_counts_by_layer: dict[str, int]
    relationship_decisions: list[RelationshipDecision]


def run_fixture_ingestion(
    *,
    fixture_root: Path,
    systems_root: Path,
    system_id: str,
    repeat_index: int = 1,
) -> FixtureRunResult:
    _reset_system_tree(systems_root, system_id)
    for subagent_name in INGESTION_SUBAGENT_NAMES:
        if subagent_name == "integration-mapper":
            decisions = _run_integration_mapper(
                fixture_root=fixture_root,
                systems_root=systems_root,
                system_id=system_id,
            )
            break
        _write_expected_elements(
            fixture_root=fixture_root,
            systems_root=systems_root,
            system_id=system_id,
            subagent_name=subagent_name,
        )
    else:
        decisions = []

    elements = load_model_elements(systems_root, system_id)
    counts_by_layer: dict[str, int] = {}
    for element in elements.values():
        counts_by_layer[element.layer] = counts_by_layer.get(element.layer, 0) + 1

    return FixtureRunResult(
        system_id=system_id,
        systems_root=systems_root,
        repeat_index=repeat_index,
        element_count=len(elements),
        element_counts_by_layer=dict(sorted(counts_by_layer.items())),
        relationship_decisions=decisions,
    )


def compare_repeated_counts(results: list[FixtureRunResult], *, tolerance: int = 1) -> None:
    if not results:
        raise ValueError("No Epic E fixture run results to compare")
    baseline = results[0].element_count
    for result in results[1:]:
        if abs(result.element_count - baseline) > tolerance:
            raise ValueError(
                "Epic E reproducibility check failed: "
                f"run 1 produced {baseline} elements, run {result.repeat_index} produced "
                f"{result.element_count}"
            )


def _write_expected_elements(
    *,
    fixture_root: Path,
    systems_root: Path,
    system_id: str,
    subagent_name: str,
) -> None:
    source_dir = fixture_root / "expected-model" / subagent_name
    if not source_dir.exists():
        raise ValueError(f"Missing fixture expected-model directory: {source_dir}")
    for path in sorted(source_dir.glob("*.json")):
        element = ModelElement(**json.loads(path.read_text(encoding="utf-8")))
        write_model_element(systems_root, system_id, element)


def _run_integration_mapper(
    *,
    fixture_root: Path,
    systems_root: Path,
    system_id: str,
) -> list[RelationshipDecision]:
    path = fixture_root / "expected-model" / "integration-mapper" / "relationships.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    decisions: list[RelationshipDecision] = []
    for candidate in payload["relationships"]:
        relationship = RelationshipRef(
            target_id=candidate["target_id"],
            type=candidate["type"],
            evidence=[EvidenceCitation(**item) for item in candidate["evidence"]],
        )
        decisions.append(
            append_relationship(
                systems_root=systems_root,
                system_id=system_id,
                source_id=candidate["source_id"],
                relationship=relationship,
            )
        )
    return decisions


def _reset_system_tree(systems_root: Path, system_id: str) -> None:
    system_root = systems_root / system_id
    if system_root.exists():
        shutil.rmtree(system_root)
