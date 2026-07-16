"""Agentic subject tests."""

from httpx import AsyncClient


async def test_create_agent_subject(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/agents/subjects",
        json={
            "principal_id": "agent://test/v1",
            "persona_key": "test_persona",
            "superpersona_contract_id": "contract-test",
            "model_version": "v1.0.0",
            "agent_owner_id": "owner_1",
            "autonomy_level": "shadow",
            "safety_class": "low",
            "registration_source": "direct",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["principal_id"] == "agent://test/v1"


async def test_create_agent_attestation(client: AsyncClient) -> None:
    agent_id = (
        await client.post(
            "/api/v1/agents/subjects",
            json={
                "principal_id": "agent://attest/v1",
                "persona_key": "attest_persona",
                "superpersona_contract_id": "contract-attest",
                "model_version": "v1.0.0",
                "agent_owner_id": "owner_1",
                "autonomy_level": "shadow",
                "safety_class": "low",
            },
        )
    ).json()["id"]
    resp = await client.post(
        f"/api/v1/agents/subjects/{agent_id}/attestations",
        json={
            "agent_subject_id": agent_id,
            "attestation_type": "clinical_safety",
            "issuer": "issuer_1",
            "signature": "sig",
            "expires_at": "2027-01-01T00:00:00",
            "claims_json": {"score": 0.95},
        },
    )
    assert resp.status_code == 200
    agent = await client.get(f"/api/v1/agents/subjects/{agent_id}")
    assert agent.json()["attestation_status"] == "valid"


async def test_create_synthetic_environment(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/agents/environments",
        json={
            "name": "Test env",
            "task_script_json": {"steps": ["a", "b"]},
            "synthetic_patient_cohort": [{}],
            "golden_path_steps": ["a", "b"],
            "perturbation_set": [{}],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["reproducibility_hash"] is not None


async def test_agent_run_and_metrics(client: AsyncClient) -> None:
    agent_id = (
        await client.post(
            "/api/v1/agents/subjects",
            json={
                "principal_id": "agent://run/v1",
                "persona_key": "run_persona",
                "superpersona_contract_id": "contract-run",
                "model_version": "v1.0.0",
                "agent_owner_id": "owner_1",
                "autonomy_level": "shadow",
                "safety_class": "low",
            },
        )
    ).json()["id"]
    env_id = (
        await client.post(
            "/api/v1/agents/environments",
            json={
                "name": "Run env",
                "task_script_json": {"steps": ["a"]},
                "synthetic_patient_cohort": [{}],
                "golden_path_steps": ["a"],
                "perturbation_set": [{}],
            },
        )
    ).json()["id"]
    run_id = (
        await client.post(
            "/api/v1/agents/runs",
            json={"environment_id": env_id, "agent_subject_ids": [agent_id]},
        )
    ).json()["id"]
    await client.post(
        f"/api/v1/agents/runs/{run_id}/complete",
        json={"task_success": 0.9, "path_optimality": 0.85, "unsafe_action_rate": 0.05},
    )
    metrics = await client.get(f"/api/v1/agents/runs/{run_id}/metrics")
    assert metrics.status_code == 200
    assert len(metrics.json()) >= 3


async def test_create_cohort(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/agents/cohorts",
        json={
            "name": "Test cohort",
            "cohort_type": "single_agent",
            "capability_profile": "test",
            "model_family": "test_family",
            "evaluation_objective": "test objective",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test cohort"


async def test_create_bias_report(client: AsyncClient) -> None:
    cohort_id = (
        await client.post(
            "/api/v1/agents/cohorts",
            json={
                "name": "Bias cohort",
                "cohort_type": "single_agent",
                "capability_profile": "test",
                "model_family": "test_family",
                "evaluation_objective": "test objective",
            },
        )
    ).json()["id"]
    resp = await client.post(
        "/api/v1/agents/bias-reports",
        json={
            "cohort_id": cohort_id,
            "demographic_strata": {"age": ["<65"]},
            "metric_disparities": {"task_success": {"<65": 0.9}},
            "drift_flags": ["drift"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["drift_flags"] == ["drift"]


async def test_create_agent_consent_contract(client: AsyncClient) -> None:
    agent_id = (
        await client.post(
            "/api/v1/agents/subjects",
            json={
                "principal_id": "agent://consent/v1",
                "persona_key": "consent_persona",
                "superpersona_contract_id": "contract-consent",
                "model_version": "v1.0.0",
                "agent_owner_id": "owner_1",
                "autonomy_level": "shadow",
                "safety_class": "low",
            },
        )
    ).json()["id"]
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
    assert resp.status_code == 200
    assert resp.json()["purpose_of_use"] == "research"


async def test_cohort_membership_and_release_gate(client: AsyncClient) -> None:
    agent_id = (
        await client.post(
            "/api/v1/agents/subjects",
            json={
                "principal_id": "agent://gate/v1",
                "persona_key": "gate_persona",
                "superpersona_contract_id": "contract-gate",
                "model_version": "v1.0.0",
                "agent_owner_id": "owner_1",
                "autonomy_level": "shadow",
                "safety_class": "low",
            },
        )
    ).json()["id"]
    cohort_id = (
        await client.post(
            "/api/v1/agents/cohorts",
            json={
                "name": "Gate cohort",
                "cohort_type": "single_agent",
                "capability_profile": "test",
                "model_family": "test_family",
                "evaluation_objective": "release gate test",
            },
        )
    ).json()["id"]
    add_resp = await client.post(
        f"/api/v1/agents/cohorts/{cohort_id}/members?agent_subject_id={agent_id}"
    )
    assert add_resp.status_code == 200
    gate = await client.get(f"/api/v1/agents/cohorts/{cohort_id}/release-gate")
    assert gate.status_code == 200
    assert gate.json()["status"] == "promoted"


async def test_create_agent_trial_arm(client: AsyncClient) -> None:
    agent_id = (
        await client.post(
            "/api/v1/agents/subjects",
            json={
                "principal_id": "agent://arm/v1",
                "persona_key": "arm_persona",
                "superpersona_contract_id": "contract-arm",
                "model_version": "v1.0.0",
                "agent_owner_id": "owner_1",
                "autonomy_level": "shadow",
                "safety_class": "low",
            },
        )
    ).json()["id"]
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "AGENT-ARM-001",
            "title": "Agent arm test",
            "phase": "II",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    study_id = study.json()["id"]
    resp = await client.post(
        "/api/v1/agents/trial-arms",
        json={
            "agent_subject_id": agent_id,
            "study_id": study_id,
            "randomisation_arm": "arm_a",
            "stratification_factors": {"site": "A"},
            "consent_contract_version": "v1.0",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["randomisation_arm"] == "arm_a"
