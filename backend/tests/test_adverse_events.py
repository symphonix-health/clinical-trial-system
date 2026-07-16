"""Adverse event and SUSAR tests."""

from httpx import AsyncClient


async def _create_study(client: AsyncClient):
    resp = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "AE-001",
            "title": "AE test",
            "phase": "III",
            "indication": "x",
            "therapeutic_area": "cardiology",
            "sponsor": "Sponsor",
        },
    )
    return resp.json()["id"]


async def _create_subject(client: AsyncClient, study_id: int):
    site = await client.post(
        "/api/v1/sites",
        json={
            "study_id": study_id,
            "site_code": "AE-01",
            "name": "Site",
            "organisation_id": "org",
            "principal_investigator_id": "pi",
        },
    )
    site_id = site.json()["id"]
    subject = await client.post(
        "/api/v1/subjects",
        json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-AE001"},
    )
    return subject.json()["id"]


async def test_create_adverse_event(client: AsyncClient) -> None:
    study_id = await _create_study(client)
    subject_id = await _create_subject(client, study_id)
    resp = await client.post(
        "/api/v1/adverse-events",
        json={
            "study_id": study_id,
            "subject_id": subject_id,
            "onset_date": "2026-04-01",
            "severity": "moderate",
            "seriousness": "non_serious",
            "causality": "unrelated",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "reported"


async def test_susar_deadline_computed(client: AsyncClient) -> None:
    study_id = await _create_study(client)
    subject_id = await _create_subject(client, study_id)
    resp = await client.post(
        "/api/v1/adverse-events",
        json={
            "study_id": study_id,
            "subject_id": subject_id,
            "onset_date": "2026-04-01",
            "severity": "severe",
            "seriousness": "life_threatening",
            "causality": "related",
            "susar_flag": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["susar_flag"] is True
    assert data["regulatory_report_deadline"] is not None


async def test_update_ae_status(client: AsyncClient) -> None:
    study_id = await _create_study(client)
    subject_id = await _create_subject(client, study_id)
    ae_id = (
        await client.post(
            "/api/v1/adverse-events",
            json={
                "study_id": study_id,
                "subject_id": subject_id,
                "onset_date": "2026-04-01",
                "severity": "moderate",
                "seriousness": "non_serious",
                "causality": "unrelated",
            },
        )
    ).json()["id"]
    resp = await client.patch(f"/api/v1/adverse-events/{ae_id}", json={"status": "assessed", "narrative": "Narrative text"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "assessed"
