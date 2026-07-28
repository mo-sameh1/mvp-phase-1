from pathlib import Path

from agents.ingestion.model_io import write_model_element
from agents.schema import EvidenceCitation, ModelElement
from backend.gitops import index_refresh
from backend.gitops.index_refresh import refresh_model_element_index
from backend.repository import (
    create_legacy_system,
    get_model_element,
    list_model_elements,
    upsert_model_element_index,
)


def test_refresh_model_element_index_upserts_current_files_and_removes_stale(
    session,
    monkeypatch,
    tmp_path: Path,
) -> None:
    create_legacy_system(session, system_id="demo", name="Demo")
    upsert_model_element_index(
        session,
        element_id="stale",
        system_id="demo",
        layer="business",
        archimate_type="Business Process",
        name="Stale",
        git_path="systems/demo/as-is/business/stale.json",
        current_commit="old",
    )
    write_model_element(tmp_path / "systems", "demo", _business_process())
    monkeypatch.setattr(index_refresh, "checkout_base_branch", lambda runner, branch: None)
    monkeypatch.setattr(index_refresh, "current_commit", lambda runner: "newsha")

    count = refresh_model_element_index(
        session,
        model_repo_checkout=tmp_path,
        github_repo="example/repo",
        github_token="token",
        system_id="demo",
    )

    assert count == 1
    indexed = get_model_element(session, "permit-review-process")
    assert indexed.current_commit == "newsha"
    assert indexed.git_path == "systems/demo/as-is/business/permit-review-process.json"
    assert [item.id for item in list_model_elements(session, system_id="demo")] == [
        "permit-review-process"
    ]


def _business_process() -> ModelElement:
    return ModelElement(
        id="permit-review-process",
        layer="business",
        archimate_type="Business Process",
        name="Permit Review Process",
        documentation="Process.",
        confidence="observed",
        evidence=[
            EvidenceCitation(
                source_type="fixture",
                locator="/evidence/example.md:1",
                excerpt="Process.",
            )
        ],
        relationships=[],
    )
