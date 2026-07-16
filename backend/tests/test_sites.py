"""Site activation tests."""

from httpx import AsyncClient


async def test_create_site(client: AsyncClient) -> None:
    study_payload = {
        "protocol_number": "SITE-001",
        "title": "Site test",
        "phase": "I",
        "indication": "x",
        "therapeutic_area": "oncology",
        "sponsor": "Sponsor",
    }
    study = await client.post("/api/v1/studies", json=study_payload)
    study_id = study.json()["id"]
    site_payload = {
        "study_id": study_id,
        "site_code": "SITE-01",
        "name": "Site One",
        "organisation_id": "org1",
        "principal_investigator_id": "pi1",
    }
    resp = await client.post("/api/v1/sites", json=site_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["activation_status"] == "pending"


async def test_site_checklist(client: AsyncClient) -> None:
    study_payload = {
        "protocol_number": "SITE-002",
        "title": "Checklist test",
        "phase": "I",
        "indication": "x",
        "therapeutic_area": "oncology",
        "sponsor": "Sponsor",
    }
    study_id = (await client.post("/api/v1/studies", json=study_payload)).json()["id"]
    site_payload = {
        "study_id": study_id,
        "site_code": "SITE-02",
        "name": "Site Two",
        "organisation_id": "org2",
        "principal_investigator_id": "pi2",
    }
    site_id = (await client.post("/api/v1/sites", json=site_payload)).json()["id"]
    resp = await client.get(f"/api/v1/sites/{site_id}/checklist")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 5


async def test_activate_site(client: AsyncClient) -> None:
    study_payload = {
        "protocol_number": "SITE-003",
        "title": "Activate test",
        "phase": "I",
        "indication": "x",
        "therapeutic_area": "oncology",
        "sponsor": "Sponsor",
    }
    study_id = (await client.post("/api/v1/studies", json=study_payload)).json()["id"]
    site_payload = {
        "study_id": study_id,
        "site_code": "SITE-03",
        "name": "Site Three",
        "organisation_id": "org3",
        "principal_investigator_id": "pi3",
    }
    site_id = (await client.post("/api/v1/sites", json=site_payload)).json()["id"]
    resp = await client.patch(f"/api/v1/sites/{site_id}", json={"activation_status": "activated"})
    assert resp.status_code == 200
    assert resp.json()["activation_status"] == "activated"
