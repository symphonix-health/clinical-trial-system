"""Inbound webhook event processors.

Each processor turns a BulletTrain-routed sibling event into CTMS domain
state. Processors are idempotent where an ``event_id`` is supplied: a duplicate
event_id is ignored for events that own a dedicated record
(AgentEscalation, CouncilTrial).
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.connectors import integration_engine


async def _get_subject_by_external_id(
    db: AsyncSession, subject_id: int | None = None, screening_id: str | None = None
) -> models.Subject | None:
    if subject_id is not None:
        return await crud.get_subject(db, subject_id)
    if screening_id:
        result = await db.execute(
            select(models.Subject).where(models.Subject.screening_id == screening_id)
        )
        return result.scalar_one_or_none()
    return None


async def _get_product_by_sku(db: AsyncSession, sku: str) -> models.InvestigationalProduct | None:
    result = await db.execute(
        select(models.InvestigationalProduct).where(models.InvestigationalProduct.sku == sku)
    )
    return result.scalar_one_or_none()


async def process_appointment_confirmed(
    db: AsyncSession, payload: dict[str, Any]
) -> dict[str, Any]:
    """Create or confirm a subject visit from an appointment-system event."""

    subject = await _get_subject_by_external_id(
        db,
        subject_id=payload.get("subject_id"),
        screening_id=payload.get("screening_id"),
    )
    if not subject:
        return {"status": "ignored", "reason": "subject not found"}

    scheduled_date = dt.datetime.fromisoformat(payload["scheduled_date"]).date()
    visit = await crud.create_visit(
        db,
        schemas.SubjectVisitCreate(
            subject_id=subject.id,
            visit_definition_id=payload.get("visit_definition_id", "EXTERNAL"),
            scheduled_date=scheduled_date,
            window_min_date=payload.get("window_min_date") or scheduled_date,
            window_max_date=payload.get("window_max_date") or scheduled_date,
        ),
    )
    return {"status": "processed", "visit_id": visit.id}


async def process_lab_result(db: AsyncSession, payload: dict[str, Any]) -> dict[str, Any]:
    """Create a data-clarification query for a lab result from lis."""

    subject = await _get_subject_by_external_id(
        db,
        subject_id=payload.get("subject_id"),
        screening_id=payload.get("screening_id"),
    )
    if not subject:
        return {"status": "ignored", "reason": "subject not found"}

    query = await crud.create_query(
        db,
        schemas.QueryCreate(
            study_id=subject.study_id,
            subject_id=subject.id,
            raised_by=payload.get("source_system", "lis"),
            assigned_to="crc_1",
            description=f"Lab result {payload.get('observation_code')} received: {payload.get('value')}",
            linked_resource=f"Subject:{subject.id}",
        ),
    )
    return {"status": "processed", "query_id": query.id}


async def process_imaging_result(db: AsyncSession, payload: dict[str, Any]) -> dict[str, Any]:
    """Create a data-clarification query for an imaging result from pacs-ris."""

    subject = await _get_subject_by_external_id(
        db,
        subject_id=payload.get("subject_id"),
        screening_id=payload.get("screening_id"),
    )
    if not subject:
        return {"status": "ignored", "reason": "subject not found"}

    query = await crud.create_query(
        db,
        schemas.QueryCreate(
            study_id=subject.study_id,
            subject_id=subject.id,
            raised_by=payload.get("source_system", "pacs-ris"),
            assigned_to="crc_1",
            description=f"Imaging result {payload.get('study_instance_uid')} received",
            linked_resource=f"Subject:{subject.id}",
        ),
    )
    return {"status": "processed", "query_id": query.id}


async def process_dispense_event(db: AsyncSession, payload: dict[str, Any]) -> dict[str, Any]:
    """Record an IP dispense event from pharmacy-system / eps."""

    subject = await _get_subject_by_external_id(
        db,
        subject_id=payload.get("subject_id"),
        screening_id=payload.get("screening_id"),
    )
    if not subject:
        return {"status": "ignored", "reason": "subject not found"}

    product = await _get_product_by_sku(db, payload.get("product_sku", ""))
    if not product:
        return {"status": "ignored", "reason": "product not found"}

    dispense = await crud.create_ip_dispense(
        db,
        schemas.IpDispenseCreate(
            subject_id=subject.id,
            product_id=product.id,
            visit_id=payload.get("visit_id"),
            quantity_dispensed=payload.get("quantity_dispensed", 1),
            quantity_returned=0,
            dispensed_by=payload.get("dispensed_by", "pharmacy-system"),
        ),
    )

    await integration_engine.notify_ip_dispensed(
        db,
        dispense_id=dispense.id,
        subject_id=subject.id,
        product_sku=product.sku,
        quantity_dispensed=dispense.quantity_dispensed,
        correlation_id=payload.get("event_id"),
    )

    return {"status": "processed", "dispense_id": dispense.id}


async def process_agent_task_completed(
    db: AsyncSession, payload: dict[str, Any]
) -> dict[str, Any]:
    """Record an agent arena run completion from nexus-a2a-protocol."""

    run_id = payload.get("run_id")
    if run_id is None:
        run = await crud.create_agent_run(
            db,
            schemas.AgentRunCreate(
                environment_id=payload.get("environment_id", 1),
                agent_subject_ids=payload.get("agent_subject_ids", []),
            ),
        )
        run_id = run.id
    else:
        run = await crud.get_agent_run(db, run_id)
        if not run:
            return {"status": "ignored", "reason": "run not found"}

    metrics = payload.get("metrics", {})
    completed = await crud.complete_agent_run(
        db,
        run,
        metrics=metrics,
        trace_url=payload.get("trace_artifact_url"),
    )

    await integration_engine.notify_agent_run_completed(
        db,
        run_id=completed.id,
        agent_subject_ids=completed.agent_subject_ids,
        metrics_snapshot=metrics,
        correlation_id=payload.get("event_id"),
    )

    return {"status": "processed", "run_id": completed.id}


async def process_agent_escalation(
    db: AsyncSession, payload: dict[str, Any]
) -> dict[str, Any]:
    """Record an agent safety escalation from nexus-a2a-protocol / signalbox-mcp."""

    event_id = payload.get("event_id")
    if event_id:
        existing = await db.execute(
            select(models.AgentEscalation).where(models.AgentEscalation.event_id == event_id)
        )
        if existing.scalar_one_or_none():
            return {"status": "ignored", "reason": "duplicate event_id"}

    escalation = models.AgentEscalation(
        event_id=event_id or "unknown",
        agent_subject_id=payload.get("agent_subject_id", 0),
        reason=payload.get("reason", ""),
        severity=payload.get("severity", "medium"),
    )
    db.add(escalation)
    await db.commit()
    await db.refresh(escalation)
    return {"status": "processed", "escalation_id": escalation.id}


async def process_council_synthesis(
    db: AsyncSession, payload: dict[str, Any]
) -> dict[str, Any]:
    """Record a council deliberation outcome from nexus-a2a-protocol."""

    event_id = payload.get("event_id")
    if event_id:
        existing = await db.execute(
            select(models.CouncilTrial).where(models.CouncilTrial.event_id == event_id)
        )
        if existing.scalar_one_or_none():
            return {"status": "ignored", "reason": "duplicate event_id"}

    trial = models.CouncilTrial(
        event_id=event_id or "unknown",
        council_id=payload.get("council_id", ""),
        outcome=payload.get("outcome", ""),
        ballot_summary=payload.get("ballot_summary", {}),
    )
    db.add(trial)
    await db.commit()
    await db.refresh(trial)
    return {"status": "processed", "trial_id": trial.id}
