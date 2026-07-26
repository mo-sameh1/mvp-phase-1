from backend.repository import (
    create_artifact_version,
    create_legacy_system,
    get_artifact_version,
    list_artifact_versions,
    update_artifact_version,
)


def test_artifact_version_tracks_pull_request_metadata(session):
    system = create_legacy_system(session, name="Demo")

    artifact = create_artifact_version(
        session,
        system_id=system.id,
        commit_sha="abc123",
        phase="as-is",
        author_type="agent",
        run_id="run-1",
        pr_number=42,
        pr_url="https://github.com/example/model/pull/42",
    )
    update_artifact_version(
        session,
        artifact.id,
        approval_status="approved",
        approved_by="reviewer@example.com",
    )

    stored = get_artifact_version(session, artifact.id)
    assert stored.approval_status == "approved"
    assert stored.pr_number == 42
    assert stored.pr_url.endswith("/pull/42")
    assert list_artifact_versions(session, system_id=system.id) == [stored]
