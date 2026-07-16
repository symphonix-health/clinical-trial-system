"""Targeted coverage tests for endpoint branches not exercised by existing tests."""

from httpx import AsyncClient


# Studies
async def test_get_study(client: AsyncClient) -> None:
    created = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "COV-ST-001",
            "title": "Coverage study",
            "phase": "I",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    study_id = created.json()["id"]
    resp = await client.get(f"/api/v1/studies/{study_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == study_id


async def test_create_protocol_version_coverage(client: AsyncClient) -> None:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "COV-PV-001",
            "title": "Protocol coverage",
            "phase": "I",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    study_id = study.json()["id"]
    resp = await client.post(
        f"/api/v1/studies/{study_id}/protocol-versions",
        json={"study_id": study_id, "version_number": "v1"},
    )
    assert resp.status_code == 200
    assert resp.json()["version_number"] == "v1"


# Sites
async def test_list_and_get_site(client: AsyncClient) -> None:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "COV-SITE-001",
            "title": "Site coverage",
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
            "site_code": "COV-01",
            "name": "Coverage site",
            "organisation_id": "org",
            "principal_investigator_id": "pi",
        },
    )
    site_id = site.json()["id"]

    resp = await client.get("/api/v1/sites")
    assert resp.status_code == 200
    assert any(s["id"] == site_id for s in resp.json())

    resp = await client.get(f"/api/v1/sites/{site_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == site_id

    resp = await client.patch(f"/api/v1/sites/{site_id}/checklist/ethics?status=complete")
    assert resp.status_code == 200
    assert resp.json()["status"] == "complete"


async def test_list_sites_filtered(client: AsyncClient) -> None:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "COV-SITE-002",
            "title": "Site filter coverage",
            "phase": "I",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    study_id = study.json()["id"]
    await client.post(
        "/api/v1/sites",
        json={
            "study_id": study_id,
            "site_code": "COV-02",
            "name": "Filtered site",
            "organisation_id": "org",
            "principal_investigator_id": "pi",
        },
    )
    resp = await client.get(f"/api/v1/sites?study_id={study_id}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# Subjects
async def test_get_and_list_and_update_subject(client: AsyncClient) -> None:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "COV-SUB-001",
            "title": "Subject coverage",
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
            "site_code": "COV-SUB-01",
            "name": "Site",
            "organisation_id": "org",
            "principal_investigator_id": "pi",
        },
    )
    site_id = site.json()["id"]
    subject = await client.post(
        "/api/v1/subjects",
        json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-COV001"},
    )
    subject_id = subject.json()["id"]

    resp = await client.get(f"/api/v1/subjects/{subject_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == subject_id

    resp = await client.get("/api/v1/subjects")
    assert resp.status_code == 200
    assert any(s["id"] == subject_id for s in resp.json())

    resp = await client.patch(f"/api/v1/subjects/{subject_id}", json={"enrolment_status": "screening"})
    assert resp.status_code == 200


# Visits
async def test_get_visit(client: AsyncClient) -> None:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "COV-VIS-001",
            "title": "Visit coverage",
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
            "site_code": "COV-VIS-01",
            "name": "Site",
            "organisation_id": "org",
            "principal_investigator_id": "pi",
        },
    )
    site_id = site.json()["id"]
    subject = await client.post(
        "/api/v1/subjects",
        json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-COVV001"},
    )
    subject_id = subject.json()["id"]
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
    resp = await client.get(f"/api/v1/visits/{visit_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == visit_id


# Adverse events
async def test_list_and_get_adverse_event(client: AsyncClient) -> None:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "COV-AE-001",
            "title": "AE coverage",
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
            "site_code": "COV-AE-01",
            "name": "Site",
            "organisation_id": "org",
            "principal_investigator_id": "pi",
        },
    )
    site_id = site.json()["id"]
    subject = await client.post(
        "/api/v1/subjects",
        json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-COVAE001"},
    )
    subject_id = subject.json()["id"]
    ae = await client.post(
        "/api/v1/adverse-events",
        json={
            "study_id": study_id,
            "subject_id": subject_id,
            "onset_date": "2026-04-01",
            "severity": "mild",
            "seriousness": "non_serious",
            "causality": "unrelated",
        },
    )
    ae_id = ae.json()["id"]

    resp = await client.get(f"/api/v1/adverse-events/{ae_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == ae_id

    resp = await client.get(f"/api/v1/adverse-events?study_id={study_id}")
    assert resp.status_code == 200
    assert any(a["id"] == ae_id for a in resp.json())


# Budgets
async def test_create_invoice_coverage(client: AsyncClient) -> None:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "COV-BUD-001",
            "title": "Budget coverage",
            "phase": "I",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    study_id = study.json()["id"]
    resp = await client.post(
        "/api/v1/budgets/invoices",
        json={"study_id": study_id, "sponsor_id": "sponsor_cov", "amount": 500},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"


# IP
async def test_get_product_and_destroy_dispense(client: AsyncClient) -> None:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "COV-IP-001",
            "title": "IP coverage",
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
            "site_code": "COV-IP-01",
            "name": "Site",
            "organisation_id": "org",
            "principal_investigator_id": "pi",
        },
    )
    site_id = site.json()["id"]
    product = await client.post(
        "/api/v1/ip/products",
        json={
            "sku": "COV-SKU-001",
            "name": "Coverage drug",
            "lot_number": "COV-LOT-001",
            "expiry_date": "2027-01-01",
            "storage_conditions": "2-8C",
            "accountability_unit": "tablet",
            "quantity_on_hand": 100,
            "site_id": site_id,
        },
    )
    product_id = product.json()["id"]
    resp = await client.get(f"/api/v1/ip/products/{product_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == product_id

    subject = await client.post(
        "/api/v1/subjects",
        json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-COVIP001"},
    )
    subject_id = subject.json()["id"]
    dispense = await client.post(
        "/api/v1/ip/dispenses",
        json={"subject_id": subject_id, "product_id": product_id, "quantity_dispensed": 10},
    )
    dispense_id = dispense.json()["id"]
    resp = await client.post(
        f"/api/v1/ip/dispenses/{dispense_id}/destroy",
        json={"destroyed_at": "2026-06-01T00:00:00", "destroyed_by": "pharm1"},
    )
    assert resp.status_code == 200
    assert resp.json()["destroyed_by"] == "pharm1"


# Queries
async def test_list_and_get_query(client: AsyncClient) -> None:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "COV-Q-001",
            "title": "Query coverage",
            "phase": "I",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    study_id = study.json()["id"]
    query = await client.post(
        "/api/v1/queries",
        json={"study_id": study_id, "raised_by": "cra_1", "assigned_to": "crc_1"},
    )
    query_id = query.json()["id"]

    resp = await client.get(f"/api/v1/queries/{query_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == query_id

    resp = await client.get(f"/api/v1/queries?study_id={study_id}")
    assert resp.status_code == 200
    assert any(q["id"] == query_id for q in resp.json())


# Agents
async def test_agent_subject_lifecycle(client: AsyncClient) -> None:
    agent = await client.post(
        "/api/v1/agents/subjects",
        json={
            "principal_id": "agent://cov/v1",
            "persona_key": "cov_persona",
            "superpersona_contract_id": "contract-cov",
            "model_version": "v1.0.0",
            "agent_owner_id": "owner_1",
            "autonomy_level": "shadow",
            "safety_class": "low",
        },
    )
    agent_id = agent.json()["id"]

    resp = await client.get(f"/api/v1/agents/subjects/{agent_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == agent_id

    resp = await client.get("/api/v1/agents/subjects")
    assert resp.status_code == 200
    assert any(a["id"] == agent_id for a in resp.json())

    resp = await client.patch(f"/api/v1/agents/subjects/{agent_id}", json={"autonomy_level": "supervised"})
    assert resp.status_code == 200
    assert resp.json()["autonomy_level"] == "supervised"

    resp = await client.post(
        f"/api/v1/agents/subjects/{agent_id}/consent-contracts",
        json={
            "agent_subject_id": agent_id,
            "allowed_systems": ["ctms"],
            "withdrawal_mechanism": "api",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["withdrawal_mechanism"] == "api"


async def test_agent_cohort_and_trial_arm(client: AsyncClient) -> None:
    agent = await client.post(
        "/api/v1/agents/subjects",
        json={
            "principal_id": "agent://cov2/v1",
            "persona_key": "cov2_persona",
            "superpersona_contract_id": "contract-cov2",
            "model_version": "v1.0.0",
            "agent_owner_id": "owner_1",
            "autonomy_level": "shadow",
            "safety_class": "low",
        },
    )
    agent_id = agent.json()["id"]
    cohort = await client.post(
        "/api/v1/agents/cohorts",
        json={
            "name": "Coverage cohort",
            "cohort_type": "single_agent",
            "capability_profile": "test",
            "model_family": "test_family",
            "evaluation_objective": "coverage",
        },
    )
    cohort_id = cohort.json()["id"]
    resp = await client.post(f"/api/v1/agents/cohorts/{cohort_id}/members", params={"agent_subject_id": agent_id})
    assert resp.status_code == 200
    assert "membership_id" in resp.json()

    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "COV-AGENT-001",
            "title": "Agent study coverage",
            "phase": "I",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    study_id = study.json()["id"]
    resp = await client.post(
        "/api/v1/agents/trial-arms",
        json={"agent_subject_id": agent_id, "study_id": study_id, "randomisation_arm": "arm_a"},
    )
    assert resp.status_code == 200
    assert resp.json()["randomisation_arm"] == "arm_a"


async def test_agent_release_gate(client: AsyncClient) -> None:
    cohort = await client.post(
        "/api/v1/agents/cohorts",
        json={
            "name": "Release cohort",
            "cohort_type": "single_agent",
            "capability_profile": "test",
            "model_family": "test_family",
            "evaluation_objective": "release",
        },
    )
    cohort_id = cohort.json()["id"]
    resp = await client.get(f"/api/v1/agents/cohorts/{cohort_id}/release-gate")
    assert resp.status_code == 200
    assert resp.json()["cohort_id"] == cohort_id
