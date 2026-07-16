"""Tests for the hub-mediated integration dispatch engine."""

from __future__ import annotations

import os
from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.connectors import integration_engine


class _FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse | None = None, exc: Exception | None = None) -> None:
        self.response = response
        self.exc = exc
        self.closed = False
        self.posted: dict[str, Any] | None = None

    async def post(self, target: str, *, json: dict[str, Any], headers: dict[str, str]) -> _FakeResponse:
        self.posted = {"target": target, "json": json, "headers": headers}
        if self.exc:
            raise self.exc
        return self.response or _FakeResponse(200)

    async def aclose(self) -> None:
        self.closed = True


async def test_dispatch_via_hub_persists_and_skips_network_when_hub_unset(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CTMS_CASCADE_HUB_URL", raising=False)

    dispatch = await integration_engine.dispatch_via_hub(
        db_session,
        event_id="ctms-test-1",
        route="ctms.subject.enrolled",
        receiver="citizen-portal",
        payload={"subject_id": 1},
    )

    assert isinstance(dispatch, models.IntegrationDispatch)
    assert dispatch.event_id == "ctms-test-1"
    assert dispatch.status == "pending"
    assert dispatch.receiver == "citizen-portal"


async def test_dispatch_via_hub_delivers_when_hub_set(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CTMS_CASCADE_HUB_URL", "http://hub.test")
    fake_client = _FakeAsyncClient(response=_FakeResponse(202))

    dispatch = await integration_engine.dispatch_via_hub(
        db_session,
        event_id="ctms-test-2",
        route="ctms.visit.scheduled",
        receiver="appointment-system",
        payload={"visit_id": 1},
        http_client=fake_client,
    )

    assert dispatch.status == "sent"
    assert fake_client.posted is not None
    assert fake_client.posted["target"] == "http://hub.test/v1/connectors/appointment_system/exchange"
    assert fake_client.posted["json"]["operation"] == "notify"
    assert fake_client.posted["json"]["resource_type"] == "VisitScheduled"
    assert fake_client.posted["json"]["payload"]["event_type"] == "ctms.visit.scheduled"
    assert fake_client.posted["json"]["payload"]["payload"]["visit_id"] == 1
    assert fake_client.posted["headers"]["Authorization"] == "Bearer internal-hub-token"


async def test_dispatch_via_hub_owns_and_closes_client(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CTMS_CASCADE_HUB_URL", "http://hub.test")
    fake_client = _FakeAsyncClient(response=_FakeResponse(200))

    class _Factory:
        def __call__(self, *, timeout: float) -> _FakeAsyncClient:
            return fake_client

    monkeypatch.setattr(integration_engine.httpx, "AsyncClient", _Factory())

    dispatch = await integration_engine.dispatch_via_hub(
        db_session,
        event_id="ctms-test-3",
        route="ctms.adverse_event.reported",
        receiver="analytics-bi",
        payload={"ae_id": 1},
    )

    assert dispatch.status == "sent"
    assert fake_client.closed


async def test_dispatch_via_hub_logs_http_error(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("CTMS_CASCADE_HUB_URL", "http://hub.test")
    fake_client = _FakeAsyncClient(exc=httpx.ConnectError("unreachable"))

    dispatch = await integration_engine.dispatch_via_hub(
        db_session,
        event_id="ctms-test-4",
        route="ctms.ip.dispensed",
        receiver="pharmacy-system",
        payload={"dispense_id": 1},
        http_client=fake_client,
    )

    assert dispatch.status == "pending"
    assert any("cascade hub delivery error" in r.message for r in caplog.records)


async def test_dispatch_via_hub_keeps_pending_on_non_2xx(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CTMS_CASCADE_HUB_URL", "http://hub.test")
    fake_client = _FakeAsyncClient(response=_FakeResponse(500))

    dispatch = await integration_engine.dispatch_via_hub(
        db_session,
        event_id="ctms-test-5",
        route="ctms.agent.run_completed",
        receiver="global-agent-registry",
        payload={"run_id": 1},
        http_client=fake_client,
    )

    assert dispatch.status == "pending"


@pytest.mark.parametrize(
    "receiver,route,resource_type,connector_name",
    [
        ("citizen-portal", "ctms.subject.enrolled", "SubjectEnrolled", "citizen_portal"),
        ("appointment-system", "ctms.visit.scheduled", "VisitScheduled", "appointment_system"),
        ("analytics-bi", "ctms.adverse_event.reported", "AdverseEventReported", "analytics_bi"),
        ("pharmacy-system", "ctms.ip.dispensed", "IpDispensed", "pharmacy_system"),
        ("global-agent-registry", "ctms.agent.run_completed", "AgentRunCompleted", "global_agent_registry"),
    ],
)
async def test_dispatch_via_hub_targets_correct_connector(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    receiver: str,
    route: str,
    resource_type: str,
    connector_name: str,
) -> None:
    monkeypatch.setenv("CTMS_CASCADE_HUB_URL", "http://hub.test")
    fake_client = _FakeAsyncClient(response=_FakeResponse(200))

    await integration_engine.dispatch_via_hub(
        db_session,
        event_id=f"ctms-test-{connector_name}",
        route=route,
        receiver=receiver,
        payload={"key": "value"},
        http_client=fake_client,
    )

    assert fake_client.posted is not None
    assert fake_client.posted["target"] == f"http://hub.test/v1/connectors/{connector_name}/exchange"
    assert fake_client.posted["json"]["resource_type"] == resource_type
    assert fake_client.posted["json"]["payload"]["event_type"] == route


async def test_dispatch_via_hub_rejects_unknown_resource_type(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CTMS_CASCADE_HUB_URL", "http://hub.test")
    fake_client = _FakeAsyncClient(response=_FakeResponse(200))

    with pytest.raises(integration_engine.IntegrationError, match="no resource_type mapping"):
        await integration_engine.dispatch_via_hub(
            db_session,
            event_id="ctms-test-unknown-route",
            route="ctms.unknown.event",
            receiver="citizen-portal",
            payload={},
            http_client=fake_client,
        )


async def test_dispatch_via_hub_rejects_unmapped_receiver(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CTMS_CASCADE_HUB_URL", "http://hub.test")
    fake_client = _FakeAsyncClient(response=_FakeResponse(200))
    override = integration_engine.ConnectorPolicy(
        allowed_receivers=frozenset({"citizen-portal", "unmapped-receiver"}),
    )

    with pytest.raises(integration_engine.IntegrationError, match="no connector mapping"):
        await integration_engine.dispatch_via_hub(
            db_session,
            event_id="ctms-test-unmapped",
            route="ctms.subject.enrolled",
            receiver="unmapped-receiver",
            payload={},
            policy_override=override,
            http_client=fake_client,
        )


async def test_dispatch_via_hub_rejects_unsupported_route(db_session: AsyncSession) -> None:
    with pytest.raises(integration_engine.IntegrationError, match="unsupported route format"):
        await integration_engine.dispatch_via_hub(
            db_session,
            event_id="ctms-test-6",
            route="bad.route",
            receiver="citizen-portal",
            payload={},
        )


async def test_dispatch_via_hub_rejects_unauthorised_receiver(db_session: AsyncSession) -> None:
    with pytest.raises(integration_engine.IntegrationError, match="integration security policy"):
        await integration_engine.dispatch_via_hub(
            db_session,
            event_id="ctms-test-7",
            route="ctms.subject.enrolled",
            receiver="forbidden-system",
            payload={},
        )


async def test_dispatch_via_hub_rejects_empty_receiver(db_session: AsyncSession) -> None:
    with pytest.raises(integration_engine.IntegrationError, match="integration security policy"):
        await integration_engine.dispatch_via_hub(
            db_session,
            event_id="ctms-test-8",
            route="ctms.subject.enrolled",
            receiver="   ",
            payload={},
        )


async def test_dispatch_via_hub_rejects_invalid_envelope(db_session: AsyncSession) -> None:
    with pytest.raises(integration_engine.IntegrationError, match="invalid dispatch envelope"):
        await integration_engine.dispatch_via_hub(
            db_session,
            event_id="ab",
            route="ctms.subject.enrolled",
            receiver="citizen-portal",
            payload={},
        )


async def test_dispatch_via_hub_rejects_tenant_mismatch(db_session: AsyncSession) -> None:
    with pytest.raises(integration_engine.IntegrationError, match="integration tenant policy"):
        await integration_engine.dispatch_via_hub(
            db_session,
            event_id="ctms-test-9",
            route="ctms.subject.enrolled",
            receiver="citizen-portal",
            payload={},
            tenant_id="OTHER-TENANT",
        )


async def test_notify_subject_enrolled(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CTMS_CASCADE_HUB_URL", raising=False)
    dispatch = await integration_engine.notify_subject_enrolled(
        db_session,
        subject_id=1,
        study_id=1,
        site_id=1,
        subject_number="S001-0001",
    )
    assert dispatch.receiver == "citizen-portal"
    assert dispatch.route == "ctms.subject.enrolled"
    assert dispatch.payload["subject_number"] == "S001-0001"


async def test_notify_visit_scheduled(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CTMS_CASCADE_HUB_URL", raising=False)
    dispatch = await integration_engine.notify_visit_scheduled(
        db_session,
        visit_id=2,
        subject_id=1,
        scheduled_date="2026-07-01",
    )
    assert dispatch.receiver == "appointment-system"
    assert dispatch.route == "ctms.visit.scheduled"


async def test_notify_adverse_event(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CTMS_CASCADE_HUB_URL", raising=False)
    dispatch = await integration_engine.notify_adverse_event(
        db_session,
        ae_id=3,
        study_id=1,
        subject_id=1,
        seriousness="serious",
    )
    assert dispatch.receiver == "analytics-bi"
    assert dispatch.route == "ctms.adverse_event.reported"


async def test_notify_ip_dispensed(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CTMS_CASCADE_HUB_URL", raising=False)
    dispatch = await integration_engine.notify_ip_dispensed(
        db_session,
        dispense_id=4,
        subject_id=1,
        product_sku="ONCO-IP-001",
        quantity_dispensed=30,
    )
    assert dispatch.receiver == "pharmacy-system"
    assert dispatch.route == "ctms.ip.dispensed"
    assert dispatch.payload["product_sku"] == "ONCO-IP-001"


async def test_notify_agent_run_completed(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CTMS_CASCADE_HUB_URL", raising=False)
    dispatch = await integration_engine.notify_agent_run_completed(
        db_session,
        run_id=5,
        agent_subject_ids=[1, 2],
        metrics_snapshot={"accuracy": 0.95},
    )
    assert dispatch.receiver == "global-agent-registry"
    assert dispatch.route == "ctms.agent.run_completed"
