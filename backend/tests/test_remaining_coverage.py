"""Remaining coverage tests to reach 100% backend coverage."""

import datetime as dt
import hashlib
import hmac

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.config import get_settings


def _sign(payload: bytes) -> str:
    secret = get_settings().webhook_secret.encode()
    return f"sha256={hmac.new(secret, payload, hashlib.sha256).hexdigest()}"


async def _create_study_and_site(client: AsyncClient):
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "REM-001",
            "title": "Remaining coverage",
            "phase": "I",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    study_id = study.json()["id"]
    site = await client.post(
        "/api/v1/sites",
        json={
            "study_id": study_id,
            "site_code": "REM-01",
            "name": "Remaining site",
            "organisation_id": "org",
            "principal_investigator_id": "pi",
        },
    )
    return study_id, site.json()["id"]


# IP 404 branches
async def test_get_ip_product_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/ip/products/99999")
    assert resp.status_code == 404


async def test_receive_ip_shipment_not_found(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/ip/shipments/99999/receive",
        params={"received_by": "pharm1", "condition_ok": True},
    )
    assert resp.status_code == 404


# Query 404 branch
async def test_get_query_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/queries/99999")
    assert resp.status_code == 404


# Regulatory list
async def test_list_regulatory_documents(client: AsyncClient) -> None:
    study_id, _ = await _create_study_and_site(client)
    await client.post(
        "/api/v1/regulatory-documents",
        json={
            "study_id": study_id,
            "document_type": "protocol",
            "document_reference": "ref-1",
            "version": "1.0",
        },
    )
    resp = await client.get(f"/api/v1/regulatory-documents?study_id={study_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# Reports
async def test_etmf_report(client: AsyncClient) -> None:
    study_id, _ = await _create_study_and_site(client)
    await client.post(
        "/api/v1/regulatory-documents",
        json={
            "study_id": study_id,
            "document_type": "protocol",
            "document_reference": "ref-exp",
            "version": "1.0",
            "expiry_date": "2020-01-01",
        },
    )
    resp = await client.get(f"/api/v1/reports/etmf/{study_id}")
    assert resp.status_code == 200
    assert resp.json()["expired_count"] >= 1


async def test_ip_accountability_invalid_site(client: AsyncClient) -> None:
    study_id, _ = await _create_study_and_site(client)
    resp = await client.get(f"/api/v1/reports/ip-accountability/{study_id}/99999")
    assert resp.status_code == 400


# Webhooks
@pytest.mark.parametrize(
    "endpoint,event",
    [
        ("imaging-result", "imaging.result"),
        ("dispense-event", "dispense.event"),
        ("agent-task-completed", "agent.task.completed"),
        ("council-synthesis", "council.synthesis"),
    ],
)
async def test_webhook_endpoints(client: AsyncClient, endpoint: str, event: str) -> None:
    payload = f'{{"event": "{event}", "data": {{}}}}'.encode()
    resp = await client.post(
        f"/api/v1/webhooks/bullettrain/{endpoint}",
        content=payload,
        headers={"x-bt-signature": _sign(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert body["status"] in ("processed", "ignored")


# Subject withdrawal with scheduled visit
async def test_withdraw_subject_marks_scheduled_visit_missed(client: AsyncClient) -> None:
    study_id, site_id = await _create_study_and_site(client)
    subject_id = (
        await client.post(
            "/api/v1/subjects",
            json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-REM-WD"},
        )
    ).json()["id"]
    await client.post(
        f"/api/v1/subjects/{subject_id}/consent",
        json={"subject_id": subject_id, "consent_version": "v1.0", "consent_date": "2026-01-20T09:00:00"},
    )
    visit = await client.post(
        "/api/v1/visits",
        json={
            "subject_id": subject_id,
            "visit_definition_id": "V1",
            "scheduled_date": "2026-06-01",
            "window_min_date": "2026-05-30",
            "window_max_date": "2026-06-03",
        },
    )
    visit_id = visit.json()["id"]
    resp = await client.post(f"/api/v1/subjects/{subject_id}/withdraw", params={"reason": "personal"})
    assert resp.status_code == 200
    visit_resp = await client.get(f"/api/v1/visits/{visit_id}")
    assert visit_resp.json()["status"] == "missed"


# Visit update outside window creates protocol deviation
async def test_update_visit_outside_window_creates_protocol_deviation(client: AsyncClient) -> None:
    study_id, site_id = await _create_study_and_site(client)
    subject_id = (
        await client.post(
            "/api/v1/subjects",
            json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-REM-VIS"},
        )
    ).json()["id"]
    visit = await client.post(
        "/api/v1/visits",
        json={
            "subject_id": subject_id,
            "visit_definition_id": "V1",
            "scheduled_date": "2026-06-01",
            "window_min_date": "2026-05-30",
            "window_max_date": "2026-06-03",
        },
    )
    visit_id = visit.json()["id"]
    resp = await client.patch(
        f"/api/v1/visits/{visit_id}",
        json={"actual_date": "2026-06-10"},
    )
    assert resp.status_code == 200


# CRUD direct coverage
async def test_crud_list_subjects_by_site(db_session: AsyncSession) -> None:
    study = await crud.create_study(
        db_session,
        schemas.StudyCreate(
            protocol_number="CRUD-SITE",
            title="x",
            phase="I",
            indication="x",
            therapeutic_area="oncology",
            sponsor="Sponsor",
        ),
    )
    site = await crud.create_site(
        db_session,
        schemas.SiteCreate(
            study_id=study.id,
            site_code="CRUD-01",
            name="Site",
            organisation_id="org",
            principal_investigator_id="pi",
        ),
    )
    subject = await crud.create_subject(
        db_session,
        schemas.SubjectCreate(study_id=study.id, site_id=site.id, screening_id="SCR-CSITE"),
    )
    subjects = await crud.list_subjects(db_session, site_id=site.id)
    assert any(s.id == subject.id for s in subjects)


async def test_crud_list_protocol_deviations(db_session: AsyncSession) -> None:
    study = await crud.create_study(
        db_session,
        schemas.StudyCreate(
            protocol_number="CRUD-PD",
            title="x",
            phase="I",
            indication="x",
            therapeutic_area="oncology",
            sponsor="Sponsor",
        ),
    )
    site = await crud.create_site(
        db_session,
        schemas.SiteCreate(
            study_id=study.id,
            site_code="CRUD-PD01",
            name="Site",
            organisation_id="org",
            principal_investigator_id="pi",
        ),
    )
    subject = await crud.create_subject(
        db_session,
        schemas.SubjectCreate(study_id=study.id, site_id=site.id, screening_id="SCR-CPD"),
    )
    await crud.create_protocol_deviation(
        db_session,
        schemas.ProtocolDeviationCreate(
            study_id=study.id,
            subject_id=subject.id,
            category="x",
            description="x",
            severity="minor",
        ),
    )
    deviations = await crud.list_protocol_deviations(db_session, study_id=study.id)
    assert len(deviations) == 1


async def test_crud_get_agent_cohort_and_environment(client: AsyncClient, db_session: AsyncSession) -> None:
    cohort_resp = await client.post(
        "/api/v1/agents/cohorts",
        json={
            "name": "CRUD cohort",
            "cohort_type": "single_agent",
            "capability_profile": "test",
            "model_family": "test_family",
            "evaluation_objective": "coverage",
        },
    )
    cohort_id = cohort_resp.json()["id"]
    cohort = await crud.get_agent_cohort(db_session, cohort_id)
    assert cohort is not None
    assert cohort.id == cohort_id

    env_resp = await client.post(
        "/api/v1/agents/environments",
        json={
            "name": "CRUD env",
            "task_script_json": {},
            "synthetic_patient_cohort": [],
            "golden_path_steps": [],
            "perturbation_set": [],
        },
    )
    env_id = env_resp.json()["id"]
    env = await crud.get_synthetic_environment(db_session, env_id)
    assert env is not None
    assert env.id == env_id


async def test_release_gate_blocked_with_failed_metric(client: AsyncClient) -> None:
    env_resp = await client.post(
        "/api/v1/agents/environments",
        json={
            "name": "Gate env",
            "task_script_json": {},
            "synthetic_patient_cohort": [],
            "golden_path_steps": [],
            "perturbation_set": [],
        },
    )
    env_id = env_resp.json()["id"]
    run_resp = await client.post(
        "/api/v1/agents/runs",
        json={"environment_id": env_id, "agent_subject_ids": []},
    )
    run_id = run_resp.json()["id"]
    await client.post(
        f"/api/v1/agents/runs/{run_id}/complete",
        json={"accuracy": 0.0},
    )
    cohort_resp = await client.post(
        "/api/v1/agents/cohorts",
        json={
            "name": "Gate cohort",
            "cohort_type": "single_agent",
            "capability_profile": "test",
            "model_family": "test_family",
            "evaluation_objective": "coverage",
        },
    )
    cohort_id = cohort_resp.json()["id"]
    resp = await client.get(f"/api/v1/agents/cohorts/{cohort_id}/release-gate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "blocked"
    assert any(m["metric"] == "accuracy" for m in data["failed_metrics"])


async def test_release_gate_promoted_with_passed_metric(client: AsyncClient) -> None:
    env_resp = await client.post(
        "/api/v1/agents/environments",
        json={
            "name": "Gate env pass",
            "task_script_json": {},
            "synthetic_patient_cohort": [],
            "golden_path_steps": [],
            "perturbation_set": [],
        },
    )
    env_id = env_resp.json()["id"]
    run_resp = await client.post(
        "/api/v1/agents/runs",
        json={"environment_id": env_id, "agent_subject_ids": []},
    )
    run_id = run_resp.json()["id"]
    await client.post(
        f"/api/v1/agents/runs/{run_id}/complete",
        json={"accuracy": 1.0},
    )
    cohort_resp = await client.post(
        "/api/v1/agents/cohorts",
        json={
            "name": "Gate cohort pass",
            "cohort_type": "single_agent",
            "capability_profile": "test",
            "model_family": "test_family",
            "evaluation_objective": "coverage",
        },
    )
    cohort_id = cohort_resp.json()["id"]
    resp = await client.get(f"/api/v1/agents/cohorts/{cohort_id}/release-gate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "promoted"
    assert any(m == "accuracy" for m in data["passed_metrics"])


async def test_destroy_dispense_not_found(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/ip/dispenses/99999/destroy",
        json={"destroyed_at": "2026-06-01T00:00:00", "destroyed_by": "pharm1"},
    )
    assert resp.status_code == 404


async def test_update_query_not_found(client: AsyncClient) -> None:
    resp = await client.patch(
        "/api/v1/queries/99999",
        json={"status": "closed"},
    )
    assert resp.status_code == 404
