import json
from pathlib import Path

import pytest

from agents.ingestion.model_io import (
    append_relationship,
    load_model_element,
    load_model_elements,
    model_file_path,
    model_relative_path,
    slugify,
    write_model_element,
)
from agents.schema import EvidenceCitation, ModelElement, RelationshipRef


def test_slugify_is_stable_and_rejects_empty_values() -> None:
    assert slugify("Case Management Service!") == "case-management-service"
    assert slugify("  CASE___Management   Service  ") == "case-management-service"

    with pytest.raises(ValueError, match="empty"):
        slugify("!!!")


def test_model_paths_resolve_to_expected_as_is_layer_layout(tmp_path: Path) -> None:
    assert model_relative_path("demo", "business", "permit-review") == Path(
        "demo/as-is/business/permit-review.json"
    )
    assert model_file_path(tmp_path, "demo", "business", "permit-review") == (
        tmp_path / "demo/as-is/business/permit-review.json"
    )


def test_write_and_load_model_element_round_trip(tmp_path: Path) -> None:
    element = _element(
        element_id="citizen-applicant",
        layer="business",
        archimate_type="Business Role",
    )

    path = write_model_element(tmp_path, "demo", element)

    assert path == tmp_path / "demo/as-is/business/citizen-applicant.json"
    assert load_model_element(path) == element
    assert load_model_elements(tmp_path, "demo") == {"citizen-applicant": element}


def test_load_model_element_fails_loudly_on_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON"):
        load_model_element(path)


def test_load_model_element_fails_loudly_on_invalid_schema(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "id": "bad",
                "layer": "business",
                "archimate_type": "Application Component",
                "name": "Bad",
                "documentation": "Wrong layer/type pair.",
                "confidence": "observed",
                "evidence": [_evidence().model_dump()],
                "relationships": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid model element"):
        load_model_element(path)


def test_append_relationship_writes_valid_rule_and_preserves_evidence(tmp_path: Path) -> None:
    source = _element(
        element_id="citizen-applicant",
        layer="business",
        archimate_type="Business Role",
        evidence_excerpt="The citizen applicant starts the request.",
    )
    target = _element(
        element_id="permit-review-process",
        layer="business",
        archimate_type="Business Process",
        evidence_excerpt="The permit review process checks the application.",
    )
    write_model_element(tmp_path, "demo", source)
    write_model_element(tmp_path, "demo", target)

    decision = append_relationship(
        systems_root=tmp_path,
        system_id="demo",
        source_id=source.id,
        relationship=RelationshipRef(
            target_id=target.id,
            type="Assignment",
            evidence=[_evidence("The citizen applicant performs the permit review process.")],
        ),
    )

    assert decision.written is True
    reloaded = load_model_elements(tmp_path, "demo")[source.id]
    assert reloaded.evidence == source.evidence
    assert len(reloaded.relationships) == 1
    assert reloaded.relationships[0].target_id == target.id


def test_append_relationship_rejects_missing_target_id(tmp_path: Path) -> None:
    source = _element(
        element_id="case-handling-service",
        layer="application",
        archimate_type="Application Service",
    )
    write_model_element(tmp_path, "demo", source)

    with pytest.raises(ValueError, match="does not exist"):
        append_relationship(
            systems_root=tmp_path,
            system_id="demo",
            source_id=source.id,
            relationship=RelationshipRef(
                target_id="missing-process",
                type="Serving",
                evidence=[_evidence()],
            ),
        )


def test_append_relationship_skips_unsupported_source_target_pair(tmp_path: Path) -> None:
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
    write_model_element(tmp_path, "demo", source)
    write_model_element(tmp_path, "demo", target)

    decision = append_relationship(
        systems_root=tmp_path,
        system_id="demo",
        source_id=source.id,
        relationship=RelationshipRef(
            target_id=target.id,
            type="Flow",
            evidence=[_evidence("The API forwards requests to the service.")],
        ),
    )

    assert decision.written is False
    assert "not established" in decision.reason
    assert load_model_elements(tmp_path, "demo")[source.id].relationships == []


def _element(
    *,
    element_id: str,
    layer: str,
    archimate_type: str,
    evidence_excerpt: str = "Evidence excerpt.",
) -> ModelElement:
    return ModelElement(
        id=element_id,
        layer=layer,
        archimate_type=archimate_type,
        name=element_id.replace("-", " ").title(),
        documentation="Fixture element.",
        confidence="observed",
        evidence=[_evidence(evidence_excerpt)],
        relationships=[],
    )


def _evidence(excerpt: str = "Evidence excerpt.") -> EvidenceCitation:
    return EvidenceCitation(
        source_type="fixture",
        locator="/evidence/example.md:1",
        excerpt=excerpt,
    )
