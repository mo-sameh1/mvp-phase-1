from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import ArtifactVersion


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
