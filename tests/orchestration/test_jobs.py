from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config.settings import Settings
from backend.database import models  # noqa: F401
from backend.database.base import Base
from backend.orchestration import jobs
from backend.orchestration.jobs import run_as_is_job
from backend.repository.jobs import create_job, get_job
from backend.repository.systems import create_legacy_system


def test_run_as_is_job_marks_success(monkeypatch, tmp_path: Path) -> None:
    settings, job_id = _seed_job(tmp_path)
    monkeypatch.setattr(jobs, "run_as_is_ingestion", lambda *args, **kwargs: None)

    run_as_is_job(
        job_id=job_id,
        system_id="demo",
        evidence_path=str(tmp_path / "evidence"),
        run_id="run-1",
        settings=settings,
    )

    stored = _get_job(settings, job_id)
    assert stored.status == "succeeded"
    assert stored.run_id == "run-1"
    assert stored.started_at is not None
    assert stored.finished_at is not None


def test_run_as_is_job_marks_failure_with_error(monkeypatch, tmp_path: Path) -> None:
    settings, job_id = _seed_job(tmp_path)

    def fail(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(jobs, "run_as_is_ingestion", fail)

    run_as_is_job(
        job_id=job_id,
        system_id="demo",
        evidence_path=str(tmp_path / "evidence"),
        run_id="run-1",
        settings=settings,
    )

    stored = _get_job(settings, job_id)
    assert stored.status == "failed"
    assert stored.error_message == "RuntimeError: boom"
    assert stored.finished_at is not None


def _seed_job(tmp_path: Path) -> tuple[Settings, str]:
    db_path = tmp_path / "jobs.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with SessionLocal() as session:
        create_legacy_system(session, system_id="demo", name="Demo")
        job = create_job(session, system_id="demo", phase="as-is")
        session.commit()
        job_id = job.id

    settings = Settings(
        database_url=database_url,
        evidence_root=str(tmp_path / "evidence"),
        model_repo_checkout=str(tmp_path / "model"),
        github_model_repo="example/repo",
        github_token="token",
        backend_api_key="api-key",
    )
    return settings, job_id


def _get_job(settings: Settings, job_id: str):
    engine = create_engine(settings.database_url, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with SessionLocal() as session:
        return get_job(session, job_id)
