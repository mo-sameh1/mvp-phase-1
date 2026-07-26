import json
from pathlib import Path

from agents.archimate_metamodel.metamodel import SKILL_DATA_DIR


def load_json(name: str):
    with (SKILL_DATA_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


def test_every_element_has_summary_and_citation():
    elements = load_json("elements.json")

    for layer, layer_data in elements["layers"].items():
        assert layer_data["citation"], layer
        for element in layer_data["elements"]:
            assert element["name"], layer
            assert element["summary"], element["name"]


def test_relationship_rules_are_citation_backed_and_reviewed():
    relationships = load_json("relationships.json")

    for rule in relationships["validation_rules"]:
        assert rule["review_status"] == "approved"
        assert rule["citation"]


def test_candidate_examples_are_not_approved_rules():
    relationships = load_json("relationships.json")
    approved_rule_ids = {rule["id"] for rule in relationships["validation_rules"]}

    assert approved_rule_ids == {"specialization-same-element-type"}
    for candidate in relationships["candidate_examples"]:
        assert candidate["review_status"] == "needs_review"


def test_skill_document_points_to_structured_tables():
    skill = Path("agents/skills/archimate-metamodel/SKILL.md").read_text(encoding="utf-8")

    assert "data/elements.json" in skill
    assert "data/relationships.json" in skill
    assert "not established by the ArchiMate metamodel skill" in skill
