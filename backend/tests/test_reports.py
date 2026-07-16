"""Report generation tests."""

from httpx import AsyncClient


async def _seed_data_for_report(client: AsyncClient):
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "REP-001",
            "title": "Report test",
            "phase": "II",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
            "planned_subjects": 10,
        },
    )
    study_id = study.json()["id"]
    site = await client.post(
        "/api/v1/sites",
        json={
            "study_id": study_id,
            "site_code": "REP-01",
            "name": "Site",
            "organisation_id": "org",
            "principal_investigator_id": "pi",
        },
    )
    site_id = site.json()["id"]
    for i in range(3):
        await client.post(
            "/api/v1/subjects",
            json={"study_id": study_id, "site_id": site_id, "screening_id": f"SCR-R{i}"},
        )
    return study_id, site_id


async def test_recruitment_report(client: AsyncClient) -> None:
    study_id, _ = await _seed_data_for_report(client)
    resp = await client.get(f"/api/v1/reports/recruitment/{study_id}")
    assert resp.status_code == 200
    assert resp.json()["study_id"] == study_id


async def test_safety_report(client: AsyncClient) -> None:
    study_id, site_id = await _seed_data_for_report(client)
    subject_id = (
        await client.post(
            "/api/v1/subjects",
            json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-SAFE"},
        )
    ).json()["id"]
    await client.post(
        "/api/v1/adverse-events",
        json={
            "study_id": study_id,
            "subject_id": subject_id,
            "onset_date": "2026-04-01",
            "severity": "severe",
            "seriousness": "serious",
            "causality": "related",
            "susar_flag": True,
        },
    )
    resp = await client.get(f"/api/v1/reports/safety/{study_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_aes"] >= 1
    assert data["pending_susars"] >= 1


async def test_ip_accountability_report(client: AsyncClient) -> None:
    study_id, site_id = await _seed_data_for_report(client)
    product_id = (
        await client.post(
            "/api/v1/ip/products",
            json={
                "sku": "REP-IP",
                "name": "Rep drug",
                "lot_number": "LOT-R",
                "expiry_date": "2027-01-01",
                "storage_conditions": "2-8C",
                "accountability_unit": "capsule",
                "quantity_on_hand": 100,
                "site_id": site_id,
            },
        )
    ).json()["id"]
    subject_id = (
        await client.post(
            "/api/v1/subjects",
            json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-IP"},
        )
    ).json()["id"]
    await client.post(
        "/api/v1/ip/dispenses",
        json={"subject_id": subject_id, "product_id": product_id, "quantity_dispensed": 10, "quantity_returned": 2},
    )
    resp = await client.get(f"/api/v1/reports/ip-accountability/{study_id}/{site_id}")
    assert resp.status_code == 200
    assert resp.json()["dispensed"] == 10
    assert resp.json()["returned"] == 2
