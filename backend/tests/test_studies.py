"""Study lifecycle tests."""

from httpx import AsyncClient


async def test_create_study(client: AsyncClient) -> None:
    payload = {
        "protocol_number": "TEST-001",
        "title": "Test study",
        "phase": "I",
        "indication": "test indication",
        "therapeutic_area": "oncology",
        "sponsor": "Test Sponsor",
        "planned_sites": 2,
        "planned_subjects": 10,
    }
    resp = await client.post("/api/v1/studies", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["protocol_number"] == "TEST-001"
    assert data["status"] == "draft"


async def test_list_studies(seeded_client: AsyncClient) -> None:
    resp = await seeded_client.get("/api/v1/studies")
    assert resp.status_code == 200
    assert len(resp.json()) >= 3


async def test_approve_study(client: AsyncClient) -> None:
    payload = {
        "protocol_number": "TEST-002",
        "title": "Test study 2",
        "phase": "II",
        "indication": "test",
        "therapeutic_area": "cardiology",
        "sponsor": "Sponsor",
    }
    created = await client.post("/api/v1/studies", json=payload)
    study_id = created.json()["id"]
    resp = await client.post(f"/api/v1/studies/{study_id}/approve", params={"version_number": "v1.0"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


async def test_update_study(client: AsyncClient) -> None:
    payload = {
        "protocol_number": "TEST-003",
        "title": "Before",
        "phase": "I",
        "indication": "x",
        "therapeutic_area": "neurology",
        "sponsor": "Sponsor",
    }
    created = await client.post("/api/v1/studies", json=payload)
    study_id = created.json()["id"]
    resp = await client.patch(f"/api/v1/studies/{study_id}", json={"title": "After"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "After"
