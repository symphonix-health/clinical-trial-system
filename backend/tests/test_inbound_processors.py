"""Direct tests for inbound webhook processors."""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.connectors import inbound_processors


async def _seed_minimal_domain(db: AsyncSession) -> dict[str, Any]:
    study = await crud.create_study(
        db,
        schemas.StudyCreate(
            protocol_number="INBOUND-001",
            title="Inbound processor study",
            phase="I",
            indication="x",
            therapeutic_area="oncology",
            sponsor="Symphonix",
        ),
    )
    site = await crud.create_site(
        db,
        schemas.SiteCreate(
            study_id=study.id,
            site_code="INB-01",
            name="Inbound site",
            organisation_id="org",
            principal_investigator_id="pi",
        ),
    )
    subject = await crud.create_subject(
        db,
        schemas.SubjectCreate(
            study_id=study.id,
            site_id=site.id,
            screening_id="INB-S-001",
        ),
    )
    product = await crud.create_investigational_product(
        db,
        schemas.InvestigationalProductCreate(
            sku="INB-IP-001",
            name="Test IP",
            lot_number="LOT-1",
            expiry_date=dt.date(2027, 1, 1),
            storage_conditions="room temp",
            accountability_unit="tablet",
            quantity_on_hand=100,
            site_id=site.id,
        ),
    )
    env = await crud.create_synthetic_environment(
        db,
        schemas.SyntheticEnvironmentCreate(
            name="Inbound env",
            task_script_json={"steps": ["step1"]},
            synthetic_patient_cohort=[{"age": 50}],
            golden_path_steps=["step1"],
            perturbation_set=[{"type": "none"}],
        ),
    )
    return {"study": study, "site": site, "subject": subject, "product": product, "env": env}


async def test_get_subject_by_external_id_no_identifier(db_session: AsyncSession) -> None:
    subject = await inbound_processors._get_subject_by_external_id(db_session)
    assert subject is None


async def test_process_appointment_confirmed_by_screening_id(db_session: AsyncSession) -> None:
    domain = await _seed_minimal_domain(db_session)
    result = await inbound_processors.process_appointment_confirmed(
        db_session,
        {"screening_id": domain["subject"].screening_id, "scheduled_date": "2026-08-01"},
    )
    assert result["status"] == "processed"
    assert "visit_id" in result


async def test_process_lab_result_subject_not_found(db_session: AsyncSession) -> None:
    result = await inbound_processors.process_lab_result(db_session, {})
    assert result["status"] == "ignored"
    assert result["reason"] == "subject not found"


async def test_process_imaging_result_subject_not_found(db_session: AsyncSession) -> None:
    result = await inbound_processors.process_imaging_result(db_session, {})
    assert result["status"] == "ignored"


async def test_process_dispense_event_product_not_found(db_session: AsyncSession) -> None:
    domain = await _seed_minimal_domain(db_session)
    result = await inbound_processors.process_dispense_event(
        db_session,
        {"subject_id": domain["subject"].id, "product_sku": "MISSING"},
    )
    assert result["status"] == "ignored"
    assert result["reason"] == "product not found"


async def test_process_dispense_event_success(db_session: AsyncSession) -> None:
    domain = await _seed_minimal_domain(db_session)
    result = await inbound_processors.process_dispense_event(
        db_session,
        {
            "subject_id": domain["subject"].id,
            "product_sku": domain["product"].sku,
            "quantity_dispensed": 5,
            "event_id": "disp-direct-001",
        },
    )
    assert result["status"] == "processed"
    assert "dispense_id" in result


async def test_process_agent_task_completed_existing_run(db_session: AsyncSession) -> None:
    domain = await _seed_minimal_domain(db_session)
    run = await crud.create_agent_run(
        db_session,
        schemas.AgentRunCreate(environment_id=domain["env"].id, agent_subject_ids=[1]),
    )
    result = await inbound_processors.process_agent_task_completed(
        db_session,
        {"run_id": run.id, "metrics": {"accuracy": 0.91}, "event_id": "agent-direct-001"},
    )
    assert result["status"] == "processed"
    assert result["run_id"] == run.id


async def test_process_agent_task_completed_run_not_found(db_session: AsyncSession) -> None:
    result = await inbound_processors.process_agent_task_completed(
        db_session, {"run_id": 99999, "metrics": {}}
    )
    assert result["status"] == "ignored"
    assert result["reason"] == "run not found"


async def test_process_agent_escalation_duplicate(db_session: AsyncSession) -> None:
    payload = {"event_id": "esc-direct-dup", "agent_subject_id": 1, "reason": "x"}
    first = await inbound_processors.process_agent_escalation(db_session, payload)
    assert first["status"] == "processed"
    second = await inbound_processors.process_agent_escalation(db_session, payload)
    assert second["status"] == "ignored"


async def test_process_council_synthesis_duplicate(db_session: AsyncSession) -> None:
    payload = {"event_id": "council-direct-dup", "council_id": "c1", "outcome": "ok"}
    first = await inbound_processors.process_council_synthesis(db_session, payload)
    assert first["status"] == "processed"
    second = await inbound_processors.process_council_synthesis(db_session, payload)
    assert second["status"] == "ignored"


async def test_models_persisted_after_processing(db_session: AsyncSession) -> None:
    domain = await _seed_minimal_domain(db_session)
    await inbound_processors.process_agent_escalation(
        db_session,
        {"event_id": "esc-persist-001", "agent_subject_id": 1, "reason": "r", "severity": "low"},
    )
    await inbound_processors.process_council_synthesis(
        db_session,
        {"event_id": "council-persist-001", "council_id": "c1", "outcome": "approved"},
    )
    # All commits happen inside processors; a fresh count confirms persistence.
    result = await db_session.execute(select(func.count(models.AgentEscalation.id)))
    assert result.scalar() >= 1
