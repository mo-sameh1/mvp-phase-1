from __future__ import annotations

import secrets

from fastapi import Depends, Header, HTTPException, status

from backend.config.settings import Settings, get_settings

API_KEY_HEADER = Header(default=None)
SETTINGS_DEPENDENCY = Depends(get_settings)


def require_api_key(
    x_api_key: str | None = API_KEY_HEADER,
    settings: Settings = SETTINGS_DEPENDENCY,
) -> None:
    if _is_placeholder(settings.backend_api_key):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend API key is not configured",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, settings.backend_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def _is_placeholder(value: str) -> bool:
    return not value or value.endswith("_placeholder")
