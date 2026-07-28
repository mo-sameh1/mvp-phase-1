from __future__ import annotations

from backend.config.settings import Settings, get_settings
from backend.database.session import build_sessionmaker
from backend.orchestration.phase1 import run_as_is_ingestion
from backend.repository.jobs import update_job_status


def run_as_is_job(
    *,
    job_id: str,
    system_id: str,
    evidence_path: str,
    run_id: str,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    SessionLocal = build_sessionmaker(settings.database_url)
    with SessionLocal() as session:
        try:
            update_job_status(session, job_id, status="running", run_id=run_id)
            session.commit()

            run_as_is_ingestion(
                system_id,
                evidence_path,
                run_id=run_id,
                settings=settings,
                session=session,
            )

            update_job_status(session, job_id, status="succeeded", run_id=run_id)
            session.commit()
        except Exception as exc:
            session.rollback()
            error_message = f"{type(exc).__name__}: {exc}"
            update_job_status(
                session,
                job_id,
                status="failed",
                run_id=run_id,
                error_message=error_message,
            )
            session.commit()
