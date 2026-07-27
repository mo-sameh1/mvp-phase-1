from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from agents.assembly.reports import report_pair_paths, write_report_pair
from agents.ingestion.model_io import load_model_element, model_file_path, write_model_element
from agents.schema import EvidenceCitation, ModelElement, RelationshipRef

AMBIGUOUS_MATCH_THRESHOLD = 0.82


class MergeDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical_id: str
    merged_ids: list[str]
    layer: str
    archimate_type: str
    normalized_name: str
    evidence_count: int


class AmbiguousConflict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    left_id: str
    right_id: str
    layer: str
    archimate_type: str
    left_name: str
    right_name: str
    similarity: float
    reason: str


class ReconciliationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system_id: str
    run_id: str
    status: str
    counts_before_by_layer: dict[str, int] = Field(default_factory=dict)
    counts_after_by_layer: dict[str, int] = Field(default_factory=dict)
    total_elements_before: int
    total_elements_after: int
    merge_decisions: list[MergeDecision] = Field(default_factory=list)
    ambiguous_conflicts: list[AmbiguousConflict] = Field(default_factory=list)
    report_paths: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            "# Reconciliation Report",
            "",
            f"- System ID: `{self.system_id}`",
            f"- Run ID: `{self.run_id}`",
            f"- Status: `{self.status}`",
            f"- Elements before: `{self.total_elements_before}`",
            f"- Elements after: `{self.total_elements_after}`",
            "",
            "## Counts By Layer",
            "",
        ]
        for layer, count in self.counts_after_by_layer.items():
            lines.append(f"- `{layer}`: {count}")
        lines.extend(["", "## Merge Decisions", ""])
        if not self.merge_decisions:
            lines.append("- None")
        for decision in self.merge_decisions:
            merged = ", ".join(f"`{item}`" for item in decision.merged_ids)
            lines.append(
                f"- `{decision.canonical_id}` retained for {merged} "
                f"({decision.layer}, {decision.archimate_type})"
            )
        lines.extend(["", "## Ambiguous Conflicts", ""])
        if not self.ambiguous_conflicts:
            lines.append("- None")
        for conflict in self.ambiguous_conflicts:
            lines.append(
                f"- `{conflict.left_id}` vs `{conflict.right_id}`: "
                f"{conflict.similarity:.2f} similarity; {conflict.reason}"
            )
        return "\n".join(lines)


@dataclass(frozen=True)
class _ElementRecord:
    path: Path
    element: ModelElement


def normalize_reconciliation_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def reconcile_model_tree(
    systems_root: Path,
    system_id: str,
    run_id: str,
) -> ReconciliationReport:
    records = _load_records(systems_root, system_id)
    counts_before = _counts_by_layer([record.element for record in records])
    alias_map, merge_decisions = _merge_duplicate_groups(systems_root, system_id, records)

    current_records = _load_records(systems_root, system_id)
    rewritten = [
        _rewrite_relationship_targets(record.element, alias_map) for record in current_records
    ]
    for element in rewritten:
        write_model_element(systems_root, system_id, element)

    final_records = _load_records(systems_root, system_id)
    counts_after = _counts_by_layer([record.element for record in final_records])
    report = ReconciliationReport(
        system_id=system_id,
        run_id=run_id,
        status="completed",
        counts_before_by_layer=counts_before,
        counts_after_by_layer=counts_after,
        total_elements_before=len(records),
        total_elements_after=len(final_records),
        merge_decisions=merge_decisions,
        ambiguous_conflicts=_find_ambiguous_conflicts([record.element for record in final_records]),
    )
    paths = report_pair_paths(systems_root, system_id, run_id, "reconciliation-report")
    report = report.model_copy(update={"report_paths": [str(path) for path in paths]})
    write_reconciliation_reports(systems_root, system_id, run_id, report)
    return report


def write_reconciliation_reports(
    systems_root: Path,
    system_id: str,
    run_id: str,
    report: ReconciliationReport,
) -> list[Path]:
    return write_report_pair(
        systems_root=systems_root,
        system_id=system_id,
        run_id=run_id,
        stem="reconciliation-report",
        report=report,
    )


def _load_records(systems_root: Path, system_id: str) -> list[_ElementRecord]:
    system_root = systems_root / system_id / "as-is"
    if not system_root.exists():
        return []
    return [
        _ElementRecord(path=path, element=load_model_element(path))
        for path in sorted(system_root.glob("*/*.json"))
    ]


