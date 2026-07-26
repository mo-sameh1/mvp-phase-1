from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import EvidenceSource


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
