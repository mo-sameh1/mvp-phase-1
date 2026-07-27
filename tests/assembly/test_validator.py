import json
from pathlib import Path

from agents.assembly.validator import validate_reconciled_model
from agents.ingestion.model_io import write_model_element
from agents.schema import EvidenceCitation, ModelElement, RelationshipRef


def test_validator_passes_valid_reconciled_model_and_writes_reports(tmp_path: Path) -> None:
    _write_valid_business_pair(tmp_path)

    report = validate_reconciled_model(tmp_path, "demo", "run-1")

    assert report.status == "passed"
    assert report.violations == []
    assert report.counts_by_layer == {"business": 2}
    assert len(report.report_paths) == 2
    assert (tmp_path / "demo/reports/run-1/validation-report.json").exists()
    assert (tmp_path / "demo/reports/run-1/validation-report.md").exists()


def test_validator_reports_invalid_archimate_type(tmp_path: Path) -> None:
    _write_raw(
        tmp_path / "demo/as-is/business/bad-type.json",
        {
            "id": "bad-type",
            "layer": "business",
            "archimate_type": "Application Component",
            "name": "Bad Type",
            "documentation": "Wrong type.",
            "confidence": "observed",
            "evidence": [_evidence("Wrong type.").model_dump()],
            "relationships": [],
        },
    )

    report = validate_reconciled_model(tmp_path, "demo", "run-1")

    assert report.status == "failed"
    assert _codes(report) >= {"invalid_archimate_type", "schema_error"}


def test_validator_reports_illegal_relationship_pair(tmp_path: Path) -> None:
    source = ModelElement(
        id="case-api",
        layer="application",
        archimate_type="Application Interface",
        name="Case API",
        documentation="API fixture.",
        confidence="observed",
        evidence=[_evidence("API fixture.")],
        relationships=[
            RelationshipRef(
                target_id="case-service",
                type="Flow",
                evidence=[_evidence("API forwards requests.")],
            )
        ],
    )
    target = ModelElement(
        id="case-service",
        layer="application",
        archimate_type="Application Service",
        name="Case Service",
        documentation="Service fixture.",
        confidence="observed",
        evidence=[_evidence("Service fixture.")],
        relationships=[],
    )
    write_model_element(tmp_path, "demo", source)
    write_model_element(tmp_path, "demo", target)

    report = validate_reconciled_model(tmp_path, "demo", "run-1")

    assert report.status == "failed"
    assert "invalid_relationship_pair" in _codes(report)


def test_validator_reports_missing_relationship_target(tmp_path: Path) -> None:
    source = ModelElement(
        id="case-service",
        layer="application",
        archimate_type="Application Service",
        name="Case Service",
        documentation="Service fixture.",
        confidence="observed",
        evidence=[_evidence("Service fixture.")],
        relationships=[
            RelationshipRef(
                target_id="missing-process",
                type="Serving",
                evidence=[_evidence("Missing target fixture.")],
            )
        ],
    )
    write_model_element(tmp_path, "demo", source)

    report = validate_reconciled_model(tmp_path, "demo", "run-1")

    assert report.status == "failed"
    assert "missing_relationship_target" in _codes(report)


def test_validator_reports_missing_evidence_and_malformed_json(tmp_path: Path) -> None:
    _write_raw(
        tmp_path / "demo/as-is/business/no-evidence.json",
        {
            "id": "no-evidence",
            "layer": "business",
            "archimate_type": "Business Process",
            "name": "No Evidence",
            "documentation": "Missing evidence.",
            "confidence": "observed",
            "evidence": [],
            "relationships": [],
        },
    )
    malformed = tmp_path / "demo/as-is/business/malformed.json"
    malformed.parent.mkdir(parents=True, exist_ok=True)
    malformed.write_text("{not-json", encoding="utf-8")

    report = validate_reconciled_model(tmp_path, "demo", "run-1")

    assert report.status == "failed"
    assert _codes(report) >= {"missing_evidence", "malformed_json", "schema_error"}


def test_validator_reports_duplicate_ids(tmp_path: Path) -> None:
    payload = _business_role_payload("duplicate-role")
    _write_raw(tmp_path / "demo/as-is/business/duplicate-role.json", payload)
    _write_raw(tmp_path / "demo/as-is/business/duplicate-role-copy.json", payload)

    report = validate_reconciled_model(tmp_path, "demo", "run-1")

    assert report.status == "failed"
    assert "duplicate_id" in _codes(report)


def _write_valid_business_pair(tmp_path: Path) -> None:
    process = ModelElement(
        id="permit-review-process",
        layer="business",
        archimate_type="Business Process",
        name="Permit Review Process",
        documentation="Review process.",
        confidence="observed",
        evidence=[_evidence("Review process.")],
        relationships=[],
    )
    role = ModelElement(
        id="citizen-applicant",
        layer="business",
        archimate_type="Business Role",
        name="Citizen Applicant",
        documentation="Applicant role.",
        confidence="observed",
        evidence=[_evidence("Applicant role.")],
        relationships=[
            RelationshipRef(
                target_id=process.id,
                type="Assignment",
                evidence=[_evidence("Applicant performs review process.")],
            )
        ],
    )
    write_model_element(tmp_path, "demo", process)
    write_model_element(tmp_path, "demo", role)


def _business_role_payload(element_id: str) -> dict:
    return {
        "id": element_id,
        "layer": "business",
        "archimate_type": "Business Role",
        "name": "Duplicate Role",
        "documentation": "Duplicate role.",
        "confidence": "observed",
        "evidence": [_evidence("Duplicate role.").model_dump()],
        "relationships": [],
    }


def _write_raw(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _evidence(excerpt: str) -> EvidenceCitation:
    return EvidenceCitation(
        source_type="fixture",
        locator="/evidence/example.md:1",
        excerpt=excerpt,
    )


def _codes(report) -> set[str]:
    return {violation.code for violation in report.violations}
