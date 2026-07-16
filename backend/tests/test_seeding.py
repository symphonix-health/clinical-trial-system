"""Seeding tests."""

from httpx import AsyncClient


async def test_seeded_studies(seeded_client: AsyncClient) -> None:
    resp = await seeded_client.get("/api/v1/studies")
    assert resp.status_code == 200
    studies = resp.json()
    assert len(studies) >= 3
    phases = {s["phase"] for s in studies}
    assert "II" in phases


async def test_seeded_subjects(seeded_client: AsyncClient) -> None:
    resp = await seeded_client.get("/api/v1/subjects")
    assert resp.status_code == 200
    subjects = resp.json()
    assert len(subjects) >= 40


async def test_seeded_adverse_events(seeded_client: AsyncClient) -> None:
    resp = await seeded_client.get("/api/v1/adverse-events")
    assert resp.status_code == 200
    assert len(resp.json()) >= 5


async def test_seeded_agent_subjects(seeded_client: AsyncClient) -> None:
    resp = await seeded_client.get("/api/v1/agents/subjects")
    assert resp.status_code == 200
    assert len(resp.json()) >= 9
