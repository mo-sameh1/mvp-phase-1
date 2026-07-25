from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class LegacySystem(Base):
    __tablename__ = "legacy_systems"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)

    model_elements: Mapped[list[ModelElementIndex]] = relationship(
        back_populates="system", cascade="all, delete-orphan"
    )
    artifact_versions: Mapped[list[ArtifactVersion]] = relationship(
        back_populates="system", cascade="all, delete-orphan"
    )
    jobs: Mapped[list[Job]] = relationship(back_populates="system", cascade="all, delete-orphan")
    evidence_sources: Mapped[list[EvidenceSource]] = relationship(
        back_populates="system", cascade="all, delete-orphan"
    )


class ModelElementIndex(Base):
    __tablename__ = "model_element_index"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    system_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("legacy_systems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    layer: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    archimate_type: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    git_path: Mapped[str] = mapped_column(Text, nullable=False)
    current_commit: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    system: Mapped[LegacySystem] = relationship(back_populates="model_elements")

    __table_args__ = (
        CheckConstraint(
            "layer in ('motivation', 'strategy', 'business', 'application', 'technology')",
            name="ck_model_element_index_layer",
        ),
    )


class ArtifactVersion(Base):
    __tablename__ = "artifact_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    system_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("legacy_systems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commit_sha: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    phase: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tag: Mapped[str | None] = mapped_column(String(128))
    author_type: Mapped[str] = mapped_column(String(32), nullable=False)
    run_id: Mapped[str | None] = mapped_column(String(128), index=True)
    approval_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    approved_by: Mapped[str | None] = mapped_column(String(255))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pr_number: Mapped[int | None] = mapped_column(Integer)
    pr_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    system: Mapped[LegacySystem] = relationship(back_populates="artifact_versions")

    __table_args__ = (
        CheckConstraint(
            "approval_status in ('pending', 'approved', 'rejected')",
            name="ck_artifact_versions_approval_status",
        ),
        CheckConstraint(
            "author_type in ('agent', 'human', 'system')",
            name="ck_artifact_versions_author_type",
        ),
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    system_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("legacy_systems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phase: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    run_id: Mapped[str | None] = mapped_column(String(128), index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    system: Mapped[LegacySystem] = relationship(back_populates="jobs")

    __table_args__ = (
        CheckConstraint(
            "status in ('queued', 'running', 'succeeded', 'failed')",
            name="ck_jobs_status",
        ),
    )


class EvidenceSource(Base):
    __tablename__ = "evidence_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    system_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("legacy_systems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    location: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    system: Mapped[LegacySystem] = relationship(back_populates="evidence_sources")

    __table_args__ = (
        UniqueConstraint(
            "system_id",
            "source_type",
            "location",
            name="uq_evidence_source_location",
        ),
    )
