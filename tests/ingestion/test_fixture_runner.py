from pathlib import Path

from agents.ingestion.fixture_runner import compare_repeated_counts, run_fixture_ingestion
from agents.ingestion.model_io import validate_model_tree


def test_epic_e_fixture_runner_writes_expected_elements_and_relationships(
    tmp_path: Path,
) -> None:
    fixture_root = Path("test-fixtures/epic-e")

    result = run_fixture_ingestion(
        fixture_root=fixture_root,
        systems_root=tmp_path,
        system_id="demo-legacy-system",
    )
    elements = validate_model_tree(tmp_path, "demo-legacy-system")

    assert result.element_count == 13
    assert result.element_counts_by_layer == {
        "application": 4,
        "business": 2,
        "motivation": 2,
        "strategy": 2,
        "technology": 3,
    }
    assert set(elements) == {
        "app-server-node",
        "case-api",
        "case-database-artifact",
        "case-handling-service",
        "case-management-system",
        "case-record",
        "citizen-access-goal",
        "citizen-applicant",
        "container-runtime",
        "digital-case-capability",
        "online-service-course-of-action",
        "permit-review-process",
        "regulatory-compliance-driver",
    }

    written = [decision for decision in result.relationship_decisions if decision.written]
    skipped = [decision for decision in result.relationship_decisions if not decision.written]
    assert len(written) == 3
    assert len(skipped) == 1
    assert skipped[0].relationship_type == "Flow"
    assert "not established" in skipped[0].reason


def test_epic_e_fixture_runner_repeat_count_is_reproducible(tmp_path: Path) -> None:
    fixture_root = Path("test-fixtures/epic-e")
    results = [
        run_fixture_ingestion(
            fixture_root=fixture_root,
            systems_root=tmp_path / f"run-{index}",
            system_id="demo-legacy-system",
            repeat_index=index,
        )
        for index in range(1, 3)
    ]

    compare_repeated_counts(results, tolerance=1)
    assert [result.element_count for result in results] == [13, 13]
