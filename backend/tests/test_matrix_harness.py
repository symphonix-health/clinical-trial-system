"""CAID 14-column scenario matrix harness for CTMS."""

from __future__ import annotations

import json
import operator
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient

MATRIX_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "harness"
    / "reduced_json_matrices"
    / "ctms_matrix.14col.json"
)

REQUIRED_COLUMNS = {
    "use_case_id",
    "component",
    "scenario",
    "test_type",
    "priority",
    "expected_outcomes",
    "preconditions",
    "test_data",
    "validation_rules",
    "dependencies",
    "tags",
    "estimated_duration",
    "automation_status",
    "notes",
}


def _load_matrix() -> dict[str, Any]:
    with MATRIX_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _validate_rule(rule: str, response: Any, request_data: dict[str, Any]) -> bool:
    """Evaluate a simple validation rule against a response."""
    ctx: dict[str, Any] = {
        "response": response,
        "data": request_data,
        "operator": operator,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "set": set,
        "true": True,
        "false": False,
        "null": None,
    }
    try:
        return bool(eval(rule, {"__builtins__": {}}, ctx))  # noqa: S307
    except Exception:
        return False


@pytest.fixture(scope="session")
def matrix() -> dict[str, Any]:
    return _load_matrix()


def test_matrix_schema(matrix: dict[str, Any]) -> None:
    assert "metadata" in matrix
    assert "test_cases" in matrix
    for case in matrix["test_cases"]:
        missing = REQUIRED_COLUMNS - set(case.keys())
        assert not missing, f"{case.get('use_case_id', '?')} missing {missing}"
        assert case["test_type"] in {"positive", "negative", "edge"}
        assert case["priority"] in {"high", "medium", "low"}
        assert case["automation_status"] in {"automated", "manual", "planned"}
        assert isinstance(case["expected_outcomes"], list)
        assert isinstance(case["validation_rules"], list)


async def _create_study(client: AsyncClient, protocol_number: str) -> int:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": protocol_number,
            "title": "Matrix study",
            "phase": "II",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    assert study.status_code == 200
    return study.json()["id"]


async def _approve_study(client: AsyncClient, study_id: int) -> None:
    resp = await client.post(f"/api/v1/studies/{study_id}/approve?version_number=1.0")
    assert resp.status_code == 200


async def _create_site(client: AsyncClient, study_id: int, site_code: str) -> int:
    site = await client.post(
        "/api/v1/sites",
        json={
            "study_id": study_id,
            "site_code": site_code,
            "name": "Matrix site",
            "organisation_id": "org",
            "principal_investigator_id": "pi",
        },
    )
    assert site.status_code == 200
    return site.json()["id"]


async def _create_subject(client: AsyncClient, study_id: int, site_id: int) -> int:
    subject = await client.post(
        "/api/v1/subjects",
        json={"study_id": study_id, "site_id": site_id, "screening_id": "MAT-S-001"},
    )
    assert subject.status_code == 200
    return subject.json()["id"]


async def _create_agent(client: AsyncClient) -> int:
    agent = await client.post(
        "/api/v1/agents/subjects",
        json={
            "principal_id": "agent://matrix/v1",
            "persona_key": "matrix_persona",
            "superpersona_contract_id": "contract-matrix",
            "model_version": "v1.0.0",
            "agent_owner_id": "owner_matrix",
            "autonomy_level": "shadow",
            "safety_class": "low",
        },
    )
    assert agent.status_code == 200
    return agent.json()["id"]


