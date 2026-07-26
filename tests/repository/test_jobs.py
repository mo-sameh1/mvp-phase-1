from backend.repository import (
    create_job,
    create_legacy_system,
    get_job,
    list_jobs,
    update_job_status,
)


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
