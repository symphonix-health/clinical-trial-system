"""Health endpoint."""

import datetime as dt

from fastapi import APIRouter

from app import schemas

router = APIRouter()


@router.get("/health", response_model=schemas.HealthOut)
async def health_check() -> schemas.HealthOut:
    return schemas.HealthOut(status="ok", version="0.1.0", timestamp=dt.datetime.utcnow())
