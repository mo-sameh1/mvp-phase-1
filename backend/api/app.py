from __future__ import annotations

import json

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from sqlalchemy.orm import Session

from backend.config.settings import Settings, get_settings
from backend.database.session import get_session
from backend.gitops.webhook_security import verify_github_signature
from backend.gitops.webhooks import handle_pull_request_webhook

SESSION_DEPENDENCY = Depends(get_session)
SETTINGS_DEPENDENCY = Depends(get_settings)


def create_app() -> FastAPI:
    app = FastAPI(title="7bots MVP Phase 1")

    @app.post("/webhooks/github")
    async def github_webhook(
        request: Request,
        x_github_event: str | None = Header(default=None),
        x_hub_signature_256: str | None = Header(default=None),
        session: Session = SESSION_DEPENDENCY,
        settings: Settings = SETTINGS_DEPENDENCY,
    ) -> dict:
        body = await request.body()
        if not verify_github_signature(
            settings.github_webhook_secret,
            body,
            x_hub_signature_256,
        ):
            raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature")
        if x_github_event != "pull_request":
            return {"status": "ignored", "approved": False}
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

        result = handle_pull_request_webhook(session, payload, settings)
        session.commit()
        return {
            "status": result.status,
            "approved": result.approved,
            "artifact_version_id": result.artifact_version_id,
            "indexed_elements": result.indexed_elements,
        }

    return app
