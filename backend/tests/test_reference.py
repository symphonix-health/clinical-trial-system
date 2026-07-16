"""Reference valueset tests."""

from httpx import AsyncClient


async def test_reference_valuesets(client: AsyncClient) -> None:
    for name in ("therapeutic_areas", "phases", "document_types", "ae_seriousness", "arena_metric_names"):
        resp = await client.get(f"/api/v1/reference/{name}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == name
        assert len(data["values"]) > 0
