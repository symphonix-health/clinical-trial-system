"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.config import get_settings
from app.database import init_db
from app.seeding.loader import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover
    settings = get_settings()
    await init_db()
    await seed_database()
    yield


app = FastAPI(
    title=get_settings().app_name,
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
)

import os

_frontend_port = os.getenv("CTMS_FRONTEND_PORT", "5281")
_frontend_origin = f"http://localhost:{_frontend_port}"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[_frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=get_settings().api_v1_prefix)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "CTMS API", "version": "0.1.0"}
