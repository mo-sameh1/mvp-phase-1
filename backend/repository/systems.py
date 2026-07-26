from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import LegacySystem


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
