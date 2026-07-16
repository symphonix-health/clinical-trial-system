"""Edge-case and error-path coverage tests."""

from httpx import AsyncClient


async def test_get_nonexistent_study(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/studies/99999")
    assert resp.status_code == 404


async def test_update_nonexistent_study(client: AsyncClient) -> None:
    resp = await client.patch("/api/v1/studies/99999", json={"title": "x"})
    assert resp.status_code == 404


async def test_approve_nonexistent_study(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/studies/99999/approve?version_number=1")
    assert resp.status_code == 404


async def test_get_nonexistent_site(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/sites/99999")
    assert resp.status_code == 404


async def test_activate_nonexistent_site(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/sites/99999/activate")
    assert resp.status_code == 404


async def test_get_nonexistent_subject(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/subjects/99999")
    assert resp.status_code == 404


async def test_update_nonexistent_subject(client: AsyncClient) -> None:
    resp = await client.patch("/api/v1/subjects/99999", json={"status": "withdrawn"})
    assert resp.status_code == 404


async def test_withdraw_nonexistent_subject(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/subjects/99999/withdraw?reason=adverse_event")
    assert resp.status_code == 404


async def test_randomise_nonexistent_subject(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/subjects/99999/randomise", json={"stratification_factors": {}})
    assert resp.status_code == 404


async def test_get_nonexistent_visit(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/visits/99999")
    assert resp.status_code == 404


async def test_update_nonexistent_visit(client: AsyncClient) -> None:
    resp = await client.patch("/api/v1/visits/99999", json={"status": "completed"})
    assert resp.status_code == 404


async def test_get_nonexistent_adverse_event(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/adverse-events/99999")
    assert resp.status_code == 404


async def test_update_nonexistent_adverse_event(client: AsyncClient) -> None:
    resp = await client.patch("/api/v1/adverse-events/99999", json={"severity": "mild"})
    assert resp.status_code == 404


async def test_get_nonexistent_agent_subject(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/agents/subjects/99999")
    assert resp.status_code == 404


async def test_update_nonexistent_agent_subject(client: AsyncClient) -> None:
    resp = await client.patch("/api/v1/agents/subjects/99999", json={"enrolment_status": "enrolled"})
    assert resp.status_code == 404


async def test_complete_nonexistent_agent_run(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/agents/runs/99999/complete", json={})
    assert resp.status_code == 404


async def test_update_nonexistent_budget(client: AsyncClient) -> None:
    resp = await client.patch("/api/v1/budgets/99999", json={"actual_cost": 100})
    assert resp.status_code == 404


async def test_get_nonexistent_ip_product(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/ip/products/99999")
    assert resp.status_code == 404


async def test_get_nonexistent_query(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/queries/99999")
    assert resp.status_code == 404


async def test_close_nonexistent_query(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/queries/99999/close")
    assert resp.status_code == 404


async def test_list_studies_pagination(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/studies?skip=0&limit=5")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_list_subjects_filter(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/subjects?status=enrolled")
    assert resp.status_code == 200


async def test_list_agent_subjects_filter(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/agents/subjects?enrolled_study_id=1")
    assert resp.status_code == 200


async def test_list_agent_metrics(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/agents/runs/99999/metrics")
    assert resp.status_code == 200


async def test_etmf_report_empty_study(client: AsyncClient) -> None:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "ETMF-EMPTY-001",
            "title": "Empty eTMF",
            "phase": "I",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    study_id = study.json()["id"]
    resp = await client.get(f"/api/v1/reports/etmf/{study_id}")
    assert resp.status_code == 200
    assert resp.json()["expired_count"] == 0


async def test_recruitment_report_empty_study(client: AsyncClient) -> None:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "RECR-EMPTY-001",
            "title": "Empty recruitment",
            "phase": "I",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    study_id = study.json()["id"]
    resp = await client.get(f"/api/v1/reports/recruitment/{study_id}")
    assert resp.status_code == 200


async def test_reference_valueset(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/reference/visit_status")
    assert resp.status_code == 200


async def test_update_nonexistent_site(client: AsyncClient) -> None:
    resp = await client.patch("/api/v1/sites/99999", json={"name": "x"})
    assert resp.status_code == 404


async def test_update_nonexistent_checklist_task(client: AsyncClient) -> None:
    resp = await client.patch("/api/v1/sites/99999/checklist/missing_task?status=complete")
    assert resp.status_code == 404


async def test_record_consent_nonexistent_subject(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/subjects/99999/consent",
        json={
            "subject_id": 99999,
            "consent_version": "v1",
            "consent_date": "2026-01-01T00:00:00",
            "document_reference": "x.pdf",
        },
    )
    assert resp.status_code == 404


async def test_create_protocol_version(client: AsyncClient) -> None:
    study = await client.post(
        "/api/v1/studies",
        json={
            "protocol_number": "PV-001",
            "title": "Protocol version test",
            "phase": "I",
            "indication": "x",
            "therapeutic_area": "oncology",
            "sponsor": "Sponsor",
        },
    )
    study_id = study.json()["id"]
    resp = await client.post(
        f"/api/v1/studies/{study_id}/protocol-versions",
        json={"study_id": study_id, "version_number": "v2", "approval_date": "2026-01-01"},
    )
    assert resp.status_code == 200
    assert resp.json()["study_id"] == study_id


async def test_webhook_imaging_result_valid(client: AsyncClient) -> None:
    import hashlib, hmac

    from app.config import get_settings

    settings = get_settings()
    body = '{"event": "imaging.result", "data": {"study_id": 1}}'
    sig = hmac.new(settings.webhook_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    resp = await client.post(
        "/api/v1/webhooks/bullettrain/imaging-result",
        content=body,
        headers={"x-bt-signature": f"sha256={sig}", "content-type": "application/json"},
    )
    assert resp.status_code == 200


async def test_webhook_dispense_event_invalid(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/webhooks/bullettrain/dispense-event",
        json={"event": "dispense", "data": {}},
        headers={"x-bt-signature": "sha256=bad"},
    )
    assert resp.status_code == 401


async def test_webhook_agent_task_completed(client: AsyncClient) -> None:
    import hashlib, hmac

    from app.config import get_settings

    settings = get_settings()
    body = '{"event": "agent.task.completed", "data": {"task_id": "t1"}}'
    sig = hmac.new(settings.webhook_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    resp = await client.post(
        "/api/v1/webhooks/bullettrain/agent-task-completed",
        content=body,
        headers={"x-bt-signature": f"sha256={sig}", "content-type": "application/json"},
    )
    assert resp.status_code == 200


async def test_webhook_agent_escalation(client: AsyncClient) -> None:
    import hashlib, hmac

    from app.config import get_settings

    settings = get_settings()
    body = '{"event": "agent.escalation", "data": {"reason": "safety"}}'
    sig = hmac.new(settings.webhook_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    resp = await client.post(
        "/api/v1/webhooks/bullettrain/agent-escalation",
        content=body,
        headers={"x-bt-signature": f"sha256={sig}", "content-type": "application/json"},
    )
    assert resp.status_code == 200


async def test_webhook_council_synthesis(client: AsyncClient) -> None:
    import hashlib, hmac

    from app.config import get_settings

    settings = get_settings()
    body = '{"event": "council.synthesis", "data": {"recommendation": "continue"}}'
    sig = hmac.new(settings.webhook_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    resp = await client.post(
        "/api/v1/webhooks/bullettrain/council-synthesis",
        content=body,
        headers={"x-bt-signature": f"sha256={sig}", "content-type": "application/json"},
    )
    assert resp.status_code == 200
