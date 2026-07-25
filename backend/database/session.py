from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config.settings import get_settings


def build_engine(database_url: str | None = None):
    url = database_url or get_settings().database_url
    return create_engine(url, future=True)


def build_sessionmaker(database_url: str | None = None) -> sessionmaker[Session]:
    return sessionmaker(bind=build_engine(database_url), autoflush=False, expire_on_commit=False)


SessionLocal = build_sessionmaker()


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
