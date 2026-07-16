"""Query resolution tests."""

from httpx import AsyncClient


async def _create_study(client: AsyncClient):
    return (
        await client.post(
            "/api/v1/studies",
            json={
                "protocol_number": "Q-001",
                "title": "Query test",
                "phase": "II",
                "indication": "x",
                "therapeutic_area": "oncology",
                "sponsor": "Sponsor",
            },
        )
    ).json()["id"]


async def test_create_query(client: AsyncClient) -> None:
    study_id = await _create_study(client)
    resp = await client.post(
        "/api/v1/queries",
        json={"study_id": study_id, "raised_by": "cra_1", "assigned_to": "crc_1"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "open"


async def test_resolve_query(client: AsyncClient) -> None:
    study_id = await _create_study(client)
    query_id = (
        await client.post(
            "/api/v1/queries",
            json={"study_id": study_id, "raised_by": "cra_1", "assigned_to": "crc_1"},
        )
    ).json()["id"]
    resp = await client.patch(
        f"/api/v1/queries/{query_id}",
        json={"status": "resolved", "resolution": "Clarified with PI"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"
