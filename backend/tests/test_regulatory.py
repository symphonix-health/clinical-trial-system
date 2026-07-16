"""Regulatory document and eTMF tests."""

from httpx import AsyncClient


async def test_create_regulatory_document(client: AsyncClient) -> None:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "REG-001",
            "title": "Regulatory test",
            "phase": "II",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    study_id = study.json()["id"]
    resp = await client.post(
        "/api/v1/regulatory-documents",
        json={
            "study_id": study_id,
            "document_type": "ethics_approval",
            "document_reference": "ETHICS-001.pdf",
            "version": "1",
            "expiry_date": "2026-12-31",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["document_type"] == "ethics_approval"


async def test_etmf_report(client: AsyncClient) -> None:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "REG-002",
            "title": "eTMF test",
            "phase": "II",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    study_id = study.json()["id"]
    await client.post(
        "/api/v1/regulatory-documents",
        json={
            "study_id": study_id,
            "document_type": "protocol",
            "document_reference": "PROTO-v1.pdf",
            "version": "v1.0",
        },
    )
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
    assert resp.status_code == 200
    data = resp.json()
    assert data["expired_count"] >= 1
