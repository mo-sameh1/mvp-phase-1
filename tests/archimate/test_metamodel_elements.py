from agents.archimate_metamodel import (
    explain_rule,
    is_valid_element_type,
    list_element_types,
)


def test_valid_element_type_for_layer():
    assert is_valid_element_type("application", "Application Component")

    explanation = explain_rule(layer="application", archimate_type="Application Component")
    assert explanation["valid"] is True
    assert explanation["status"] == "valid"
    assert "Section 9" in explanation["citation"]


def test_wrong_layer_element_type_fails_closed():
    assert not is_valid_element_type("business", "Application Component")

    explanation = explain_rule(layer="business", archimate_type="Application Component")
    assert explanation["valid"] is False
    assert explanation["status"] == "invalid"
    assert "application" in explanation["reason"]


def test_unknown_element_type_fails_closed():
    assert not is_valid_element_type("application", "Legacy Batch Job")

    explanation = explain_rule(layer="application", archimate_type="Legacy Batch Job")
    assert explanation["valid"] is False
    assert explanation["status"] == "invalid"
    assert explanation["citation"] is None


def test_lists_element_types_by_layer():
    assert list_element_types("strategy") == [
        "Resource",
        "Capability",
        "Value Stream",
        "Course of Action",
    ]
