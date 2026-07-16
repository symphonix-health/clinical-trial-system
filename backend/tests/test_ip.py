"""IP accountability tests."""

from httpx import AsyncClient


async def _create_site(client: AsyncClient):
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "IP-001",
            "title": "IP test",
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
            "site_code": "IP-01",
            "name": "Site",
            "organisation_id": "org",
            "principal_investigator_id": "pi",
        },
    )
    return study_id, site.json()["id"]


async def test_create_product(client: AsyncClient) -> None:
    _, site_id = await _create_site(client)
    resp = await client.post(
        "/api/v1/ip/products",
        json={
            "sku": "SKU-001",
            "name": "Test drug",
            "lot_number": "LOT-001",
            "expiry_date": "2027-01-01",
            "storage_conditions": "2-8C",
            "accountability_unit": "tablet",
            "quantity_on_hand": 100,
            "site_id": site_id,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["quantity_on_hand"] == 100


async def test_shipment_receipt_updates_inventory(client: AsyncClient) -> None:
    _, site_id = await _create_site(client)
    product_id = (
        await client.post(
            "/api/v1/ip/products",
            json={
                "sku": "SKU-002",
                "name": "Test drug 2",
                "lot_number": "LOT-002",
                "expiry_date": "2027-01-01",
                "storage_conditions": "2-8C",
                "accountability_unit": "tablet",
                "quantity_on_hand": 0,
                "site_id": site_id,
            },
        )
    ).json()["id"]
    shipment_id = (
        await client.post(
            "/api/v1/ip/shipments",
            json={
                "shipment_id": "SHIP-001",
                "product_id": product_id,
                "from_organisation": "Sponsor",
                "to_site_id": site_id,
                "quantity_shipped": 50,
            },
        )
    ).json()["id"]
    resp = await client.post(f"/api/v1/ip/shipments/{shipment_id}/receive", params={"received_by": "pharm1", "condition_ok": True})
    assert resp.status_code == 200
    product = await client.get(f"/api/v1/ip/products/{product_id}")
    assert product.json()["quantity_on_hand"] == 50


async def test_dispense_decrements_inventory(client: AsyncClient) -> None:
    _, site_id = await _create_site(client)
    study_id = (await client.get(f"/api/v1/sites/{site_id}")).json()["study_id"]
    subject_id = (
        await client.post(
            "/api/v1/subjects",
            json={"study_id": study_id, "site_id": site_id, "screening_id": "SCR-IP001"},
        )
    ).json()["id"]
    product_id = (
        await client.post(
            "/api/v1/ip/products",
            json={
                "sku": "SKU-003",
                "name": "Test drug 3",
                "lot_number": "LOT-003",
                "expiry_date": "2027-01-01",
                "storage_conditions": "2-8C",
                "accountability_unit": "tablet",
                "quantity_on_hand": 100,
                "site_id": site_id,
            },
        )
    ).json()["id"]
    resp = await client.post(
        "/api/v1/ip/dispenses",
        json={"subject_id": subject_id, "product_id": product_id, "quantity_dispensed": 30},
    )
    assert resp.status_code == 200
    product = await client.get(f"/api/v1/ip/products/{product_id}")
    assert product.json()["quantity_on_hand"] == 70
