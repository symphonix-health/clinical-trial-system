"""Inbound webhook endpoints."""

import hashlib
import hmac
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.config import get_settings
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
async def appointment_confirmed(payload: schemas.WebhookPayload, request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await _verify_signature(request)
    return {"status": "received", "event": payload.event}


@router.post("/lab-result")
async def lab_result(payload: schemas.WebhookPayload, request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await _verify_signature(request)
    return {"status": "received", "event": payload.event}


@router.post("/imaging-result")
async def imaging_result(payload: schemas.WebhookPayload, request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await _verify_signature(request)
    return {"status": "received", "event": payload.event}


@router.post("/dispense-event")
async def dispense_event(payload: schemas.WebhookPayload, request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await _verify_signature(request)
    return {"status": "received", "event": payload.event}


@router.post("/agent-task-completed")
async def agent_task_completed(payload: schemas.WebhookPayload, request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await _verify_signature(request)
    return {"status": "received", "event": payload.event}


@router.post("/agent-escalation")
async def agent_escalation(payload: schemas.WebhookPayload, request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await _verify_signature(request)
    return {"status": "received", "event": payload.event}


@router.post("/council-synthesis")
async def council_synthesis(payload: schemas.WebhookPayload, request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await _verify_signature(request)
    return {"status": "received", "event": payload.event}
