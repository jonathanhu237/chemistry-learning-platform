from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from server.app.infrastructure.settings import get_settings


bearer = HTTPBearer(auto_error=False)


class WebAdminSessionResponse(BaseModel):
    ok: bool = True


def require_web_admin_token(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> None:
    configured_token = get_settings().web_admin_access_token
    if not configured_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="WEB_ADMIN_ACCESS_TOKEN is not configured",
        )
    if not credentials or not secrets.compare_digest(credentials.credentials, configured_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid web admin token")
