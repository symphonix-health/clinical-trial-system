"""Subject enrolment tests."""

from httpx import AsyncClient


async def _create_study_and_site(client: AsyncClient):
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "SUB-001",
            "title": "Subject test",
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
            "site_code": "SUB-01",
            "name": "Site",
            "organisation_id": "org",
            "principal_investigator_id": "pi",
        },
    )
    return study_id, site.json()["id"]


async def test_create_subject(client: AsyncClient) -> None:
    study_id, site_id = await _create_study_and_site(client)
    resp = await client.post(
        "/api/v1/subjects",
        json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-001"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["enrolment_status"] == "screening"
    assert data["subject_number"].startswith("S")


async def test_record_consent(client: AsyncClient) -> None:
    study_id, site_id = await _create_study_and_site(client)
    subject_id = (
        await client.post(
            "/api/v1/subjects",
            json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-002"},
        )
    ).json()["id"]
    resp = await client.post(
        f"/api/v1/subjects/{subject_id}/consent",
        json={"subject_id": subject_id, "consent_version": "v1.0", "consent_date": "2026-01-20T09:00:00"},
    )
    assert resp.status_code == 200
    assert resp.json()["consent_version"] == "v1.0"
    subject = await client.get(f"/api/v1/subjects/{subject_id}")
    assert subject.json()["enrolment_status"] == "enrolled"


async def test_withdraw_subject(client: AsyncClient) -> None:
    study_id, site_id = await _create_study_and_site(client)
    subject_id = (
        await client.post(
            "/api/v1/subjects",
            json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-003"},
        )
    ).json()["id"]
    await client.post(
        f"/api/v1/subjects/{subject_id}/consent",
        json={"subject_id": subject_id, "consent_version": "v1.0", "consent_date": "2026-01-20T09:00:00"},
    )
    resp = await client.post(f"/api/v1/subjects/{subject_id}/withdraw", params={"reason": "personal"})
    assert resp.status_code == 200
    assert resp.json()["enrolment_status"] == "withdrawn"


async def test_randomise_subject(client: AsyncClient) -> None:
    study_id, site_id = await _create_study_and_site(client)
    subject_id = (
        await client.post(
            "/api/v1/subjects",
            json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-004"},
        )
    ).json()["id"]
    await client.post(
        f"/api/v1/subjects/{subject_id}/consent",
        json={"subject_id": subject_id, "consent_version": "v1.0", "consent_date": "2026-01-20T09:00:00"},
    )
    resp = await client.post(f"/api/v1/subjects/{subject_id}/randomise", json={})
    assert resp.status_code == 200
    assert resp.json()["randomisation_arm"] in ("arm_a", "arm_b")
