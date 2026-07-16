"""Hub-mediated integration dispatch for CTMS.

Constitution compliance (BulletTrain Integration Constitution / ADR-004):
  * This module is the ONLY place that performs outbound HTTP to sibling
    systems for CTMS-driven cascades.
  * CTMS workflow code calls these helpers; the helpers route through the
    BulletTrain api_gateway connector hub
    (``/v1/connectors/{connector_name}/exchange``), never dialling a receiver
    directly.
  * If ``CTMS_CASCADE_HUB_URL`` is unset, the dispatch is queued locally in
    ``IntegrationDispatch`` and no network call is attempted. This keeps unit
    tests hermetic and production behaviour unchanged when the hub is not
    configured.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models

logger = logging.getLogger("ctms.integration")


class IntegrationError(RuntimeError):
    """Normalised connector boundary error."""


class DispatchSchema(BaseModel):
    """Validated outbound dispatch envelope."""

    event_id: str = Field(min_length=3)
    route: str = Field(pattern=r"^ctms\.")
    receiver: str = Field(min_length=2)
    payload: dict[str, Any]
    tenant_id: str = Field(default="SYMPHONIX-DEFAULT", min_length=3)
    source_system: str = Field(default="clinical-trial-system", min_length=2)
    correlation_id: str | None = Field(default=None, max_length=64)


# Map receiver name -> BulletTrain connector manifest name. The hub selects the
# target sibling connector by this name and then matches the resource_type to an
# exchange route in that connector's manifest.
_RECEIVER_CONNECTOR_MAP: dict[str, str] = {
    "citizen-portal": "citizen_portal",
    "appointment-system": "appointment_system",
    "analytics-bi": "analytics_bi",
    "pharmacy-system": "pharmacy_system",
    "global-agent-registry": "global_agent_registry",
}

# Map CTMS dotted route -> exchange route resource_type expected by the target
# sibling connector manifest.
_ROUTE_RESOURCE_TYPE_MAP: dict[str, str] = {
    "ctms.subject.enrolled": "SubjectEnrolled",
    "ctms.visit.scheduled": "VisitScheduled",
    "ctms.adverse_event.reported": "AdverseEventReported",
    "ctms.ip.dispensed": "IpDispensed",
    "ctms.agent.run_completed": "AgentRunCompleted",
}


def _hub_token() -> str:
    """Resolve the hub bearer token from env, with a dev fallback."""

    return os.environ.get("CTMS_HUB_API_TOKEN", "internal-hub-token").strip()


@dataclass(frozen=True)
class ConnectorPolicy:
    """Security and routing policy for outbound dispatches."""

    max_attempts: int = 3
    timeout_seconds: float = 5.0
    required_token: str = _hub_token()
    allowed_receivers: frozenset[str] = frozenset(_RECEIVER_CONNECTOR_MAP)
    tenant_id: str = "SYMPHONIX-DEFAULT"


def _connector_name(receiver: str) -> str:
    """Resolve a receiver to its BulletTrain connector manifest name."""

    name = _RECEIVER_CONNECTOR_MAP.get(receiver)
    if not name:
        raise IntegrationError(f"no connector mapping for receiver {receiver!r}")
    return name


def _resource_type(route: str) -> str:
    """Resolve a CTMS dotted route to a connector exchange resource_type."""

    resource_type = _ROUTE_RESOURCE_TYPE_MAP.get(route)
    if not resource_type:
        raise IntegrationError(f"no resource_type mapping for route {route!r}")
    return resource_type


def _authorise_receiver(receiver: str, policy: ConnectorPolicy) -> None:
    """Reject disallowed or empty receivers."""

    token = policy.required_token
    if not token or receiver.strip() == "" or receiver not in policy.allowed_receivers:
        raise IntegrationError("integration security policy rejected dispatch")


def _check_tenant(validated: DispatchSchema, policy: ConnectorPolicy) -> None:
    """Reject tenant mismatches."""

    if validated.tenant_id != policy.tenant_id:
        raise IntegrationError("integration tenant policy rejected dispatch")


def _normalise_route(route: str) -> str:
    """Validate and return a CTMS dotted route."""

    if route.startswith("ctms."):
        return route
    raise IntegrationError(f"unsupported route format: {route}")


async def _deliver_via_cascade_hub(
    dispatch: models.IntegrationDispatch,
    validated: DispatchSchema,
    *,
    correlation_id: str,
    active_policy: ConnectorPolicy,
    http_client: httpx.AsyncClient | None = None,
) -> None:
    """Best-effort delivery to the BulletTrain connector hub.

    On a 2xx response, mark ``dispatch.status`` as ``sent``. Transport errors
    are logged but not raised so the local queued row remains the only effect.
    """

    hub = os.environ.get("CTMS_CASCADE_HUB_URL", "").strip()
    if not hub:
        return

    connector_name = _connector_name(validated.receiver)
    resource_type = _resource_type(validated.route)

    client = http_client
    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=active_policy.timeout_seconds)

    try:
        # Canonical HubExchangeRequest accepted by
        # services/api_gateway/connector_hub.py. The hub resolves the named
        # connector manifest, selects the exchange route by resource_type,
        # HMAC-signs the payload, and delivers to the receiver's webhook.
        event = {
            "event_id": validated.event_id,
            "event_type": validated.route,
            "source_system": validated.source_system,
            "correlation_id": correlation_id,
            "payload": validated.payload,
        }
        exchange_request = {
            "tenant_id": validated.tenant_id,
            "actor_id": validated.source_system,
            "correlation_id": correlation_id,
            "operation": "notify",
            "resource_type": resource_type,
            "purpose_of_use": "treatment",
            "source_system": validated.source_system,
            "payload": event,
        }
        target = hub.rstrip("/") + f"/v1/connectors/{connector_name}/exchange"
        resp = await client.post(
            target,
            json=exchange_request,
            headers={
                "X-Correlation-Id": correlation_id,
                "Authorization": f"Bearer {active_policy.required_token}",
            },
        )
        if 200 <= resp.status_code < 300:
            dispatch.status = "sent"
    except httpx.HTTPError as exc:
        logger.warning("ctms cascade hub delivery error: %s", exc)
    finally:
        if owns_client:
            await client.aclose()


policy = ConnectorPolicy()


async def dispatch_via_hub(
    session: AsyncSession,
    *,
    event_id: str,
    route: str,
    receiver: str,
    payload: dict[str, Any],
    tenant_id: str = "SYMPHONIX-DEFAULT",
    source_system: str = "clinical-trial-system",
    correlation_id: str | None = None,
    policy_override: ConnectorPolicy | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> models.IntegrationDispatch:
    """Queue and best-effort deliver an outbound CTMS integration event.

    The dispatch is always persisted in ``IntegrationDispatch``. If
    ``CTMS_CASCADE_HUB_URL`` is set, a canonical ``HubExchangeRequest`` is
    forwarded to the BulletTrain api_gateway connector hub
    (``/v1/connectors/{connector_name}/exchange``); otherwise the row remains
    pending.
    """

    active_policy = policy_override or policy
    _authorise_receiver(receiver, active_policy)

    normalised_route = _normalise_route(route)

    try:
        validated = DispatchSchema(
            event_id=event_id,
            route=normalised_route,
            receiver=receiver,
            payload=payload,
            tenant_id=tenant_id,
            source_system=source_system,
            correlation_id=correlation_id,
        )
    except ValidationError as exc:
        raise IntegrationError(f"invalid dispatch envelope: {exc}") from exc

    _check_tenant(validated, active_policy)

    dispatch = models.IntegrationDispatch(
        event_id=validated.event_id,
        route=validated.route,
        receiver=validated.receiver,
        payload=validated.payload,
        status="pending",
        source_system=validated.source_system,
        tenant_id=validated.tenant_id,
        correlation_id=correlation_id or validated.event_id,
    )
    session.add(dispatch)
    await session.flush()

    await _deliver_via_cascade_hub(
        dispatch,
        validated,
        correlation_id=correlation_id or validated.event_id,
        active_policy=active_policy,
        http_client=http_client,
    )

    await session.commit()
    return dispatch


# Convenience helpers for CTMS workflow code


async def notify_subject_enrolled(
    session: AsyncSession,
    *,
    subject_id: int,
    study_id: int,
    site_id: int,
    subject_number: str,
    correlation_id: str | None = None,
) -> models.IntegrationDispatch:
    """Notify siblings that a subject has enrolled."""

    return await dispatch_via_hub(
        session,
        event_id=f"ctms-subject-enrolled-{subject_id}",
        route="ctms.subject.enrolled",
        receiver="citizen-portal",
        payload={
            "subject_id": subject_id,
            "study_id": study_id,
            "site_id": site_id,
            "subject_number": subject_number,
        },
        correlation_id=correlation_id,
    )


async def notify_visit_scheduled(
    session: AsyncSession,
    *,
    visit_id: int,
    subject_id: int,
    scheduled_date: str,
    correlation_id: str | None = None,
) -> models.IntegrationDispatch:
    """Notify appointment-system that a visit has been scheduled."""

    return await dispatch_via_hub(
        session,
        event_id=f"ctms-visit-scheduled-{visit_id}",
        route="ctms.visit.scheduled",
        receiver="appointment-system",
        payload={
            "visit_id": visit_id,
            "subject_id": subject_id,
            "scheduled_date": scheduled_date,
        },
        correlation_id=correlation_id,
    )


async def notify_adverse_event(
    session: AsyncSession,
    *,
    ae_id: int,
    study_id: int,
    subject_id: int,
    seriousness: str,
    correlation_id: str | None = None,
) -> models.IntegrationDispatch:
    """Notify analytics-bi and triage-api of a reported adverse event."""

    return await dispatch_via_hub(
        session,
        event_id=f"ctms-ae-{ae_id}",
        route="ctms.adverse_event.reported",
        receiver="analytics-bi",
        payload={
            "ae_id": ae_id,
            "study_id": study_id,
            "subject_id": subject_id,
            "seriousness": seriousness,
        },
        correlation_id=correlation_id,
    )


async def notify_ip_dispensed(
    session: AsyncSession,
    *,
    dispense_id: int,
    subject_id: int,
    product_sku: str,
    quantity_dispensed: int,
    correlation_id: str | None = None,
) -> models.IntegrationDispatch:
    """Notify pharmacy-system and eps of an IP dispense event."""

    return await dispatch_via_hub(
        session,
        event_id=f"ctms-ip-dispense-{dispense_id}",
        route="ctms.ip.dispensed",
        receiver="pharmacy-system",
        payload={
            "dispense_id": dispense_id,
            "subject_id": subject_id,
            "product_sku": product_sku,
            "quantity_dispensed": quantity_dispensed,
        },
        correlation_id=correlation_id,
    )


async def notify_agent_run_completed(
    session: AsyncSession,
    *,
    run_id: int,
    agent_subject_ids: list[int],
    metrics_snapshot: dict[str, Any],
    correlation_id: str | None = None,
) -> models.IntegrationDispatch:
    """Notify global-agent-registry of a completed agent arena run."""

    return await dispatch_via_hub(
        session,
        event_id=f"ctms-agent-run-{run_id}",
        route="ctms.agent.run_completed",
        receiver="global-agent-registry",
        payload={
            "run_id": run_id,
            "agent_subject_ids": agent_subject_ids,
            "metrics_snapshot": metrics_snapshot,
        },
        correlation_id=correlation_id,
    )
