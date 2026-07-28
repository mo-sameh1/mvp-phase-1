from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from backend.config.settings import Settings
from backend.database.models import utc_now
from backend.gitops.index_refresh import refresh_model_element_index
from backend.repository.artifacts import get_artifact_version_by_pr, update_artifact_version


@dataclass(frozen=True)
class WebhookResult:
    status: str
    approved: bool
    artifact_version_id: str | None = None
    indexed_elements: int = 0


def handle_pull_request_webhook(
    session: Session,
    payload: dict,
    settings: Settings,
) -> WebhookResult:
    action = payload.get("action")
    pull_request = payload.get("pull_request") or {}
    if action != "closed" or pull_request.get("merged") is not True:
        return WebhookResult(status="ignored", approved=False)

    pr_number = int(pull_request["number"])
    artifact = get_artifact_version_by_pr(session, pr_number=pr_number)
    if artifact is None:
        return WebhookResult(status="ignored_no_artifact", approved=False)
    if artifact.approval_status == "approved":
        return WebhookResult(
            status="already_approved",
            approved=True,
            artifact_version_id=artifact.id,
        )

    sender = payload.get("sender") or {}
    update_artifact_version(
        session,
        artifact.id,
        approval_status="approved",
        approved_by=sender.get("login") or "github",
        approved_at=utc_now(),
    )
    indexed = refresh_model_element_index(
        session,
        model_repo_checkout=Path(settings.model_repo_checkout).expanduser().resolve(),
        github_repo=settings.github_model_repo,
        github_token=settings.github_token,
        system_id=artifact.system_id,
    )
    return WebhookResult(
        status="approved",
        approved=True,
        artifact_version_id=artifact.id,
        indexed_elements=indexed,
    )