def _merge_duplicate_groups(
    systems_root: Path,
    system_id: str,
    records: list[_ElementRecord],
) -> tuple[dict[str, str], list[MergeDecision]]:
    groups: dict[tuple[str, str, str], list[ModelElement]] = {}
    for record in records:
        element = record.element
        key = (
            element.layer,
            element.archimate_type,
            normalize_reconciliation_key(element.name),
        )
        groups.setdefault(key, []).append(element)

    alias_map: dict[str, str] = {}
    decisions: list[MergeDecision] = []
    for (layer, archimate_type, normalized_name), elements in sorted(groups.items()):
        if len(elements) < 2:
            continue
        canonical_id = min(element.id for element in elements)
        canonical = next(element for element in elements if element.id == canonical_id)
        merged_ids = sorted(element.id for element in elements)
        for element in elements:
            alias_map[element.id] = canonical_id
        merged = _merge_elements(canonical, sorted(elements, key=lambda item: item.id), alias_map)
        write_model_element(systems_root, system_id, merged)
        for element in elements:
            if element.id == canonical_id:
                continue
            path = model_file_path(systems_root, system_id, element.layer, element.id)
            path.unlink(missing_ok=True)
        decisions.append(
            MergeDecision(
                canonical_id=canonical_id,
                merged_ids=merged_ids,
                layer=layer,
                archimate_type=archimate_type,
                normalized_name=normalized_name,
                evidence_count=len(merged.evidence),
            )
        )
    return alias_map, decisions


def _merge_elements(
    canonical: ModelElement,
    elements: list[ModelElement],
    alias_map: dict[str, str],
) -> ModelElement:
    return canonical.model_copy(
        update={
            "documentation": _merge_documentation(canonical, elements),
            "evidence": _dedupe_evidence(
                evidence for element in elements for evidence in element.evidence
            ),
            "relationships": _merge_relationships(
                relationship
                for element in elements
                for relationship in element.relationships
                if alias_map.get(relationship.target_id, relationship.target_id) != canonical.id
            ),
        }
    )


def _merge_documentation(canonical: ModelElement, elements: list[ModelElement]) -> str:
    sections = [canonical.documentation]
    seen = {canonical.documentation}
    for element in elements:
        if element.id == canonical.id or element.documentation in seen:
            continue
        sections.append(f"Merged documentation from {element.id}:\n{element.documentation}")
        seen.add(element.documentation)
    return "\n\n".join(sections)


def _dedupe_evidence(items) -> list[EvidenceCitation]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[EvidenceCitation] = []
    for evidence in items:
        key = (evidence.source_type, evidence.locator, evidence.excerpt)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(evidence)
    return deduped


def _merge_relationships(items) -> list[RelationshipRef]:
    grouped: dict[tuple[str, str], list[EvidenceCitation]] = {}
    for relationship in items:
        key = (relationship.target_id, relationship.type)
        grouped.setdefault(key, [])
        grouped[key].extend(relationship.evidence)
    return [
        RelationshipRef(
            target_id=target_id,
            type=relationship_type,
            evidence=_dedupe_evidence(evidence_items),
        )
        for (target_id, relationship_type), evidence_items in sorted(grouped.items())
    ]


def _rewrite_relationship_targets(
    element: ModelElement,
    alias_map: dict[str, str],
) -> ModelElement:
    rewritten = [
        relationship.model_copy(
            update={"target_id": alias_map.get(relationship.target_id, relationship.target_id)}
        )
        for relationship in element.relationships
    ]
    return element.model_copy(update={"relationships": _merge_relationships(rewritten)})


def _find_ambiguous_conflicts(elements: list[ModelElement]) -> list[AmbiguousConflict]:
    conflicts: list[AmbiguousConflict] = []
    sorted_elements = sorted(elements, key=lambda item: item.id)
    for index, left in enumerate(sorted_elements):
        left_key = normalize_reconciliation_key(left.name)
        for right in sorted_elements[index + 1 :]:
            if left.layer != right.layer or left.archimate_type != right.archimate_type:
                continue
            right_key = normalize_reconciliation_key(right.name)
            if left_key == right_key:
                continue
            similarity = SequenceMatcher(None, left_key, right_key).ratio()
            if similarity >= AMBIGUOUS_MATCH_THRESHOLD:
                conflicts.append(
                    AmbiguousConflict(
                        left_id=left.id,
                        right_id=right.id,
                        layer=left.layer,
                        archimate_type=left.archimate_type,
                        left_name=left.name,
                        right_name=right.name,
                        similarity=round(similarity, 4),
                        reason="Near-match requires human review before merging.",
                    )
                )
    return conflicts


def _counts_by_layer(elements: list[ModelElement]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for element in elements:
        counts[element.layer] = counts.get(element.layer, 0) + 1
    return dict(sorted(counts.items()))
