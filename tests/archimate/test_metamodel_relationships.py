from agents.archimate_metamodel import (
    explain_rule,
    is_valid_relationship,
    list_relationship_types,
)


def test_same_type_specialization_is_valid_with_citation():
    assert is_valid_relationship(
        "Business Process",
        "Specialization",
        "Business Process",
    )

    explanation = explain_rule(
        source_type="Business Process",
        relationship_type="Specialization",
        target_type="Business Process",
    )
    assert explanation["valid"] is True
    assert explanation["status"] == "valid"
    assert explanation["rule_id"] == "specialization-same-element-type"
    assert "Section 5" in explanation["citation"]


def test_cross_type_specialization_fails_closed():
    explanation = explain_rule(
        source_type="Business Process",
        relationship_type="Specialization",
        target_type="Application Component",
    )

    assert explanation["valid"] is False
    assert explanation["status"] == "unknown"
    assert "not established" in explanation["reason"]


def test_unapproved_candidate_relationship_is_not_valid():
    assert not is_valid_relationship(
        "Application Service",
        "Serving",
        "Business Process",
    )

    explanation = explain_rule(
        source_type="Application Service",
        relationship_type="Serving",
        target_type="Business Process",
    )
    assert explanation["valid"] is False
    assert explanation["status"] == "needs_review"
    assert "requires confirmation" in explanation["citation"]


def test_unknown_relationship_type_fails_closed():
    explanation = explain_rule(
        source_type="Application Service",
        relationship_type="Magically Integrates With",
        target_type="Business Process",
    )

    assert explanation["valid"] is False
    assert explanation["status"] == "invalid"
    assert explanation["citation"] is None


def test_relationship_type_vocabulary_is_available():
    assert list_relationship_types() == [
        "Composition",
        "Aggregation",
        "Assignment",
        "Realization",
        "Serving",
        "Access",
        "Influence",
        "Association",
        "Triggering",
        "Flow",
        "Specialization",
    ]
