"""Pytest fixtures."""

import asyncio
import os
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth import require_auth
from app.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.seeding.loader import _seed

settings = get_settings()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    test_id = uuid.uuid4().hex[:12]
    db_path = f"ctms_test_{test_id}.db"
    url = f"sqlite+aiosqlite:///./{db_path}"
    engine = create_async_engine(url, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except PermissionError:
        pass


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    TestingSessionLocal = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # Route-auth remediation (2026-08-11): patient routes now require a bearer
    # token via require_auth. Business-logic tests are not auth tests, so bypass
    # the guard with a stub principal; real 401 behaviour is covered by
    # tests/test_route_auth_guards.py (which does NOT use this fixture).
    app.dependency_overrides[require_auth] = lambda: {"sub": "test-user", "roles": ["investigator"]}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded_client(client: AsyncClient, db_engine) -> AsyncClient:
    TestingSessionLocal = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with TestingSessionLocal() as db:
        await _seed(db)
        await db.commit()
    return client