async def _run_ctms_uc_001(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _create_study(client, "CTMS-UC-001")
    resp = await client.post(f"/api/v1/studies/{study_id}/approve?version_number=1.0")
    return resp


async def _run_ctms_uc_002(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _create_study(client, "CTMS-UC-002")
    await _approve_study(client, study_id)
    site_id = await _create_site(client, study_id, "UC002-01")
    resp = await client.patch(f"/api/v1/sites/{site_id}", json={"activation_status": "activated"})
    return resp


async def _run_ctms_uc_003(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _create_study(client, "CTMS-UC-003")
    await _approve_study(client, study_id)
    site_id = await _create_site(client, study_id, "UC003-01")
    await client.post(f"/api/v1/sites/{site_id}/activate")
    subject_id = await _create_subject(client, study_id, site_id)
    await client.post(
        f"/api/v1/subjects/{subject_id}/consent",
        json={
            "subject_id": subject_id,
            "consent_version": "v1.0",
            "consent_date": "2026-01-01",
            "document_reference": "consent.pdf",
        },
    )
    resp = await client.get(f"/api/v1/subjects/{subject_id}")
    return resp


async def _run_ctms_uc_004(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _create_study(client, "CTMS-UC-004")
    await _approve_study(client, study_id)
    site_id = await _create_site(client, study_id, "UC004-01")
    await client.post(f"/api/v1/sites/{site_id}/activate")
    subject_id = await _create_subject(client, study_id, site_id)
    resp = await client.post(f"/api/v1/subjects/{subject_id}/withdraw?reason=withdrawal_of_consent")
    return resp


async def _run_ctms_uc_005(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _create_study(client, "CTMS-UC-005")
    await _approve_study(client, study_id)
    site_id = await _create_site(client, study_id, "UC005-01")
    await client.patch(f"/api/v1/sites/{site_id}", json={"activation_status": "activated"})
    subject_id = await _create_subject(client, study_id, site_id)
    await client.post(
        f"/api/v1/subjects/{subject_id}/consent",
        json={"subject_id": subject_id, "consent_version": "v1.0", "consent_date": "2026-01-01"},
    )
    resp = await client.post(
        f"/api/v1/subjects/{subject_id}/randomise",
        json={"stratification_factors": {"site": "UC005-01"}},
    )
    return resp


async def _run_ctms_uc_006(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _create_study(client, "CTMS-UC-006")
    await _approve_study(client, study_id)
    site_id = await _create_site(client, study_id, "UC006-01")
    await client.post(f"/api/v1/sites/{site_id}/activate")
    subject_id = await _create_subject(client, study_id, site_id)
    await client.post(
        "/api/v1/visits",
        json={
            "subject_id": subject_id,
            "visit_definition_id": "V2",
            "scheduled_date": "2026-01-01",
            "window_min_date": "2026-01-01",
            "window_max_date": "2026-01-05",
        },
    )
    resp = await client.post("/api/v1/visits/flag-missed")
    return resp


async def _run_ctms_uc_007(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _create_study(client, "CTMS-UC-007")
    await client.post(
        "/api/v1/regulatory-documents",
        json={
            "study_id": study_id,
            "document_type": "ethics_approval",
            "document_reference": "ETHICS-expired.pdf",
            "version": "1",
            "expiry_date": "2020-01-01",
        },
    )
    resp = await client.get(f"/api/v1/reports/etmf/{study_id}")
    return resp


async def _run_ctms_uc_008(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _create_study(client, "CTMS-UC-008")
    await _approve_study(client, study_id)
    site_id = await _create_site(client, study_id, "UC008-01")
    await client.post(f"/api/v1/sites/{site_id}/activate")
    subject_id = await _create_subject(client, study_id, site_id)
    resp = await client.post(
        "/api/v1/adverse-events",
        json={
            "study_id": study_id,
            "subject_id": subject_id,
            "onset_date": "2026-07-01",
            "severity": "severe",
            "seriousness": "life_threatening",
            "causality": "related",
            # ICH E2A: a SUSAR is Serious AND Unexpected AND suspected-related.
            # The row always asserted SUSAR behaviour; before REQ-CTS-NAT-006
            # the code inferred it from two limbs only, so the payload never
            # had to say it was unexpected.
            "expectedness": "unexpected",
        },
    )
    return resp


async def _run_ctms_uc_012(client: AsyncClient, case: dict[str, Any]) -> Any:
    agent_id = await _create_agent(client)
    await client.post(
        f"/api/v1/agents/subjects/{agent_id}/attestations",
        json={
            "agent_subject_id": agent_id,
            "attestation_type": "clinical_safety",
            "issuer": "issuer_matrix",
            "signature": "sig",
            "expires_at": "2027-01-01T00:00:00",
            "claims_json": {"score": 0.95},
        },
    )
    resp = await client.get(f"/api/v1/agents/subjects/{agent_id}")
    return resp


async def _run_ctms_uc_013(client: AsyncClient, case: dict[str, Any]) -> Any:
    agent_id = await _create_agent(client)
    resp = await client.post(
        f"/api/v1/agents/subjects/{agent_id}/consent-contracts",
        json={
            "agent_subject_id": agent_id,
            "purpose_of_use": "research",
            "allowed_systems": ["ctms"],
            "data_retention_days": 365,
            "model_owner_consent": True,
            "human_oversight_required": True,
            "withdrawal_mechanism": "token_revocation",
        },
    )
    return resp


async def _run_ctms_uc_014(client: AsyncClient, case: dict[str, Any]) -> Any:
    resp = await client.post(
        "/api/v1/agents/environments",
        json={
            "name": "Matrix env",
            "task_script_json": {"steps": ["triage", "reconcile"]},
            "synthetic_patient_cohort": [{}],
            "golden_path_steps": ["triage", "reconcile"],
            "perturbation_set": [{}],
        },
    )
    return resp


async def _run_ctms_uc_015(client: AsyncClient, case: dict[str, Any]) -> Any:
    agent_id = await _create_agent(client)
    env = await client.post(
        "/api/v1/agents/environments",
        json={
            "name": "Matrix run env",
            "task_script_json": {"steps": ["a"]},
            "synthetic_patient_cohort": [{}],
            "golden_path_steps": ["a"],
            "perturbation_set": [{}],
        },
    )
    env_id = env.json()["id"]
    run = await client.post(
        "/api/v1/agents/runs",
        json={"environment_id": env_id, "agent_subject_ids": [agent_id]},
    )
    run_id = run.json()["id"]
    await client.post(
        f"/api/v1/agents/runs/{run_id}/complete",
        json={"task_success": 0.95, "path_optimality": 0.9, "unsafe_action_rate": 0.01},
    )
    resp = await client.get(f"/api/v1/agents/runs/{run_id}/metrics")
    return resp


async def _run_ctms_uc_016(client: AsyncClient, case: dict[str, Any]) -> Any:
    cohort = await client.post(
        "/api/v1/agents/cohorts",
        json={
            "name": "Matrix cohort",
            "cohort_type": "single_agent",
            "capability_profile": "test",
            "model_family": "test_family",
            "evaluation_objective": "matrix release gate",
        },
    )
    cohort_id = cohort.json()["id"]
    resp = await client.get(f"/api/v1/agents/cohorts/{cohort_id}/release-gate")
    return resp


async def _run_ctms_uc_017(client: AsyncClient, case: dict[str, Any]) -> Any:
    cohort = await client.post(
        "/api/v1/agents/cohorts",
        json={
            "name": "Matrix bias cohort",
            "cohort_type": "single_agent",
            "capability_profile": "test",
            "model_family": "test_family",
            "evaluation_objective": "matrix bias",
        },
    )
    cohort_id = cohort.json()["id"]
    resp = await client.post(
        "/api/v1/agents/bias-reports",
        json={
            "cohort_id": cohort_id,
            "demographic_strata": {"age": ["<65"]},
            "metric_disparities": {"task_success": {"<65": 0.9}},
            "drift_flags": ["drift"],
        },
    )
    return resp


async def _run_ctms_uc_018(client: AsyncClient, case: dict[str, Any]) -> Any:
    await _create_study(client, "CTMS-DUP-001")
    resp = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "CTMS-DUP-001",
            "title": "Duplicate",
            "phase": "II",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    return resp


async def _run_ctms_uc_019(client: AsyncClient, case: dict[str, Any]) -> Any:
    resp = await client.get("/api/v1/studies/99999")
    return resp


async def _run_ctms_uc_009(client: AsyncClient, case: dict[str, Any]) -> Any:
    """FR-C-71 / FR-C-72: receive a shipment, then dispense from it."""

    study_id = await _create_study(client, "CTMS-UC-009")
    await _approve_study(client, study_id)
    site_id = await _create_site(client, study_id, "UC009-01")
    await client.patch(f"/api/v1/sites/{site_id}", json={"activation_status": "activated"})
    subject_id = await _create_subject(client, study_id, site_id)
    await client.post(
        f"/api/v1/subjects/{subject_id}/consent",
        json={
            "subject_id": subject_id,
            "consent_version": "v1.0",
            "consent_date": "2026-01-01",
        },
    )
    product = await client.post(
        "/api/v1/ip/products",
        json={
            "sku": "UC009-IP",
            "name": "UC009 capsules",
            "lot_number": case["test_data"]["lot"],
            "expiry_date": "2027-01-01",
            "storage_conditions": "2-8C",
            "accountability_unit": "capsule",
            "quantity_on_hand": 0,
            "site_id": site_id,
        },
    )
    assert product.status_code == 200, product.text
    product_id = product.json()["id"]
    shipment = await client.post(
        "/api/v1/ip/shipments",
        json={
            "shipment_id": "SHIP-UC009-001",
            "product_id": product_id,
            "from_organisation": "Central depot",
            "to_site_id": site_id,
            "quantity_shipped": case["test_data"]["quantity"],
        },
    )
    assert shipment.status_code == 200, shipment.text
    received = await client.post(
        f"/api/v1/ip/shipments/{shipment.json()['id']}/receive"
        "?received_by=pharm_uc009&condition_ok=true"
    )
    assert received.status_code == 200, received.text
    stock = await client.get(f"/api/v1/ip/products/{product_id}")
    assert stock.json()["quantity_on_hand"] == case["test_data"]["quantity"]
    return await client.post(
        "/api/v1/ip/dispenses",
        json={
            "subject_id": subject_id,
            "product_id": product_id,
            "quantity_dispensed": case["test_data"]["dispense_quantity"],
            "dispensed_by": "pharm_uc009",
        },
    )


async def _run_ctms_uc_010(client: AsyncClient, case: dict[str, Any]) -> Any:
    """FR-C-81 / FR-C-83: budget actuals accrue, then an invoice is drafted."""

    study_id = await _create_study(client, "CTMS-UC-010")
    budget = await client.post(
        "/api/v1/budgets",
        json={
            "study_id": study_id,
            "budget_category": case["test_data"]["budget_category"],
            "planned_amount": case["test_data"]["planned_amount"],
        },
    )
    assert budget.status_code == 200, budget.text
    updated = await client.patch(
        f"/api/v1/budgets/{budget.json()['id']}", json={"actual_amount": 2500.0}
    )
    assert updated.status_code == 200 and updated.json()["actual_amount"] == 2500.0
    return await client.post(
        "/api/v1/budgets/invoices",
        json={
            "study_id": study_id,
            "sponsor_id": "SPON-UC010",
            "amount": 2500.0,
            "linked_items": [{"budget_id": budget.json()["id"], "amount": 2500.0}],
        },
    )


async def _run_ctms_uc_011(client: AsyncClient, case: dict[str, Any]) -> Any:
    """FR-C-91: the recruitment dashboard reports actual against planned."""

    study_id = await _create_study(client, "CTMS-UC-011")
    await _approve_study(client, study_id)
    site_id = await _create_site(client, study_id, "UC011-01")
    await client.patch(f"/api/v1/sites/{site_id}", json={"activation_status": "activated"})
    subject_id = await _create_subject(client, study_id, site_id)
    await client.post(
        f"/api/v1/subjects/{subject_id}/consent",
        json={
            "subject_id": subject_id,
            "consent_version": "v1.0",
            "consent_date": "2026-01-01",
        },
    )
    return await client.get(f"/api/v1/reports/recruitment/{study_id}")


# --- National capability runners (REQ-CTS-NAT-001..008) ---------------------


async def _nat_study(client: AsyncClient, protocol: str, jurisdiction: str) -> int:
    resp = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": protocol,
            "title": f"National capability study {protocol}",
            "phase": "II",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Symphonix Research",
            "jurisdiction": jurisdiction,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


async def _nat_site(client: AsyncClient, study_id: int, code: str) -> int:
    site_id = await _create_site(client, study_id, code)
    for task in ("ethics", "contract", "delegation_log", "training", "pharmacy_setup"):
        await client.patch(
            f"/api/v1/sites/{site_id}/checklist/{task}?status=complete"
        )
    return site_id


async def _nat_subject(client: AsyncClient, study_id: int, site_id: int, screening: str) -> int:
    resp = await client.post(
        "/api/v1/subjects",
        json={"study_id": study_id, "site_id": site_id, "screening_id": screening},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


async def _run_ctms_uc_021(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _nat_study(client, "CTMS-UC-021", case["test_data"]["jurisdiction"])
    submitted = await client.post(
        "/api/v1/trial-registrations", json={"study_id": study_id}
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["status"] == "submitted", "dispatch is not completion"
    assert submitted.json()["registry_code"] == case["test_data"]["registry_code"]
    registration_id = submitted.json()["id"]
    wrong = await client.post(
        f"/api/v1/trial-registrations/{registration_id}/receipt",
        json={"registry_identifier": "ISRCTN12345678", "receipt_reference": "WRONG"},
    )
    assert wrong.status_code == 422, "a UK identifier must not satisfy an IE registry"
    return await client.post(
        f"/api/v1/trial-registrations/{registration_id}/receipt",
        json={
            "registry_identifier": case["test_data"]["registry_identifier"],
            "receipt_reference": "CTIS-ACK-2026-000431",
        },
    )


async def _run_ctms_uc_022(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _nat_study(client, "CTMS-UC-022", "UK")
    site_id = await _create_site(client, study_id, "UC022-01")
    delegation = await client.post(
        "/api/v1/delegations",
        json={
            "site_id": site_id,
            "person_id": "rn_uc022",
            "person_name": "Research Nurse",
            "role": case["test_data"]["role"],
            "delegated_tasks": ["vital_signs", "ae_capture"],
            "delegated_by": "dr_uc022",
            "gcp_training_date": case["test_data"]["gcp_training_date"],
            "start_date": "2026-02-01",
        },
    )
    assert delegation.status_code == 200, delegation.text
    assert delegation.json()["status"] == "active"
    assert delegation.json()["gcp_training_expiry"] > case["test_data"]["gcp_training_date"]
    return await client.get(f"/api/v1/sites/{site_id}/readiness")


async def _run_ctms_uc_023(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _nat_study(client, "CTMS-UC-023", "UK")
    approval = await client.post(
        "/api/v1/regulatory-approvals",
        json={
            "study_id": study_id,
            "authority_kind": case["test_data"]["authority_kind"],
            "submission_type": case["test_data"]["submission_type"],
            "submission_reference": "IRAS-UC023-001",
            "protocol_version": "v1.0",
        },
    )
    assert approval.status_code == 200, approval.text
    assert approval.json()["authority_code"] == "HRA-REC"
    approval_id = approval.json()["id"]
    unnamed = await client.post(
        f"/api/v1/regulatory-approvals/{approval_id}/decision",
        json={"decision": "approved", "decided_by": ""},
    )
    assert unnamed.status_code == 422, "an unnamed decision must be refused"
    decided = await client.post(
        f"/api/v1/regulatory-approvals/{approval_id}/decision",
        json={
            "decision": "approved_with_conditions",
            "decided_by": "Prof Helen Whitmore (REC chair)",
            "conditions": [{"reference": "C1", "text": "Update the participant sheet"}],
            "approval_expiry": "2028-06-30",
        },
    )
    due = await client.get(
        f"/api/v1/regulatory-approvals/due/{study_id}?within_days=3650"
    )
    assert due.status_code == 200 and due.json()["reports_due"], due.text
    return decided


async def _run_ctms_uc_024(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _nat_study(client, "CTMS-UC-024", "UK")
    site_id = await _create_site(client, study_id, "UC024-01")
    criteria = case["test_data"]["criteria"]
    screening = await client.post(
        "/api/v1/eligibility-screenings",
        json={
            "study_id": study_id,
            "site_id": site_id,
            "candidate_reference": case["test_data"]["candidate_reference"],
            "consent_basis": "research_contact_consent",
            "requested_by": "crc_uc024",
            "criteria_requested": criteria,
        },
    )
    assert screening.status_code == 200, screening.text
    screening_id = screening.json()["id"]
    partial = await client.post(
        f"/api/v1/eligibility-screenings/{screening_id}/outcome",
        json={"criteria_evaluated": {criteria[0]: True}},
    )
    assert partial.status_code == 422, "a partial evaluation must be refused"
    return await client.post(
        f"/api/v1/eligibility-screenings/{screening_id}/outcome",
        json={
            "criteria_evaluated": {criteria[0]: True, criteria[1]: True, criteria[2]: False},
            "reviewed_by": "dr_uc024",
            "source_system": "bullettrain-hub",
        },
    )


async def _run_ctms_uc_025(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _nat_study(client, "CTMS-UC-025", "UK")
    site_id = await _nat_site(client, study_id, "UC025-01")
    subject_id = await _nat_subject(client, study_id, site_id, "UC025-S-001")
    consent = await client.post(
        f"/api/v1/subjects/{subject_id}/consent",
        json={
            "subject_id": subject_id,
            "consent_version": "v1.0",
            "consent_date": "2026-03-01T09:00:00",
            "consent_type": "initial",
            "protocol_version": "v1.0",
        },
    )
    assert consent.status_code == 200, consent.text
    visit = await client.post(
        "/api/v1/visits",
        json={
            "subject_id": subject_id,
            "visit_definition_id": "V3",
            "scheduled_date": "2026-12-01",
            "window_min_date": "2026-11-28",
            "window_max_date": "2026-12-05",
        },
    )
    assert visit.status_code == 200
    product = await client.post(
        "/api/v1/ip/products",
        json={
            "sku": "UC025-IP",
            "name": "UC025 capsules",
            "lot_number": "LOT-UC025",
            "expiry_date": "2027-06-01",
            "storage_conditions": "2-8C",
            "accountability_unit": "capsule",
            "quantity_on_hand": 60,
        },
    )
    product_id = product.json()["id"]

    ok = await client.post(
        "/api/v1/ip/dispenses",
        json={
            "subject_id": subject_id,
            "product_id": product_id,
            "quantity_dispensed": 10,
            "dispensed_by": "pharm_uc025",
        },
    )
    assert ok.status_code == 200, "dispensing must work while consent is active"

    flagged = await client.post(
        f"/api/v1/studies/{study_id}/flag-reconsent"
        f"?protocol_version={case['test_data']['protocol_version']}"
    )
    assert flagged.status_code == 200 and flagged.json(), flagged.text
    suspended = await client.post(
        "/api/v1/ip/dispenses",
        json={
            "subject_id": subject_id,
            "product_id": product_id,
            "quantity_dispensed": 10,
            "dispensed_by": "pharm_uc025",
        },
    )
    assert suspended.status_code == 422, "re-consent must suspend dispensing"

    reconsent = await client.post(
        f"/api/v1/subjects/{subject_id}/consent",
        json={
            "subject_id": subject_id,
            "consent_version": case["test_data"]["protocol_version"],
            "consent_date": "2026-06-01T09:00:00",
            "consent_type": "re_consent",
            "protocol_version": case["test_data"]["protocol_version"],
        },
    )
    assert reconsent.status_code == 200
    resumed = await client.post(
        "/api/v1/ip/dispenses",
        json={
            "subject_id": subject_id,
            "product_id": product_id,
            "quantity_dispensed": 10,
            "dispensed_by": "pharm_uc025",
        },
    )
    assert resumed.status_code == 200, "re-consent must restore dispensing"

    withdrawn = await client.post(
        f"/api/v1/subjects/{subject_id}/withdraw"
        f"?reason=participant+request&withdrawal_scope={case['test_data']['withdrawal_scope']}"
    )
    assert withdrawn.status_code == 200
    blocked = await client.post(
        "/api/v1/ip/dispenses",
        json={
            "subject_id": subject_id,
            "product_id": product_id,
            "quantity_dispensed": 10,
            "dispensed_by": "pharm_uc025",
        },
    )
    assert blocked.status_code == 422, "withdrawal must block dispensing"
    return await client.get(f"/api/v1/participants/{subject_id}/summary")


async def _run_ctms_uc_026(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _nat_study(client, "CTMS-UC-026", "IE")
    site_id = await _nat_site(client, study_id, "UC026-01")
    subject_id = await _nat_subject(client, study_id, site_id, "UC026-S-001")
    randomised = await client.post(
        f"/api/v1/subjects/{subject_id}/randomise",
        json={
            "stratification_factors": case["test_data"]["stratification_factors"],
            "randomised_by": "crc_uc026",
        },
    )
    assert randomised.status_code == 200, randomised.text
    allocation = await client.get(f"/api/v1/subjects/{subject_id}/allocation")
    assert allocation.status_code == 200
    assert "arm" not in allocation.json(), "the blinded read must not carry the arm"
    assert allocation.json()["kit_code"].startswith("KIT-")
    return await client.post(
        f"/api/v1/subjects/{subject_id}/unblind",
        json={
            "requested_by": "crc_uc026",
            "authorised_by": "dr_uc026",
            "reason": "suspected serious reaction, treatment decision needs the arm",
            "urgency": "emergency",
        },
    )


async def _run_ctms_uc_027(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _nat_study(client, "CTMS-UC-027", "UK")
    site_id = await _nat_site(client, study_id, "UC027-01")
    subject_id = await _nat_subject(client, study_id, site_id, "UC027-S-001")
    ae = await client.post(
        "/api/v1/adverse-events",
        json={
            "study_id": study_id,
            "subject_id": subject_id,
            "onset_date": "2026-07-20",
            "severity": "fatal",
            "seriousness": case["test_data"]["seriousness"],
            "causality": case["test_data"]["causality"],
            "expectedness": case["test_data"]["expectedness"],
        },
    )
    assert ae.status_code == 200, ae.text
    assert ae.json()["susar_flag"] is True, "fatal + unexpected + related is a SUSAR"
    assert ae.json()["deadline_basis"] == "UK:1.0.0:susar:7d"
    ae_id = ae.json()["id"]
    wrong_authority = await client.post(
        f"/api/v1/adverse-events/{ae_id}/safety-submissions",
        json={
            "submitted_by": "safety_officer_uc027",
            "recipient_code": "HPRA",
            "submission_reference": "SUSAR-UC027-000",
        },
    )
    assert wrong_authority.status_code == 422, "recipient outside the jurisdiction"
    submitted = await client.post(
        f"/api/v1/adverse-events/{ae_id}/safety-submissions",
        json={
            "submitted_by": "safety_officer_uc027",
            "recipient_code": "MHRA",
            "submission_reference": "SUSAR-UC027-001",
        },
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["status"] == "submitted", "dispatch is not completion"
    return await client.post(
        f"/api/v1/safety-submissions/{submitted.json()['id']}/acknowledgement",
        json={"acknowledgement_reference": "MHRA-ACK-UC027-1"},
    )


async def _run_ctms_uc_028(client: AsyncClient, case: dict[str, Any]) -> Any:
    study_id = await _nat_study(client, "CTMS-UC-028", "UK")
    site_id = await _nat_site(client, study_id, "UC028-01")
    subject_id = await _nat_subject(client, study_id, site_id, "UC028-S-001")
    await client.post(
        f"/api/v1/subjects/{subject_id}/consent",
        json={
            "subject_id": subject_id,
            "consent_version": "v1.0",
            "consent_date": "2026-03-01T09:00:00",
        },
    )
    product = await client.post(
        "/api/v1/ip/products",
        json={
            "sku": "UC028-IP",
            "name": "UC028 capsules",
            "lot_number": "LOT-UC028",
            "expiry_date": "2027-06-01",
            "storage_conditions": "2-8C",
            "accountability_unit": "capsule",
            "quantity_on_hand": 5,
        },
    )
    product_id = product.json()["id"]
    over = await client.post(
        "/api/v1/ip/dispenses",
        json={
            "subject_id": subject_id,
            "product_id": product_id,
            "quantity_dispensed": 6,
            "dispensed_by": "pharm_uc028",
        },
    )
    assert over.status_code == 422, "a dispense above on-hand must be refused"
    within = await client.post(
        "/api/v1/ip/dispenses",
        json={
            "subject_id": subject_id,
            "product_id": product_id,
            "quantity_dispensed": 5,
            "dispensed_by": "pharm_uc028",
        },
    )
    assert within.status_code == 200
    remaining = await client.get(f"/api/v1/ip/products/{product_id}")
    assert remaining.json()["quantity_on_hand"] == 0, "accountability must balance"

    payment = await client.post(
        "/api/v1/reimbursements",
        json={
            "subject_id": subject_id,
            "category": "travel",
            "amount": case["test_data"]["over_cap_amount"],
        },
    )
    assert payment.status_code == 200, payment.text
    assert payment.json()["exceeds_guidance_cap"] is True
    assert payment.json()["currency"] == "GBP"
    approved = await client.post(
        f"/api/v1/reimbursements/{payment.json()['id']}/approve"
        "?approved_by=finance_coordinator_uc028"
    )
    assert approved.status_code == 200
    twice = await client.post(
        f"/api/v1/reimbursements/{payment.json()['id']}/approve"
        "?approved_by=finance_coordinator_uc028"
    )
    assert twice.status_code == 409, "a payment must not be approved twice"
    return await client.get(f"/api/v1/participants/{subject_id}/summary")


async def _run_ctms_uc_029(client: AsyncClient, case: dict[str, Any]) -> Any:
    packs = await client.get("/api/v1/country-packs")
    assert packs.status_code == 200
    codes = {p["code"] for p in packs.json()}
    assert codes == set(case["preconditions"]["packs"]), codes
    for pack in packs.json():
        assert pack["sources"], pack["code"]
        assert pack["pack_version"] and pack["effective_from"], pack["code"]
    return await client.get(
        f"/api/v1/country-packs/{case['test_data']['unknown_jurisdiction']}"
    )


_RUNNERS: dict[str, Any] = {
    "CTMS-UC-001": _run_ctms_uc_001,
    "CTMS-UC-002": _run_ctms_uc_002,
    "CTMS-UC-003": _run_ctms_uc_003,
    "CTMS-UC-004": _run_ctms_uc_004,
    "CTMS-UC-005": _run_ctms_uc_005,
    "CTMS-UC-006": _run_ctms_uc_006,
    "CTMS-UC-007": _run_ctms_uc_007,
    "CTMS-UC-008": _run_ctms_uc_008,
    "CTMS-UC-009": _run_ctms_uc_009,
    "CTMS-UC-010": _run_ctms_uc_010,
    "CTMS-UC-011": _run_ctms_uc_011,
    "CTMS-UC-012": _run_ctms_uc_012,
    "CTMS-UC-013": _run_ctms_uc_013,
    "CTMS-UC-014": _run_ctms_uc_014,
    "CTMS-UC-015": _run_ctms_uc_015,
    "CTMS-UC-016": _run_ctms_uc_016,
    "CTMS-UC-017": _run_ctms_uc_017,
    "CTMS-UC-018": _run_ctms_uc_018,
    "CTMS-UC-019": _run_ctms_uc_019,
    "CTMS-UC-021": _run_ctms_uc_021,
    "CTMS-UC-022": _run_ctms_uc_022,
    "CTMS-UC-023": _run_ctms_uc_023,
    "CTMS-UC-024": _run_ctms_uc_024,
    "CTMS-UC-025": _run_ctms_uc_025,
    "CTMS-UC-026": _run_ctms_uc_026,
    "CTMS-UC-027": _run_ctms_uc_027,
    "CTMS-UC-028": _run_ctms_uc_028,
    "CTMS-UC-029": _run_ctms_uc_029,
}


def _case_ids() -> list[str]:
    matrix = _load_matrix()
    return [case["use_case_id"] for case in matrix["test_cases"] if case["use_case_id"] in _RUNNERS]


@pytest.mark.parametrize("use_case_id", _case_ids())
async def test_matrix_scenario(client: AsyncClient, use_case_id: str) -> None:
    matrix = _load_matrix()
    case = next(c for c in matrix["test_cases"] if c["use_case_id"] == use_case_id)
    runner = _RUNNERS[use_case_id]
    response = await runner(client, case)
    failures = []
    for rule in case["validation_rules"]:
        if not _validate_rule(rule, response, case.get("test_data", {})):
            failures.append(rule)
    assert not failures, (
    )



def test_every_14col_row_has_an_executing_runner() -> None:
    """No 14-column row may sit in the matrix without executing.

    ``_case_ids`` silently skips a row with no runner, so a row added without
    one would look like coverage while never dispatching a request. This is
    the padding failure mode in its 14-column form.
    """

    matrix = _load_matrix()
    missing = [
        case["use_case_id"]
        for case in matrix["test_cases"]
        if case["use_case_id"] not in _RUNNERS
    ]
    assert not missing, (
        f"{len(missing)} 14-column row(s) have no runner and therefore never "
        f"execute: {missing}"
    )


def test_national_rows_bind_requirements_and_acceptance_criteria() -> None:
    """Every national row carries BOTH id families, and both resolve."""

    import json as _json

    superset = _json.loads(
        (
            MATRIX_PATH.resolve().parents[2] / "harness" / "requirements_superset.json"
        ).read_text(encoding="utf-8")
    )
    known_reqs = {r["requirement_id"] for r in superset["requirements"]}
    known_acs = {
        ac["ac_id"]
        for r in superset["requirements"]
        for ac in (r.get("acceptance_criteria") or [])
    }
    national = [
        c
        for c in _load_matrix()["test_cases"]
        if "national" in (c.get("tags") or [])
    ]
    assert national, "the national 14-column rows disappeared"
    for case in national:
        uid = case["use_case_id"]
        assert case.get("requirement_ids"), uid
        assert case.get("acceptance_criteria_ids"), uid
        unknown_r = set(case["requirement_ids"]) - known_reqs
        unknown_a = set(case["acceptance_criteria_ids"]) - known_acs
        assert not unknown_r, f"{uid} cites unknown requirement(s) {unknown_r}"
        assert not unknown_a, f"{uid} cites unknown acceptance criteria {unknown_a}"