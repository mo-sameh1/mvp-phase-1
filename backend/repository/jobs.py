from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import Job, utc_now

TERMINAL_JOB_STATUSES = {"succeeded", "failed"}


def create_job(
    session: Session,
    *,
    system_id: str,
    phase: str,
    status: str = "queued",
    run_id: str | None = None,
) -> Job:
    job = Job(system_id=system_id, phase=phase, status=status, run_id=run_id)
    if status == "running":
        job.started_at = utc_now()
    if status in TERMINAL_JOB_STATUSES:
        job.finished_at = utc_now()
    session.add(job)
    session.flush()
    return job


def get_job(session: Session, job_id: str) -> Job | None:
    return session.get(Job, job_id)


def list_jobs(session: Session, *, system_id: str) -> list[Job]:
    statement = select(Job).where(Job.system_id == system_id).order_by(Job.started_at.desc())
    return list(session.scalars(statement))


def update_job_status(
    session: Session,
    job_id: str,
    *,
    status: str,
    run_id: str | None = None,
    error_message: str | None = None,
) -> Job:
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    job.status = status
    if run_id is not None:
        job.run_id = run_id
    if error_message is not None:
        job.error_message = error_message
    if status == "running" and job.started_at is None:
        job.started_at = utc_now()
    if status in TERMINAL_JOB_STATUSES and job.finished_at is None:
        job.finished_at = utc_now()

    session.flush()
    return job
