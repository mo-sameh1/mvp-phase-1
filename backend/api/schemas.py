from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    evidence_path: str | None = Field(
        default=None,
        description="Evidence path inside EVIDENCE_ROOT, or /evidence/ for the configured root.",
    )


class IngestResponse(BaseModel):
    job_id: str
    system_id: str
    phase: str
    status: str
    run_id: str


class JobResponse(BaseModel):
    id: str
    system_id: str
    phase: str
    status: str
    run_id: str | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None


class ModelElementIndexResponse(BaseModel):
    id: str
    system_id: str
    layer: str
    archimate_type: str
    name: str
    git_path: str
    current_commit: str
    updated_at: datetime


class ModelElementDetailResponse(BaseModel):
    id: str
    system_id: str
    git_path: str
    current_commit: str
    element: dict[str, Any]


class ArtifactVersionResponse(BaseModel):
    id: str
    system_id: str
    commit_sha: str
    phase: str
    tag: str | None
    author_type: str
    run_id: str | None
    approval_status: str
    approved_by: str | None
    approved_at: datetime | None
    pr_number: int | None
    pr_url: str | None
    created_at: datetime
