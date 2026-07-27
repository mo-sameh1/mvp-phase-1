from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from agents.archimate_metamodel import explain_rule, list_relationship_types
from agents.assembly.reports import report_pair_paths, write_report_pair
from agents.schema import ModelElement


class ValidationViolation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: str = "error"
    code: str
    path: str
    element_id: str | None = None
    message: str
    citation: Any | None = None


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system_id: str
    run_id: str
    status: str
    counts_by_layer: dict[str, int] = Field(default_factory=dict)
    total_elements: int
    total_relationships: int
    violations: list[ValidationViolation] = Field(default_factory=list)
    report_paths: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            "# Validation Report",
            "",
            f"- System ID: `{self.system_id}`",
            f"- Run ID: `{self.run_id}`",
            f"- Status: `{self.status}`",
            f"- Elements: `{self.total_elements}`",
            f"- Relationships: `{self.total_relationships}`",
            "",
            "## Counts By Layer",
            "",
        ]
        for layer, count in self.counts_by_layer.items():
            lines.append(f"- `{layer}`: {count}")
        lines.extend(["", "## Violations", ""])
        if not self.violations:
            lines.append("- None")
        for violation in self.violations:
            target = f" `{violation.element_id}`" if violation.element_id else ""
            lines.append(f"- `{violation.code}`{target} in `{violation.path}`: {violation.message}")
        return "\n".join(lines)


def validate_reconciled_model(
    systems_root: Path,
    system_id: str,
    run_id: str,
) -> ValidationReport:
    payloads, violations = _scan_payloads(systems_root, system_id)
    elements, schema_violations = _validate_payloads(payloads)
    violations.extend(schema_violations)
    violations.extend(_duplicate_id_violations(elements))
    violations.extend(_relationship_violations(elements))

    counts = _counts_by_layer([element for _, element in elements])
    report = ValidationReport(
        system_id=system_id,
        run_id=run_id,
        status="passed" if not violations else "failed",
        counts_by_layer=counts,
        total_elements=len(elements),
        total_relationships=sum(len(element.relationships) for _, element in elements),
        violations=violations,
    )
    paths = report_pair_paths(systems_root, system_id, run_id, "validation-report")
    report = report.model_copy(update={"report_paths": [str(path) for path in paths]})
    write_validation_reports(systems_root, system_id, run_id, report)
    return report


def write_validation_reports(
    systems_root: Path,
    system_id: str,
    run_id: str,
    report: ValidationReport,
) -> list[Path]:
    return write_report_pair(
        systems_root=systems_root,
        system_id=system_id,
        run_id=run_id,
        stem="validation-report",
        report=report,
    )


def _scan_payloads(
    systems_root: Path,
    system_id: str,
) -> tuple[list[tuple[Path, dict[str, Any]]], list[ValidationViolation]]:
    system_root = systems_root / system_id / "as-is"
    payloads: list[tuple[Path, dict[str, Any]]] = []
    violations: list[ValidationViolation] = []
    for path in sorted(system_root.glob("*/*.json")) if system_root.exists() else []:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            violations.append(
                ValidationViolation(
                    code="malformed_json",
                    path=str(path),
                    message=f"Invalid JSON: {exc}",
                )
            )
            continue
        if not isinstance(payload, dict):
            violations.append(
                ValidationViolation(
                    code="schema_error",
                    path=str(path),
                    message="Model element JSON must be an object.",
                )
            )
            continue
        violations.extend(_raw_payload_violations(path, payload))
        payloads.append((path, payload))
    return payloads, violations


def _raw_payload_violations(path: Path, payload: dict[str, Any]) -> list[ValidationViolation]:
    violations: list[ValidationViolation] = []
    element_id = payload.get("id") if isinstance(payload.get("id"), str) else None
    evidence = payload.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        violations.append(
            ValidationViolation(
                code="missing_evidence",
                path=str(path),
                element_id=element_id,
                message="Element must include at least one evidence citation.",
            )
        )

    layer = payload.get("layer")
    archimate_type = payload.get("archimate_type")
    if isinstance(layer, str) and isinstance(archimate_type, str):
        rule = explain_rule(layer=layer, archimate_type=archimate_type)
        if not rule["valid"]:
            violations.append(
                ValidationViolation(
                    code="invalid_archimate_type",
                    path=str(path),
                    element_id=element_id,
                    message=rule["reason"],
                    citation=rule.get("citation"),
                )
            )

    valid_relationship_types = set(list_relationship_types())
    relationships = payload.get("relationships", [])
    if isinstance(relationships, list):
        for index, relationship in enumerate(relationships):
            if not isinstance(relationship, dict):
                continue
            relationship_type = relationship.get("type")
            if (
                isinstance(relationship_type, str)
                and relationship_type not in valid_relationship_types
            ):
                violations.append(
                    ValidationViolation(
                        code="invalid_relationship_type",
                        path=str(path),
                        element_id=element_id,
                        message=(
                            f"Relationship at index {index} uses unknown ArchiMate type "
                            f"'{relationship_type}'."
                        ),
                    )
                )
    return violations


def _validate_payloads(
    payloads: list[tuple[Path, dict[str, Any]]],
) -> tuple[list[tuple[Path, ModelElement]], list[ValidationViolation]]:
    elements: list[tuple[Path, ModelElement]] = []
    violations: list[ValidationViolation] = []
    for path, payload in payloads:
        try:
            elements.append((path, ModelElement(**payload)))
        except ValidationError as exc:
            element_id = payload.get("id") if isinstance(payload.get("id"), str) else None
            violations.append(
                ValidationViolation(
                    code="schema_error",
                    path=str(path),
                    element_id=element_id,
                    message=_validation_error_message(exc),
                )
            )
    return elements, violations


def _duplicate_id_violations(
    elements: list[tuple[Path, ModelElement]],
) -> list[ValidationViolation]:
    paths_by_id: dict[str, list[Path]] = {}
    for path, element in elements:
        paths_by_id.setdefault(element.id, []).append(path)
    violations: list[ValidationViolation] = []
    for element_id, paths in sorted(paths_by_id.items()):
        if len(paths) < 2:
            continue
        for path in paths:
            violations.append(
                ValidationViolation(
                    code="duplicate_id",
                    path=str(path),
                    element_id=element_id,
                    message=f"Duplicate model element id '{element_id}'.",
                )
            )
    return violations


def _relationship_violations(
    elements: list[tuple[Path, ModelElement]],
) -> list[ValidationViolation]:
    element_by_id = {element.id: element for _, element in elements}
    violations: list[ValidationViolation] = []
    for path, source in elements:
        for relationship in source.relationships:
            target = element_by_id.get(relationship.target_id)
            if target is None:
                violations.append(
                    ValidationViolation(
                        code="missing_relationship_target",
                        path=str(path),
                        element_id=source.id,
                        message=(
                            f"Relationship target id '{relationship.target_id}' does not exist."
                        ),
                    )
                )
                continue
            rule = explain_rule(
                source_type=source.archimate_type,
                relationship_type=relationship.type,
                target_type=target.archimate_type,
            )
            if not rule["valid"]:
                violations.append(
                    ValidationViolation(
                        code="invalid_relationship_pair",
                        path=str(path),
                        element_id=source.id,
                        message=rule["reason"],
                        citation=rule.get("citation"),
                    )
                )
    return violations


def _validation_error_message(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(item) for item in error['loc'])}: {error['msg']}" for error in exc.errors()
    )


def _counts_by_layer(elements: list[ModelElement]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for element in elements:
        counts[element.layer] = counts.get(element.layer, 0) + 1
    return dict(sorted(counts.items()))
