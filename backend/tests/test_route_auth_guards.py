"""Regression tests: CTMS patient/subject/consent routes require a bearer token.

CTMS is internet-reachable and previously had NO authentication layer — every
subject/consent/visit/dispense/eligibility route was reachable anonymously with
only Depends(get_db). These assert the GUARD EXISTS (401 without a valid JWT).

Uses a dedicated `noauth_client` that overrides only get_db (NOT require_auth),
so the real guard runs — unlike the shared `client` fixture which bypasses auth
for business-logic tests.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.main import app


@pytest_asyncio.fixture
async def noauth_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db  # real require_auth still runs
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


GUARDED = [
    ("GET", "/api/v1/visits/1"),
    ("PATCH", "/api/v1/visits/1"),
    ("POST", "/api/v1/ip/dispenses"),
    ("POST", "/api/v1/ip/dispenses/1/destroy"),
    ("POST", "/api/v1/subjects/1/consent"),
    ("POST", "/api/v1/studies/1/flag-reconsent"),
    ("POST", "/api/v1/agents/subjects/1/consent-contracts"),
    ("POST", "/api/v1/eligibility-screenings"),
    ("GET", "/api/v1/eligibility-screenings"),
    ("POST", "/api/v1/eligibility-screenings/1/outcome"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("verb,path", GUARDED)
async def test_anonymous_is_rejected(noauth_client, verb: str, path: str) -> None:
    resp = await noauth_client.request(verb, path, json={})
    assert resp.status_code == 401, (
        f"{verb} {path} must require a bearer token, got {resp.status_code}"
    )


@pytest.mark.asyncio
async def test_invalid_token_is_rejected(noauth_client) -> None:
    resp = await noauth_client.get(
        "/api/v1/visits/1", headers={"Authorization": "Bearer not-a-real-jwt"}
    )
    assert resp.status_code == 401, resp.text


@pytest.mark.asyncio
async def test_valid_token_passes_guard(noauth_client) -> None:
    token = jwt.encode(
        {"sub": "u", "roles": ["investigator"]},
        get_settings().secret_key,
        algorithm="HS256",
    )
    resp = await noauth_client.get(
        "/api/v1/visits/1", headers={"Authorization": f"Bearer {token}"}
    )
    # Not 401 (may be 404 for the missing visit) => the guard passed.
    assert resp.status_code != 401, resp.text
