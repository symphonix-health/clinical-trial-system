"""Inbound webhook endpoints.

All endpoints verify the BulletTrain HMAC signature and then dispatch to a
processor that mutates CTMS domain state. Constitution compliance: CTMS does
not call sibling systems directly from workflow code; outbound side-effects
are queued through ``app.connectors.integration_engine``.
"""

import hashlib
import hmac
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.config import get_settings
from app.connectors import inbound_processors
from app.database import get_db

router = APIRouter(prefix="/webhooks/bullettrain", tags=["webhooks"])


async def _verify_signature(request: Request) -> None:
    settings = get_settings()
    body = await request.body()
    expected = hmac.new(settings.webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    provided = request.headers.get("x-bt-signature", "")
    if not hmac.compare_digest(f"sha256={expected}", provided):
        raise HTTPException(status_code=401, detail="Invalid signature")


@router.post("/appointment-confirmed")
async def appointment_confirmed(
    payload: schemas.WebhookPayload, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    await _verify_signature(request)
    return await inbound_processors.process_appointment_confirmed(db, payload.data)


@router.post("/lab-result")
async def lab_result(
    payload: schemas.WebhookPayload, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    await _verify_signature(request)
    return await inbound_processors.process_lab_result(db, payload.data)


@router.post("/imaging-result")
async def imaging_result(
    payload: schemas.WebhookPayload, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    await _verify_signature(request)
    return await inbound_processors.process_imaging_result(db, payload.data)


@router.post("/dispense-event")
async def dispense_event(
    payload: schemas.WebhookPayload, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    await _verify_signature(request)
    return await inbound_processors.process_dispense_event(db, payload.data)


@router.post("/agent-task-completed")
async def agent_task_completed(
    payload: schemas.WebhookPayload, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    await _verify_signature(request)
    return await inbound_processors.process_agent_task_completed(db, payload.data)


@router.post("/agent-escalation")
async def agent_escalation(
    payload: schemas.WebhookPayload, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    await _verify_signature(request)
    return await inbound_processors.process_agent_escalation(db, payload.data)


@router.post("/council-synthesis")
async def council_synthesis(
    payload: schemas.WebhookPayload, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    await _verify_signature(request)
    return await inbound_processors.process_council_synthesis(db, payload.data)
