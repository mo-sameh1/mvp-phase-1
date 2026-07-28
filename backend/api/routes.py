from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from agents.schema import ModelElement
from backend.api.auth import require_api_key
from backend.api.schemas import (
    ArtifactVersionResponse,
    IngestRequest,
    IngestResponse,
    JobResponse,
    ModelElementDetailResponse,
    ModelElementIndexResponse,
)
from backend.config.settings import Settings, get_settings
from backend.database.session import get_session
from backend.gitops.local_git import GitCommandError, GitRunner, show_file_at_ref
from backend.orchestration.jobs import run_as_is_job
from backend.repository.artifacts import list_artifact_versions
from backend.repository.jobs import create_job, get_job
from backend.repository.model_elements import get_model_element, list_model_elements
from backend.repository.systems import create_legacy_system, get_legacy_system

Layer = Literal["motivation", "strategy", "business", "application", "technology"]

router = APIRouter(dependencies=[Depends(require_api_key)])
INGEST_BODY = Body(default_factory=IngestRequest)
LAYER_QUERY = Query(default=None)
SESSION_DEPENDENCY = Depends(get_session)
SETTINGS_DEPENDENCY = Depends(get_settings)


@router.post(
    "/systems/{system_id}/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_ingestion(
    system_id: str,
    background_tasks: BackgroundTasks,
    payload: IngestRequest = INGEST_BODY,
    session: Session = SESSION_DEPENDENCY,
    settings: Settings = SETTINGS_DEPENDENCY,
) -> IngestResponse:
    _ensure_system(session, system_id)
    job = create_job(session, system_id=system_id, phase="as-is")
    run_id = f"as-is-{job.id}"
    job.run_id = run_id
    evidence_path = payload.evidence_path or settings.evidence_root
    background_tasks.add_task(
        run_as_is_job,
        job_id=job.id,
        system_id=system_id,
        evidence_path=evidence_path,
        run_id=run_id,
        settings=settings,
    )
    session.commit()
    return IngestResponse(
        job_id=job.id,
        system_id=system_id,
        phase=job.phase,
        status=job.status,
        run_id=run_id,
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
def read_job(job_id: str, session: Session = SESSION_DEPENDENCY) -> JobResponse:
    job = get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse(**_columns(job))


@router.get("/systems/{system_id}/elements", response_model=list[ModelElementIndexResponse])
def read_model_elements(
    system_id: str,
    layer: Layer | None = LAYER_QUERY,
    session: Session = SESSION_DEPENDENCY,
) -> list[ModelElementIndexResponse]:
    _require_system(session, system_id)
    elements = list_model_elements(session, system_id=system_id, layer=layer)
    return [ModelElementIndexResponse(**_columns(element)) for element in elements]


@router.get("/elements/{element_id}", response_model=ModelElementDetailResponse)
def read_element_detail(
    element_id: str,
    session: Session = SESSION_DEPENDENCY,
    settings: Settings = SETTINGS_DEPENDENCY,
) -> ModelElementDetailResponse:
    index = get_model_element(session, element_id)
    if index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Element not found")
    try:
        payload = _read_model_payload(settings, index.current_commit, index.git_path)
        element = ModelElement(**payload)
    except (GitCommandError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not read indexed model element: {exc}",
        ) from exc
    return ModelElementDetailResponse(
        id=index.id,
        system_id=index.system_id,
        git_path=index.git_path,
        current_commit=index.current_commit,
        element=element.model_dump(mode="json"),
    )


@router.get(
    "/systems/{system_id}/artifact-versions",
    response_model=list[ArtifactVersionResponse],
)
def read_artifact_versions(
    system_id: str,
    session: Session = SESSION_DEPENDENCY,
) -> list[ArtifactVersionResponse]:
    _require_system(session, system_id)
    artifacts = list_artifact_versions(session, system_id=system_id)
    return [ArtifactVersionResponse(**_columns(artifact)) for artifact in artifacts]


def _ensure_system(session: Session, system_id: str) -> None:
    if get_legacy_system(session, system_id) is None:
        create_legacy_system(
            session,
            system_id=system_id,
            name=system_id,
            description="Legacy system created by the ingestion API.",
        )


def _require_system(session: Session, system_id: str) -> None:
    if get_legacy_system(session, system_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System not found")


def _read_model_payload(settings: Settings, commit_sha: str, git_path: str) -> dict:
    runner = GitRunner(
        Path(settings.model_repo_checkout).expanduser().resolve(),
        settings.github_model_repo,
        settings.github_token,
    )
    content = show_file_at_ref(runner, commit_sha, git_path)
    return json.loads(content)


def _columns(value) -> dict:
    return {column.name: getattr(value, column.name) for column in value.__table__.columns}
