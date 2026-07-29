from __future__ import annotations

from pathlib import Path

import pytest

from agents.ingestion.model_io import load_model_elements, write_model_element
from agents.ingestion.tools import append_model_relationship_tool, write_model_element_tool
from agents.schema import EvidenceCitation, ModelElement


def test_write_model_element_tool_validates_and_writes_json(tmp_path: Path) -> None:
    systems_root = tmp_path / "systems"
    result = write_model_element_tool.invoke(
        {
            "systems_root": str(systems_root),
            "system_id": "demo",
            "run_id": "run-1",
            "element": _element_payload(
                element_id="case-handling-service",
                layer="application",
                archimate_type="Application Service",
            ),
        }
    )

    assert result["status"] == "written"
    assert result["written"] is True
    elements = load_model_elements(systems_root, "demo")
    assert elements["case-handling-service"].archimate_type == "Application Service"
    assert "write_model_element_tool" in _event_log(systems_root)


def test_write_model_element_tool_canonicalizes_snake_case_id(tmp_path: Path) -> None:
    systems_root = tmp_path / "systems"
    result = write_model_element_tool.invoke(
        {
            "systems_root": str(systems_root),
            "system_id": "demo",
            "run_id": "run-1",
            "element": _element_payload(
                element_id="case_handling_service",
                layer="application",
                archimate_type="Application Service",
            ),
        }
    )

    assert result["status"] == "written"
    assert result["id"] == "case-handling-service"
    assert "case-handling-service" in load_model_elements(systems_root, "demo")


def test_write_model_element_tool_canonicalizes_compact_archimate_type(tmp_path: Path) -> None:
    systems_root = tmp_path / "systems"
    result = write_model_element_tool.invoke(
        {
            "systems_root": str(systems_root),
            "system_id": "demo",
            "run_id": "run-1",
            "element": _element_payload(
                element_id="online-service-channel",
                layer="strategy",
                archimate_type="CourseOfAction",
            ),
        }
    )

    assert result["status"] == "written"
    assert result["archimate_type"] == "Course of Action"
    assert (
        load_model_elements(systems_root, "demo")["online-service-channel"].archimate_type
        == "Course of Action"
    )


def test_write_model_element_tool_rejects_invalid_model_payload(tmp_path: Path) -> None:
    systems_root = tmp_path / "systems"
    with pytest.raises(ValueError, match="Ingestion tool rejected candidate"):
        write_model_element_tool.invoke(
            {
                "systems_root": str(systems_root),
                "system_id": "demo",
                "run_id": "run-1",
                "element": _element_payload(
                    element_id="bad",
                    layer="business",
                    archimate_type="Application Component",
                ),
            }
        )

    assert load_model_elements(systems_root, "demo") == {}
    assert '"status": "rejected"' in _event_log(systems_root)
    assert "not valid for layer" in _event_log(systems_root)


def test_write_model_element_tool_rejects_inline_relationships(tmp_path: Path) -> None:
    systems_root = tmp_path / "systems"
    payload = _element_payload(
        element_id="citizen-applicant",
        layer="business",
        archimate_type="Business Role",
    )
    payload["relationships"] = [
        {
            "target_id": "permit-application-process",
            "type": "Assignment",
            "evidence": [_evidence("Applicant starts the request.")],
        }
    ]

    with pytest.raises(ValueError, match="relationships to \\[\\]"):
        write_model_element_tool.invoke(
            {
                "systems_root": str(systems_root),
                "system_id": "demo",
                "run_id": "run-1",
                "element": payload,
            }
        )

    assert load_model_elements(systems_root, "demo") == {}


def test_write_model_element_tool_rejects_unsafe_systems_root() -> None:
    with pytest.raises(ValueError, match="systems directory"):
        write_model_element_tool.invoke(
            {
                "systems_root": "/",
                "system_id": "demo",
                "run_id": "run-1",
                "element": _element_payload(
                    element_id="citizen-applicant",
                    layer="business",
                    archimate_type="Business Role",
                ),
            }
        )


def test_append_model_relationship_tool_writes_valid_relationship(tmp_path: Path) -> None:
    systems_root = tmp_path / "systems"
    source = _element(
        element_id="citizen-applicant",
        layer="business",
        archimate_type="Business Role",
    )
    target = _element(
        element_id="permit-review-process",
        layer="business",
        archimate_type="Business Process",
    )
    write_model_element(systems_root, "demo", source)
    write_model_element(systems_root, "demo", target)

    result = append_model_relationship_tool.invoke(
        {
            "systems_root": str(systems_root),
            "system_id": "demo",
            "run_id": "run-1",
            "source_id": source.id,
            "relationship": {
                "target_id": target.id,
                "type": "Assignment",
                "evidence": [_evidence("Applicant performs the review process.")],
            },
        }
    )

    assert result["status"] == "written"
    assert result["written"] is True
    assert (
        load_model_elements(systems_root, "demo")[source.id].relationships[0].target_id == target.id
    )


def test_append_model_relationship_tool_rejects_missing_target(tmp_path: Path) -> None:
    systems_root = tmp_path / "systems"
    source = _element(
        element_id="case-handling-service",
        layer="application",
        archimate_type="Application Service",
    )
    write_model_element(systems_root, "demo", source)

    with pytest.raises(ValueError, match="missing-process"):
        append_model_relationship_tool.invoke(
            {
                "systems_root": str(systems_root),
                "system_id": "demo",
                "run_id": "run-1",
                "source_id": source.id,
                "relationship": {
                    "target_id": "missing-process",
                    "type": "Serving",
                    "evidence": [_evidence()],
                },
            }
        )

    assert "missing-process" in _event_log(systems_root)


def test_append_model_relationship_tool_skips_unsupported_pair(tmp_path: Path) -> None:
    systems_root = tmp_path / "systems"
    source = _element(
        element_id="case-api",
        layer="application",
        archimate_type="Application Interface",
    )
    target = _element(
        element_id="case-handling-service",
        layer="application",
        archimate_type="Application Service",
    )
    write_model_element(systems_root, "demo", source)
    write_model_element(systems_root, "demo", target)

    result = append_model_relationship_tool.invoke(
        {
            "systems_root": str(systems_root),
            "system_id": "demo",
            "run_id": "run-1",
            "source_id": source.id,
            "relationship": {
                "target_id": target.id,
                "type": "Flow",
                "evidence": [_evidence("The API sends case data to the service.")],
            },
        }
    )

    assert result["status"] == "skipped"
    assert result["written"] is False
    assert "not established" in result["reason"]
    assert '"status": "skipped"' in _event_log(systems_root)


def _element_payload(*, element_id: str, layer: str, archimate_type: str) -> dict:
    return {
        "id": element_id,
        "layer": layer,
        "archimate_type": archimate_type,
        "name": element_id.replace("-", " ").title(),
        "documentation": "Evidence-grounded fixture element.",
        "confidence": "observed",
        "evidence": [_evidence()],
        "relationships": [],
    }


def _element(*, element_id: str, layer: str, archimate_type: str) -> ModelElement:
    return ModelElement(
        **_element_payload(element_id=element_id, layer=layer, archimate_type=archimate_type)
    )


def _evidence(excerpt: str = "Evidence excerpt.") -> dict:
    return EvidenceCitation(
        source_type="fixture",
        locator="/evidence/example.md:1",
        excerpt=excerpt,
    ).model_dump()


def _event_log(systems_root: Path) -> str:
    return (systems_root / "demo" / "reports" / "run-1" / "ingestion-tool-events.jsonl").read_text(
        encoding="utf-8"
    )
