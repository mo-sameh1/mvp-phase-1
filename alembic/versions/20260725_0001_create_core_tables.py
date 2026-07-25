"""create core tables

Revision ID: 20260725_0001
Revises:
Create Date: 2026-07-25

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260725_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "legacy_systems",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "artifact_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("system_id", sa.String(length=36), nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=False),
        sa.Column("phase", sa.String(length=64), nullable=False),
        sa.Column("tag", sa.String(length=128), nullable=True),
        sa.Column("author_type", sa.String(length=32), nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=True),
        sa.Column("approval_status", sa.String(length=32), nullable=False),
        sa.Column("approved_by", sa.String(length=255), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pr_number", sa.Integer(), nullable=True),
        sa.Column("pr_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "approval_status in ('pending', 'approved', 'rejected')",
            name="ck_artifact_versions_approval_status",
        ),
        sa.CheckConstraint(
            "author_type in ('agent', 'human', 'system')",
            name="ck_artifact_versions_author_type",
        ),
        sa.ForeignKeyConstraint(["system_id"], ["legacy_systems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_artifact_versions_commit_sha", "artifact_versions", ["commit_sha"])
    op.create_index("ix_artifact_versions_phase", "artifact_versions", ["phase"])
    op.create_index("ix_artifact_versions_run_id", "artifact_versions", ["run_id"])
    op.create_index("ix_artifact_versions_system_id", "artifact_versions", ["system_id"])

    op.create_table(
        "evidence_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("system_id", sa.String(length=36), nullable=False),
        sa.Column("source_type", sa.String(length=128), nullable=False),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["system_id"], ["legacy_systems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "system_id",
            "source_type",
            "location",
            name="uq_evidence_source_location",
        ),
    )
    op.create_index("ix_evidence_sources_system_id", "evidence_sources", ["system_id"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("system_id", sa.String(length=36), nullable=False),
        sa.Column("phase", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status in ('queued', 'running', 'succeeded', 'failed')",
            name="ck_jobs_status",
        ),
        sa.ForeignKeyConstraint(["system_id"], ["legacy_systems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_phase", "jobs", ["phase"])
    op.create_index("ix_jobs_run_id", "jobs", ["run_id"])
    op.create_index("ix_jobs_system_id", "jobs", ["system_id"])

    op.create_table(
        "model_element_index",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("system_id", sa.String(length=36), nullable=False),
        sa.Column("layer", sa.String(length=64), nullable=False),
        sa.Column("archimate_type", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("git_path", sa.Text(), nullable=False),
        sa.Column("current_commit", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "layer in ('motivation', 'strategy', 'business', 'application', 'technology')",
            name="ck_model_element_index_layer",
        ),
        sa.ForeignKeyConstraint(["system_id"], ["legacy_systems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_model_element_index_layer", "model_element_index", ["layer"])
    op.create_index("ix_model_element_index_name", "model_element_index", ["name"])
    op.create_index("ix_model_element_index_system_id", "model_element_index", ["system_id"])


def downgrade() -> None:
    op.drop_index("ix_model_element_index_system_id", table_name="model_element_index")
    op.drop_index("ix_model_element_index_name", table_name="model_element_index")
    op.drop_index("ix_model_element_index_layer", table_name="model_element_index")
    op.drop_table("model_element_index")

    op.drop_index("ix_jobs_system_id", table_name="jobs")
    op.drop_index("ix_jobs_run_id", table_name="jobs")
    op.drop_index("ix_jobs_phase", table_name="jobs")
    op.drop_table("jobs")

    op.drop_index("ix_evidence_sources_system_id", table_name="evidence_sources")
    op.drop_table("evidence_sources")

    op.drop_index("ix_artifact_versions_system_id", table_name="artifact_versions")
    op.drop_index("ix_artifact_versions_run_id", table_name="artifact_versions")
    op.drop_index("ix_artifact_versions_phase", table_name="artifact_versions")
    op.drop_index("ix_artifact_versions_commit_sha", table_name="artifact_versions")
    op.drop_table("artifact_versions")

    op.drop_table("legacy_systems")
