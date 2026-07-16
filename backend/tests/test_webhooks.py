"""Inbound webhook tests."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import pytest
from httpx import AsyncClient

from app.config import get_settings


def _sign(payload: bytes) -> str:
    secret = get_settings().webhook_secret.encode()
    return f"sha256={hmac.new(secret, payload, hashlib.sha256).hexdigest()}"


def _payload(data: dict[str, Any]) -> bytes:
    return json.dumps({"event": "x", "data": data}).encode()


async def _enrolled_subject(client: AsyncClient) -> dict[str, Any]:
    studies = (await client.get("/api/v1/studies")).json()
    study_id = studies[0]["id"]
    subjects = (await client.get(f"/api/v1/subjects?study_id={study_id}")).json()
    enrolled = [s for s in subjects if s["enrolment_status"] == "enrolled"]
    if not enrolled:
        pytest.skip("no enrolled seeded subject")
    return enrolled[0]


async def test_webhook_invalid_signature(client: AsyncClient) -> None:
    payload = b'{"event": "x", "data": {}}'
    resp = await client.post(
        "/api/v1/webhooks/bullettrain/agent-escalation",
        content=payload,
        headers={"x-bt-signature": "sha256=invalid", "content-type": "application/json"},
    )
    assert resp.status_code == 401


async def test_webhook_appointment_confirmed_processed(seeded_client: AsyncClient) -> None:
    subject = await _enrolled_subject(seeded_client)
    payload = _payload({
        "subject_id": subject["id"],
        "scheduled_date": "2026-07-15",
        "visit_definition_id": "SCREENING",
    })
    resp = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/appointment-confirmed",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "processed"
    assert "visit_id" in body


async def test_webhook_appointment_confirmed_ignored(seeded_client: AsyncClient) -> None:
    payload = _payload({})
    resp = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/appointment-confirmed",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


async def test_webhook_lab_result_processed(seeded_client: AsyncClient) -> None:
    subject = await _enrolled_subject(seeded_client)
    payload = _payload({
        "subject_id": subject["id"],
        "observation_code": "WBC",
        "value": "4.5",
        "source_system": "lis",
    })
    resp = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/lab-result",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "processed"
    assert "query_id" in body


async def test_webhook_lab_result_ignored(seeded_client: AsyncClient) -> None:
    payload = _payload({"observation_code": "WBC"})
    resp = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/lab-result",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


async def test_webhook_imaging_result_processed(seeded_client: AsyncClient) -> None:
    subject = await _enrolled_subject(seeded_client)
    payload = _payload({
        "subject_id": subject["id"],
        "study_instance_uid": "1.2.3.4.5",
        "source_system": "pacs-ris",
    })
    resp = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/imaging-result",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "processed"
    assert "query_id" in body


async def test_webhook_imaging_result_ignored(seeded_client: AsyncClient) -> None:
    payload = _payload({"study_instance_uid": "1.2.3.4.5"})
    resp = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/imaging-result",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


async def test_webhook_dispense_event_processed(seeded_client: AsyncClient) -> None:
    subject = await _enrolled_subject(seeded_client)
    payload = _payload({
        "subject_id": subject["id"],
        "product_sku": "ONCO-IP-001",
        "quantity_dispensed": 2,
        "dispensed_by": "pharmacy-system",
        "event_id": "disp-001",
    })
    resp = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/dispense-event",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "processed"
    assert "dispense_id" in body


async def test_webhook_dispense_event_ignored_subject(seeded_client: AsyncClient) -> None:
    payload = _payload({"product_sku": "ONCO-IP-001"})
    resp = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/dispense-event",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


async def test_webhook_dispense_event_ignored_product(seeded_client: AsyncClient) -> None:
    subject = await _enrolled_subject(seeded_client)
    payload = _payload({
        "subject_id": subject["id"],
        "product_sku": "NONEXISTENT-SKU",
    })
    resp = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/dispense-event",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


async def test_webhook_agent_task_completed_processed(seeded_client: AsyncClient) -> None:
    payload = _payload({
        "environment_id": 1,
        "agent_subject_ids": [1, 2],
        "metrics": {"accuracy": 0.92, "response_rate": 0.88},
        "trace_artifact_url": "http://trace.test/1",
        "event_id": "agent-001",
    })
    resp = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/agent-task-completed",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "processed"
    assert "run_id" in body


async def test_webhook_agent_task_completed_existing_run(seeded_client: AsyncClient) -> None:
    payload = _payload({
        "environment_id": 1,
        "agent_subject_ids": [1],
        "metrics": {},
    })
    resp = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/agent-task-completed",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    run_id = resp.json()["run_id"]

    payload2 = _payload({
        "run_id": run_id,
        "metrics": {"accuracy": 0.99},
    })
    resp2 = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/agent-task-completed",
        content=payload2,
        headers={"x-bt-signature": _sign(payload2), "content-type": "application/json"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "processed"


async def test_webhook_agent_task_completed_run_not_found(seeded_client: AsyncClient) -> None:
    payload = _payload({"run_id": 99999, "metrics": {"accuracy": 0.5}})
    resp = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/agent-task-completed",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


async def test_webhook_agent_escalation_processed(seeded_client: AsyncClient) -> None:
    payload = _payload({
        "event_id": "esc-001",
        "agent_subject_id": 1,
        "reason": "Threshold exceeded",
        "severity": "high",
    })
    resp = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/agent-escalation",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "processed"
    assert "escalation_id" in body


async def test_webhook_agent_escalation_duplicate(seeded_client: AsyncClient) -> None:
    payload = _payload({"event_id": "esc-dup", "agent_subject_id": 1, "reason": "x"})
    await seeded_client.post(
        "/api/v1/webhooks/bullettrain/agent-escalation",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    resp2 = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/agent-escalation",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "ignored"


async def test_webhook_council_synthesis_processed(seeded_client: AsyncClient) -> None:
    payload = _payload({
        "event_id": "council-001",
        "council_id": "council-123",
        "outcome": "approved",
        "ballot_summary": {"yes": 3, "no": 0},
    })
    resp = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/council-synthesis",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "processed"
    assert "trial_id" in body


async def test_webhook_council_synthesis_duplicate(seeded_client: AsyncClient) -> None:
    payload = _payload({
        "event_id": "council-dup",
        "council_id": "council-123",
        "outcome": "approved",
    })
    await seeded_client.post(
        "/api/v1/webhooks/bullettrain/council-synthesis",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    resp2 = await seeded_client.post(
        "/api/v1/webhooks/bullettrain/council-synthesis",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "ignored"
