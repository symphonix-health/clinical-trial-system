"""Inbound webhook tests."""

import hashlib
import hmac

from httpx import AsyncClient

from app.config import get_settings


def _sign(payload: bytes) -> str:
    secret = get_settings().webhook_secret.encode()
    return f"sha256={hmac.new(secret, payload, hashlib.sha256).hexdigest()}"


async def test_webhook_appointment_confirmed(client: AsyncClient) -> None:
    payload = b'{"event": "appointment.confirmed", "data": {}}'
    resp = await client.post(
        "/api/v1/webhooks/bullettrain/appointment-confirmed",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "received"


async def test_webhook_invalid_signature(client: AsyncClient) -> None:
    payload = b'{"event": "x", "data": {}}'
    resp = await client.post(
        "/api/v1/webhooks/bullettrain/agent-escalation",
        content=payload,
        headers={"x-bt-signature": "sha256=invalid", "content-type": "application/json"},
    )
    assert resp.status_code == 401


async def test_webhook_lab_result(client: AsyncClient) -> None:
    payload = b'{"event": "lab.result", "data": {"value": 1.2}}'
    resp = await client.post(
        "/api/v1/webhooks/bullettrain/lab-result",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
