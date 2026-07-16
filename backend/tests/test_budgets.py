"""Budget and invoice tests."""

from httpx import AsyncClient


async def _create_study(client: AsyncClient):
    return (
        await client.post(
            "/api/v1/studies",
            json={
                "protocol_number": "BUD-001",
                "title": "Budget test",
                "phase": "II",
                "indication": "x",
                "therapeutic_area": "oncology",
                "sponsor": "Sponsor",
            },
        )
    ).json()["id"]


async def test_create_budget(client: AsyncClient) -> None:
    study_id = await _create_study(client)
    resp = await client.post(
        "/api/v1/budgets",
        json={"study_id": study_id, "budget_category": "per_subject", "planned_amount": 100000},
    )
    assert resp.status_code == 200
    assert resp.json()["planned_amount"] == 100000


async def test_update_budget_actual(client: AsyncClient) -> None:
    study_id = await _create_study(client)
    budget_id = (
        await client.post(
            "/api/v1/budgets",
            json={"study_id": study_id, "budget_category": "procedures", "planned_amount": 50000},
        )
    ).json()["id"]
    resp = await client.patch(f"/api/v1/budgets/{budget_id}", json={"actual_amount": 15000})
    assert resp.status_code == 200
    assert resp.json()["actual_amount"] == 15000


async def test_create_invoice(client: AsyncClient) -> None:
    study_id = await _create_study(client)
    resp = await client.post(
        "/api/v1/budgets/invoices",
        json={"study_id": study_id, "sponsor_id": "sponsor_1", "amount": 25000},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"
