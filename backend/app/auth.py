"""Bearer-JWT authentication for the Clinical Trial Management System.

CTMS is a standalone, internet-reachable FastAPI service that previously had NO
authentication layer — every subject/consent/visit/dispense/eligibility route was
reachable anonymously with only ``Depends(get_db)``. This module adds a
fail-closed bearer-token guard (route-auth remediation, 2026-08-11): a request
with no / malformed / expired / wrong-signature token is rejected with 401.

Tokens are HS256-signed with the service's existing ``secret_key`` setting.
"""
from __future__ import annotations

from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

_bearer = HTTPBearer(auto_error=False)
_ALGORITHM = "HS256"


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    """Validate the ``Authorization: Bearer <jwt>`` header; return the claims."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims: dict[str, Any] = jwt.decode(
            credentials.credentials,
            get_settings().secret_key,
            algorithms=[_ALGORITHM],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return claims
