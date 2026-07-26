import pytest
from pydantic import ValidationError

from agents.schema import EvidenceCitation, ModelElement, RelationshipRef


def evidence() -> EvidenceCitation:
    return EvidenceCitation(
        source_type="code",
        locator="src/payment.py:10-20",
        excerpt="class PaymentService",
    )


def valid_element(**overrides):
    payload = {
        "id": "payment-service",
        "layer": "application",
        "archimate_type": "Application Component",
        "name": "Payment Service",
        "documentation": "Handles payment orchestration.",
        "confidence": "observed",
        "evidence": [evidence()],
        "relationships": [],
    }
    payload.update(overrides)
    return ModelElement(**payload)


def test_valid_model_element_passes():
    element = valid_element()

    assert element.id == "payment-service"
    assert element.archimate_type == "Application Component"


def test_empty_evidence_fails():
    with pytest.raises(ValidationError):
        valid_element(evidence=[])


def test_invalid_archimate_type_for_layer_fails():
    with pytest.raises(ValidationError, match="not valid for layer"):
        valid_element(layer="business", archimate_type="Application Component")


def test_invalid_slug_id_fails():
    with pytest.raises(ValidationError):
        valid_element(id="Payment Service")


def test_invalid_relationship_type_fails():
    with pytest.raises(ValidationError, match="Unknown ArchiMate relationship type"):
        RelationshipRef(
            target_id="business-process",
            type="Depends On",
            evidence=[evidence()],
        )


def test_relationship_without_evidence_fails():
    with pytest.raises(ValidationError):
        RelationshipRef(
            target_id="business-process",
            type="Serving",
            evidence=[],
        )


def test_extra_fields_are_rejected():
    with pytest.raises(ValidationError):
        valid_element(unexpected="value")
