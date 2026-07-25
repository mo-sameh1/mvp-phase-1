from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import (
    ArtifactVersion,
    EvidenceSource,
    Job,
    LegacySystem,
    ModelElementIndex,
    utc_now,
)

TERMINAL_JOB_STATUSES = {"succeeded", "failed"}


def create_legacy_system(
    session: Session, *, name: str, description: str | None = None, system_id: str | None = None
) -> LegacySystem:
    system = LegacySystem(id=system_id, name=name, description=description)
    session.add(system)
    session.flush()
    return system


def get_legacy_system(session: Session, system_id: str) -> LegacySystem | None:
    return session.get(LegacySystem, system_id)


def get_legacy_system_by_name(session: Session, name: str) -> LegacySystem | None:
    return session.scalar(select(LegacySystem).where(LegacySystem.name == name))


def upsert_model_element_index(
    session: Session,
    *,
    element_id: str,
    system_id: str,
    layer: str,
    archimate_type: str,
    name: str,
    git_path: str,
    current_commit: str,
) -> ModelElementIndex:
    element = session.get(ModelElementIndex, element_id)
    if element is None:
        element = ModelElementIndex(
            id=element_id,
            system_id=system_id,
            layer=layer,
            archimate_type=archimate_type,
            name=name,
            git_path=git_path,
            current_commit=current_commit,
        )
        session.add(element)
    else:
        element.system_id = system_id
        element.layer = layer
        element.archimate_type = archimate_type
        element.name = name
        element.git_path = git_path
        element.current_commit = current_commit
        element.updated_at = utc_now()

    session.flush()
    return element


def get_model_element(session: Session, element_id: str) -> ModelElementIndex | None:
    return session.get(ModelElementIndex, element_id)


def list_model_elements(
    session: Session, *, system_id: str, layer: str | None = None
) -> list[ModelElementIndex]:
    statement = select(ModelElementIndex).where(ModelElementIndex.system_id == system_id)
    if layer is not None:
        statement = statement.where(ModelElementIndex.layer == layer)
    return list(
        session.scalars(statement.order_by(ModelElementIndex.layer, ModelElementIndex.name))
    )


def create_artifact_version(
    session: Session,
    *,
    system_id: str,
    commit_sha: str,
    phase: str,
    author_type: str,
    tag: str | None = None,
    run_id: str | None = None,
    approval_status: str = "pending",
    pr_number: int | None = None,
    pr_url: str | None = None,
) -> ArtifactVersion:
    artifact = ArtifactVersion(
        system_id=system_id,
        commit_sha=commit_sha,
        phase=phase,
        tag=tag,
        author_type=author_type,
        run_id=run_id,
        approval_status=approval_status,
        pr_number=pr_number,
        pr_url=pr_url,
    )
    session.add(artifact)
    session.flush()
    return artifact


def get_artifact_version(session: Session, artifact_id: str) -> ArtifactVersion | None:
    return session.get(ArtifactVersion, artifact_id)


def list_artifact_versions(session: Session, *, system_id: str) -> list[ArtifactVersion]:
    statement = (
        select(ArtifactVersion)
        .where(ArtifactVersion.system_id == system_id)
        .order_by(ArtifactVersion.created_at.desc())
    )
    return list(session.scalars(statement))


def update_artifact_version(
    session: Session,
    artifact_id: str,
    *,
    approval_status: str | None = None,
    approved_by: str | None = None,
    approved_at: datetime | None = None,
    pr_number: int | None = None,
    pr_url: str | None = None,
) -> ArtifactVersion:
    artifact = session.get(ArtifactVersion, artifact_id)
    if artifact is None:
        raise ValueError(f"Artifact version not found: {artifact_id}")

    if approval_status is not None:
        artifact.approval_status = approval_status
    if approved_by is not None:
        artifact.approved_by = approved_by
    if approved_at is not None:
        artifact.approved_at = approved_at
    if pr_number is not None:
        artifact.pr_number = pr_number
    if pr_url is not None:
        artifact.pr_url = pr_url

    session.flush()
    return artifact


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


def create_evidence_source(
    session: Session,
    *,
    system_id: str,
    source_type: str,
    location: str,
    description: str | None = None,
) -> EvidenceSource:
    existing = session.scalar(
        select(EvidenceSource).where(
            EvidenceSource.system_id == system_id,
            EvidenceSource.source_type == source_type,
            EvidenceSource.location == location,
        )
    )
    if existing is not None:
        if description is not None:
            existing.description = description
            session.flush()
        return existing

    source = EvidenceSource(
        system_id=system_id,
        source_type=source_type,
        location=location,
        description=description,
    )
    session.add(source)
    session.flush()
    return source


def list_evidence_sources(session: Session, *, system_id: str) -> list[EvidenceSource]:
    statement = (
        select(EvidenceSource)
        .where(EvidenceSource.system_id == system_id)
        .order_by(EvidenceSource.added_at.desc())
    )
    return list(session.scalars(statement))
