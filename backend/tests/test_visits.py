"""Visit scheduling tests."""

from httpx import AsyncClient


async def _create_subject(client: AsyncClient):
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "VIS-001",
            "title": "Visit test",
            "phase": "II",
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
            "site_code": "VIS-01",
            "name": "Site",
            "organisation_id": "org",
            "principal_investigator_id": "pi",
        },
    )
    site_id = site.json()["id"]
    subject = await client.post(
        "/api/v1/subjects",
        json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-V001"},
    )
    return subject.json()["id"]


async def test_create_visit(client: AsyncClient) -> None:
    subject_id = await _create_subject(client)
    resp = await client.post(
        "/api/v1/visits",
        json={
            "subject_id": subject_id,
            "visit_definition_id": "V1",
            "scheduled_date": "2026-05-01",
            "window_min_date": "2026-04-29",
            "window_max_date": "2026-05-03",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "scheduled"


async def test_update_visit_outside_window_creates_deviation(client: AsyncClient) -> None:
    subject_id = await _create_subject(client)
    visit_id = (
        await client.post(
            "/api/v1/visits",
            json={
                "subject_id": subject_id,
                "visit_definition_id": "V1",
                "scheduled_date": "2026-05-01",
                "window_min_date": "2026-04-29",
                "window_max_date": "2026-05-03",
            },
        )
    ).json()["id"]
    resp = await client.patch(
        f"/api/v1/visits/{visit_id}",
        json={"actual_date": "2026-05-10", "status": "completed"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


async def test_flag_missed_visits(client: AsyncClient) -> None:
    subject_id = await _create_subject(client)
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
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
