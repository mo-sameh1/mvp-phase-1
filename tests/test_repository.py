from backend.repository import (
    create_artifact_version,
    create_evidence_source,
    create_job,
    create_legacy_system,
    get_artifact_version,
    get_job,
    get_legacy_system,
    get_legacy_system_by_name,
    get_model_element,
    list_artifact_versions,
    list_evidence_sources,
    list_jobs,
    list_model_elements,
    update_artifact_version,
    update_job_status,
    upsert_model_element_index,
)


def test_create_and_get_legacy_system(session):
    system = create_legacy_system(
        session,
        system_id="demo-legacy-system",
        name="Demo Legacy System",
        description="Synthetic MVP fixture",
    )

    assert get_legacy_system(session, system.id) == system
    assert get_legacy_system_by_name(session, "Demo Legacy System") == system


def test_upsert_model_element_index_is_idempotent(session):
    system = create_legacy_system(session, name="Demo")

    first = upsert_model_element_index(
        session,
        element_id="payment-service",
        system_id=system.id,
        layer="application",
        archimate_type="Application Service",
        name="Payment Service",
        git_path="systems/demo/as-is/application/payment-service.json",
        current_commit="abc123",
    )
    second = upsert_model_element_index(
        session,
        element_id="payment-service",
        system_id=system.id,
        layer="application",
        archimate_type="Application Component",
        name="Payment Service API",
        git_path="systems/demo/as-is/application/payment-service-api.json",
        current_commit="def456",
    )

    assert first.id == second.id
    assert get_model_element(session, "payment-service").archimate_type == "Application Component"
    assert len(list_model_elements(session, system_id=system.id)) == 1
    assert len(list_model_elements(session, system_id=system.id, layer="application")) == 1


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


def test_job_status_updates_are_idempotent(session):
    system = create_legacy_system(session, name="Demo")
    job = create_job(session, system_id=system.id, phase="as-is")

    running = update_job_status(session, job.id, status="running", run_id="run-1")
    first_started_at = running.started_at

    running_again = update_job_status(session, job.id, status="running", run_id="run-1")
    assert running_again.started_at == first_started_at

    failed = update_job_status(session, job.id, status="failed", error_message="boom")
    first_finished_at = failed.finished_at

    failed_again = update_job_status(session, job.id, status="failed", error_message="boom")
    assert failed_again.finished_at == first_finished_at
    assert failed_again.error_message == "boom"
    assert get_job(session, job.id) == failed_again
    assert list_jobs(session, system_id=system.id) == [failed_again]


def test_evidence_source_create_is_idempotent(session):
    system = create_legacy_system(session, name="Demo")

    first = create_evidence_source(
        session,
        system_id=system.id,
        source_type="code",
        location="/evidence/code/payment.py",
        description="Initial description",
    )
    second = create_evidence_source(
        session,
        system_id=system.id,
        source_type="code",
        location="/evidence/code/payment.py",
        description="Updated description",
    )

    assert first.id == second.id
    assert second.description == "Updated description"
    assert list_evidence_sources(session, system_id=system.id) == [second]
