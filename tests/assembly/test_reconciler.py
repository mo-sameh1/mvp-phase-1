from pathlib import Path

from agents.assembly.reconciler import normalize_reconciliation_key, reconcile_model_tree
from agents.ingestion.model_io import load_model_elements, model_file_path, write_model_element
from agents.schema import EvidenceCitation, ModelElement, RelationshipRef


def test_normalize_reconciliation_key_removes_case_whitespace_and_punctuation() -> None:
    assert normalize_reconciliation_key(" Payment-Service ") == "paymentservice"
    assert normalize_reconciliation_key("payment service") == "paymentservice"


def test_reconciler_merges_exact_normalized_duplicates_and_retains_evidence(
    tmp_path: Path,
) -> None:
    _write_payment_fixture(tmp_path)

    report = reconcile_model_tree(tmp_path, "demo", "run-1")
    elements = load_model_elements(tmp_path, "demo")

    assert report.total_elements_before == 4
    assert report.total_elements_after == 3
    assert report.merge_decisions[0].canonical_id == "payment-service"
    assert report.merge_decisions[0].merged_ids == ["payment-service", "paymentservice"]
    assert len(report.report_paths) == 2
    assert "paymentservice" not in elements
    assert not model_file_path(tmp_path, "demo", "application", "paymentservice").exists()

    merged = elements["payment-service"]
    assert len(merged.evidence) == 2
    assert "Merged documentation from paymentservice" in merged.documentation


def test_reconciler_rewrites_relationship_targets_to_canonical_id(tmp_path: Path) -> None:
    _write_payment_fixture(tmp_path)

    reconcile_model_tree(tmp_path, "demo", "run-1")

    component = load_model_elements(tmp_path, "demo")["payment-client"]
    assert len(component.relationships) == 1
    assert component.relationships[0].target_id == "payment-service"
    assert component.relationships[0].type == "Realization"


def test_reconciler_flags_ambiguous_near_matches_without_merging(tmp_path: Path) -> None:
    _write_payment_fixture(tmp_path)

    report = reconcile_model_tree(tmp_path, "demo", "run-1")
    elements = load_model_elements(tmp_path, "demo")

    assert "payment-services" in elements
    assert any(
        {conflict.left_id, conflict.right_id} == {"payment-service", "payment-services"}
        for conflict in report.ambiguous_conflicts
    )


def test_reconciler_ignores_elements_below_ambiguous_threshold(tmp_path: Path) -> None:
    write_model_element(
        tmp_path,
        "demo",
        _element("payment-service", "Application Service", "Payment Service"),
    )
    write_model_element(
        tmp_path,
        "demo",
        _element("invoice-service", "Application Service", "Invoice Service"),
    )

    report = reconcile_model_tree(tmp_path, "demo", "run-1")

    assert report.merge_decisions == []
    assert report.ambiguous_conflicts == []
    assert report.total_elements_after == 2


def _write_payment_fixture(systems_root: Path) -> None:
    write_model_element(
        systems_root,
        "demo",
        _element(
            "payment-service",
            "Application Service",
            "Payment Service",
            evidence_excerpt="Payment Service handles permit payment submissions.",
        ),
    )
    write_model_element(
        systems_root,
        "demo",
        _element(
            "paymentservice",
            "Application Service",
            "Payment-Service",
            documentation="Legacy spelling for the same payment service.",
            evidence_excerpt="PaymentService exposes the same payment submission behavior.",
        ),
    )
    write_model_element(
        systems_root,
        "demo",
        _element(
            "payment-services",
            "Application Service",
            "Payment Services",
            evidence_excerpt="Payment Services handles settlement support.",
        ),
    )
    write_model_element(
        systems_root,
        "demo",
        _element(
            "payment-client",
            "Application Component",
            "Payment Client",
            relationships=[
                RelationshipRef(
                    target_id="paymentservice",
                    type="Realization",
                    evidence=[_evidence("Payment Client realizes PaymentService.")],
                )
            ],
        ),
    )


def _element(
    element_id: str,
    archimate_type: str,
    name: str,
    *,
    documentation: str = "Fixture documentation.",
    evidence_excerpt: str = "Fixture evidence.",
    relationships: list[RelationshipRef] | None = None,
) -> ModelElement:
    return ModelElement(
        id=element_id,
        layer="application",
        archimate_type=archimate_type,
        name=name,
        documentation=documentation,
        confidence="observed",
        evidence=[_evidence(evidence_excerpt)],
        relationships=relationships or [],
    )


def _evidence(excerpt: str) -> EvidenceCitation:
    return EvidenceCitation(
        source_type="fixture",
        locator="/evidence/example.md:1",
        excerpt=excerpt,
    )
