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


_RUNNERS: dict[str, Any] = {
    "CTMS-UC-001": _run_ctms_uc_001,
    "CTMS-UC-002": _run_ctms_uc_002,
    "CTMS-UC-003": _run_ctms_uc_003,
    "CTMS-UC-004": _run_ctms_uc_004,
    "CTMS-UC-005": _run_ctms_uc_005,
    "CTMS-UC-006": _run_ctms_uc_006,
    "CTMS-UC-007": _run_ctms_uc_007,
    "CTMS-UC-008": _run_ctms_uc_008,
    "CTMS-UC-012": _run_ctms_uc_012,
    "CTMS-UC-013": _run_ctms_uc_013,
    "CTMS-UC-014": _run_ctms_uc_014,
    "CTMS-UC-015": _run_ctms_uc_015,
    "CTMS-UC-016": _run_ctms_uc_016,
    "CTMS-UC-017": _run_ctms_uc_017,
    "CTMS-UC-018": _run_ctms_uc_018,
    "CTMS-UC-019": _run_ctms_uc_019,
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
    assert not failures, f"{use_case_id} failed rules: {failures}; response was {response.status_code} {response.text[:200]}"
