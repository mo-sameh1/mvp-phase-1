from __future__ import annotations

import json

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.api.routes import router as api_router
from backend.config.settings import Settings, get_settings
from backend.database.session import get_session
from backend.gitops.webhook_security import verify_github_signature
from backend.gitops.webhooks import handle_pull_request_webhook

SESSION_DEPENDENCY = Depends(get_session)
SETTINGS_DEPENDENCY = Depends(get_settings)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    app = FastAPI(title="7bots MVP Phase 1")
    _add_cors_middleware(app, app_settings)
    app.include_router(api_router)

    @app.get("/")
    async def health_check() -> dict[str, str]:
        return {"health": "OK"}

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


def _add_cors_middleware(app: FastAPI, settings: Settings) -> None:
    origins = _parse_cors_origins(settings.cors_allowed_origins)
    if not origins:
        return
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key"],
    )


def _parse_cors_origins(value: str) -> list[str]:
    return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
