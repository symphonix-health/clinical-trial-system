"""National-capability tests (REQ-CTS-NAT-001..008).

Covers the paths the canonical matrix rows do not reach: the KE/US packs,
country-pack validation, the registry rejection branch, delegation expiry
re-evaluation, the overdue-safety report, and the reimbursement policy edges.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest
from httpx import AsyncClient

from app.country_packs import loader as pack_loader

PACK_DIR = Path(pack_loader.__file__).resolve().parent / "packs"


# --- REQ-CTS-NAT-001 / FR-C-191: packs are versioned, sourced data ---------


def test_every_pack_declares_version_effective_date_and_sources() -> None:
    codes = {p["code"] for p in pack_loader.list_packs()}
    assert codes == {"IE", "UK", "KE", "US"}, codes
    for pack in pack_loader.list_packs():
        dt.date.fromisoformat(pack["effective_from"])
        assert pack["pack_version"], pack["code"]
        assert pack["sources"], pack["code"]
        for source in pack["sources"]:
            assert source["url"].startswith("http"), source
            dt.date.fromisoformat(source["accessed"])


def test_pack_on_disk_matches_the_loaded_pack() -> None:
    """The loader must not synthesise anything the file does not declare."""

    raw = json.loads((PACK_DIR / "ie.json").read_text(encoding="utf-8"))
    assert pack_loader.get_pack("IE") == raw


def test_missing_statutory_section_fails_loading() -> None:
    """A pack that drops a statutory section must raise, not lose a deadline."""

    broken = json.loads((PACK_DIR / "ie.json").read_text(encoding="utf-8"))
    del broken["safety_reporting"]
    with pytest.raises(pack_loader.CountryPackError, match="safety_reporting"):
        pack_loader._validate("IE", broken)


def test_non_integer_deadline_fails_loading() -> None:
    broken = json.loads((PACK_DIR / "uk.json").read_text(encoding="utf-8"))
    broken["safety_reporting"]["susar_other_days"] = "fifteen"
    with pytest.raises(pack_loader.CountryPackError, match="susar_other_days"):
        pack_loader._validate("UK", broken)


def test_source_without_provenance_fails_loading() -> None:
    broken = json.loads((PACK_DIR / "us.json").read_text(encoding="utf-8"))
    broken["sources"][0].pop("accessed")
    with pytest.raises(pack_loader.CountryPackError, match="accessed"):
        pack_loader._validate("US", broken)


def test_schema_version_and_code_are_checked() -> None:
    broken = json.loads((PACK_DIR / "ke.json").read_text(encoding="utf-8"))
    broken["schema_version"] = "SOMETHING_ELSE"
    with pytest.raises(pack_loader.CountryPackError, match="schema_version"):
        pack_loader._validate("KE", broken)
    mislabelled = json.loads((PACK_DIR / "ke.json").read_text(encoding="utf-8"))
    mislabelled["code"] = "KX"
    with pytest.raises(pack_loader.CountryPackError, match="declares code"):
        pack_loader._validate("KE", mislabelled)
    missing = json.loads((PACK_DIR / "ke.json").read_text(encoding="utf-8"))
    missing.pop("pack_version")
    with pytest.raises(pack_loader.CountryPackError, match="pack_version"):
        pack_loader._validate("KE", missing)


def test_unknown_jurisdiction_raises() -> None:
    with pytest.raises(pack_loader.CountryPackError, match="unknown jurisdiction"):
        pack_loader.get_pack("ZZ")


# --- REQ-CTS-NAT-006 / FR-C-161 / FR-C-162: the SUSAR clock ----------------


@pytest.mark.parametrize("jurisdiction", ["IE", "UK", "KE", "US"])
def test_fatal_unexpected_related_is_a_seven_day_susar(jurisdiction: str) -> None:
    """The regression that motivated the fix.

    The previous rule gave a FATAL reaction 1 day and never flagged it a SUSAR
    at all, because it tested ``seriousness == "life_threatening"`` only.
    """

    assert pack_loader.is_susar("fatal", "unexpected", "related") is True
    assert (
        pack_loader.susar_deadline_days("fatal", "unexpected", "related", jurisdiction)
        == 7
    )
    assert (
        pack_loader.susar_deadline_days(
            "life_threatening", "unexpected", "probably_related", jurisdiction
        )
        == 7
    )


@pytest.mark.parametrize("jurisdiction", ["IE", "UK", "KE", "US"])
def test_other_susars_and_serious_events_get_fifteen_days(jurisdiction: str) -> None:
    assert (
        pack_loader.susar_deadline_days(
            "serious", "unexpected", "possibly_related", jurisdiction
        )
        == 15
    )
    # Serious but EXPECTED is not a SUSAR; it still carries the serious clock.
    assert pack_loader.is_susar("serious", "expected", "related") is False
    assert (
        pack_loader.susar_deadline_days("serious", "expected", "related", jurisdiction)
        == 15
    )


def test_non_serious_events_carry_no_statutory_clock() -> None:
    assert pack_loader.susar_deadline_days("non_serious", "unexpected", "related") is None
    assert pack_loader.is_susar("non_serious", "unexpected", "related") is False
    # Unrelated events are not suspected reactions, so not SUSARs.
    assert pack_loader.is_susar("fatal", "unexpected", "unrelated") is False


def test_registry_identifier_validation_is_per_jurisdiction() -> None:
    assert pack_loader.validate_registry_identifier("ISRCTN12345678", "UK") is True
    assert pack_loader.validate_registry_identifier("NCT01234567", "UK") is False
    assert pack_loader.validate_registry_identifier("NCT01234567", "US") is True
    assert pack_loader.validate_registry_identifier("PACTR202601123456789", "KE") is True
    assert pack_loader.validate_registry_identifier("2026-512345-21-00", "IE") is True
    assert pack_loader.validate_registry_identifier("ISRCTN12345678", "IE") is False


async def test_adverse_event_records_the_deadline_basis(seeded_client: AsyncClient) -> None:
    studies = (await seeded_client.get("/api/v1/studies")).json()
    ie_study = next(s for s in studies if s["jurisdiction"] == "IE")
    uk_study = next(s for s in studies if s["jurisdiction"] == "UK")
    subject = (
        await seeded_client.get(f"/api/v1/subjects?study_id={uk_study['id']}")
    ).json()[0]
    resp = await seeded_client.post(
        "/api/v1/adverse-events",
        json={
            "study_id": uk_study["id"],
            "subject_id": subject["id"],
            "onset_date": "2026-08-01",
            "severity": "fatal",
            "seriousness": "fatal",
            "causality": "related",
            "expectedness": "unexpected",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["susar_flag"] is True
    assert body["jurisdiction"] == "UK"
    assert body["deadline_basis"] == "UK:1.0.0:susar:7d"
    assert body["regulatory_report_deadline"].startswith("2026-08-08")
    assert ie_study["jurisdiction"] == "IE"


# --- REQ-CTS-NAT-001: registry rejection branch ---------------------------


async def test_registry_rejection_is_recorded_with_its_reason(
    seeded_client: AsyncClient,
) -> None:
    study = (await seeded_client.get("/api/v1/studies")).json()[0]
    submitted = await seeded_client.post(
        "/api/v1/trial-registrations", json={"study_id": study["id"]}
    )
    assert submitted.status_code == 200
    registration_id = submitted.json()["id"]
    rejected = await seeded_client.post(
        f"/api/v1/trial-registrations/{registration_id}/receipt",
        json={
            "registry_identifier": "",
            "receipt_reference": "",
            "accepted": False,
            "rejection_reason": "sponsor legal entity not verified",
        },
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["rejection_reason"] == "sponsor legal entity not verified"
    # A rejected registration is no longer awaiting a receipt.
    again = await seeded_client.post(
        f"/api/v1/trial-registrations/{registration_id}/receipt",
        json={"registry_identifier": "ISRCTN12345678", "receipt_reference": "X"},
    )
    assert again.status_code == 409


async def test_registration_for_an_unknown_study_is_refused(
    seeded_client: AsyncClient,
) -> None:
    resp = await seeded_client.post(
        "/api/v1/trial-registrations", json={"study_id": 999999}
    )
    assert resp.status_code == 404
    assert (
        await seeded_client.post(
            "/api/v1/trial-registrations/999999/receipt",
            json={"registry_identifier": "ISRCTN12345678", "receipt_reference": "X"},
        )
    ).status_code == 404


# --- REQ-CTS-NAT-001: delegation expiry -----------------------------------


async def test_expired_gcp_training_is_reclassified_on_read(
    seeded_client: AsyncClient,
) -> None:
    sites = (await seeded_client.get("/api/v1/sites")).json()
    site = sites[0]
    created = await seeded_client.post(
        "/api/v1/delegations",
        json={
            "site_id": site["id"],
            "person_id": "lapsed_rn_1",
            "person_name": "Lapsed Nurse",
            "role": "research_nurse",
            "delegated_tasks": ["vital_signs"],
            "delegated_by": "dr_sarah_chen",
            "gcp_training_date": "2019-01-01",
            "start_date": "2019-02-01",
        },
    )
    assert created.status_code == 200
    assert created.json()["status"] == "expired"
    listing = (await seeded_client.get(f"/api/v1/delegations?site_id={site['id']}")).json()
    lapsed = next(d for d in listing if d["person_id"] == "lapsed_rn_1")
    assert lapsed["status"] == "expired"
    readiness = (await seeded_client.get(f"/api/v1/sites/{site['id']}/readiness")).json()
    assert any("expired GCP" in reason for reason in readiness["blocking_reasons"])
    assert readiness["ready_for_activation"] is False


async def test_delegation_for_an_unknown_site_is_refused(
    seeded_client: AsyncClient,
) -> None:
    resp = await seeded_client.post(
        "/api/v1/delegations",
        json={
            "site_id": 999999,
            "person_id": "nobody",
            "person_name": "Nobody",
            "role": "research_nurse",
            "delegated_tasks": [],
            "delegated_by": "dr_sarah_chen",
            "gcp_training_date": "2026-01-01",
            "start_date": "2026-01-02",
        },
    )
    assert resp.status_code == 404


# --- REQ-CTS-NAT-002: approvals -------------------------------------------


async def test_approval_requires_a_named_decider_and_a_known_decision(
    seeded_client: AsyncClient,
) -> None:
    study = (await seeded_client.get("/api/v1/studies")).json()[0]
    approval = (
        await seeded_client.post(
            "/api/v1/regulatory-approvals",
            json={
                "study_id": study["id"],
                "authority_kind": "competent_authority",
                "submission_type": "renewal",
                "submission_reference": "CTA-RENEW-0001",
            },
        )
    ).json()
    assert approval["authority_code"] == "MHRA"
    blank = await seeded_client.post(
        f"/api/v1/regulatory-approvals/{approval['id']}/decision",
        json={"decision": "approved", "decided_by": "   "},
    )
    assert blank.status_code == 422
    unknown = await seeded_client.post(
        f"/api/v1/regulatory-approvals/{approval['id']}/decision",
        json={"decision": "probably_fine", "decided_by": "someone"},
    )
    assert unknown.status_code == 422
    ok = await seeded_client.post(
        f"/api/v1/regulatory-approvals/{approval['id']}/decision",
        json={
            "decision": "approved_with_conditions",
            "decided_by": "MHRA assessor R. Iyengar",
            "conditions": [{"reference": "C1", "text": "Submit revised IB"}],
            "approval_expiry": "2028-01-31",
        },
    )
    assert ok.status_code == 200
    assert ok.json()["next_report_due"] is not None
    assert (
        await seeded_client.post(
            "/api/v1/regulatory-approvals/999999/decision",
            json={"decision": "approved", "decided_by": "x"},
        )
    ).status_code == 404


async def test_unknown_submission_type_is_refused(seeded_client: AsyncClient) -> None:
    study = (await seeded_client.get("/api/v1/studies")).json()[0]
    resp = await seeded_client.post(
        "/api/v1/regulatory-approvals",
        json={
            "study_id": study["id"],
            "authority_kind": "ethics",
            "submission_type": "vibes_check",
            "submission_reference": "NOPE-1",
        },
    )
    assert resp.status_code == 422
    assert (
        await seeded_client.post(
            "/api/v1/regulatory-approvals",
            json={
                "study_id": 999999,
                "authority_kind": "ethics",
                "submission_type": "initial",
                "submission_reference": "NOPE-2",
            },
        )
    ).status_code == 404


async def test_approvals_and_reports_falling_due_are_listed(
    seeded_client: AsyncClient,
) -> None:
    study = (await seeded_client.get("/api/v1/studies")).json()[0]
    due = (
        await seeded_client.get(
            f"/api/v1/regulatory-approvals/due/{study['id']}?within_days=3650"
        )
    ).json()
    assert due["expiring_approvals"], due
    assert due["reports_due"], due
    listing = (
        await seeded_client.get(f"/api/v1/regulatory-approvals?study_id={study['id']}")
    ).json()
    assert any(a["decision"] == "approved_with_conditions" for a in listing)
    assert all(
        a["decided_by"] for a in listing if a["decision"] != "pending"
    ), "a decided submission with no named decider would be an unattributed decision"


# --- REQ-CTS-NAT-003: eligibility -----------------------------------------


async def test_all_pass_criteria_derive_an_eligible_outcome(
    seeded_client: AsyncClient,
) -> None:
    study = (await seeded_client.get("/api/v1/studies")).json()[0]
    screening = (
        await seeded_client.post(
            "/api/v1/eligibility-screenings",
            json={
                "study_id": study["id"],
                "candidate_reference": "CAND-UNIT-1",
                "consent_basis": "research_contact_consent",
                "requested_by": "crc_unit",
                "criteria_requested": ["age_18_or_over", "ecog_0_to_2"],
            },
        )
    ).json()
    outcome = await seeded_client.post(
        f"/api/v1/eligibility-screenings/{screening['id']}/outcome",
        json={
            "criteria_evaluated": {"age_18_or_over": True, "ecog_0_to_2": True},
            "reviewed_by": "dr_sarah_chen",
        },
    )
    assert outcome.status_code == 200
    assert outcome.json()["outcome"] == "eligible"


async def test_unevaluable_criterion_derives_pending_review(
    seeded_client: AsyncClient,
) -> None:
    study = (await seeded_client.get("/api/v1/studies")).json()[0]
    screening = (
        await seeded_client.post(
            "/api/v1/eligibility-screenings",
            json={
                "study_id": study["id"],
                "candidate_reference": "CAND-UNIT-2",
                "consent_basis": "research_contact_consent",
                "requested_by": "crc_unit",
                "criteria_requested": ["age_18_or_over", "biopsy_available"],
            },
        )
    ).json()
    outcome = await seeded_client.post(
        f"/api/v1/eligibility-screenings/{screening['id']}/outcome",
        json={
            "criteria_evaluated": {"age_18_or_over": True, "biopsy_available": None},
        },
    )
    assert outcome.status_code == 200
    assert outcome.json()["outcome"] == "pending_review"
    assert (
        await seeded_client.post(
            "/api/v1/eligibility-screenings/999999/outcome",
            json={"criteria_evaluated": {}},
        )
    ).status_code == 404
    assert (
        await seeded_client.post(
            "/api/v1/eligibility-screenings",
            json={
                "study_id": 999999,
                "candidate_reference": "CAND-UNIT-3",
                "consent_basis": "research_contact_consent",
                "requested_by": "crc_unit",
                "criteria_requested": ["age_18_or_over"],
            },
        )
    ).status_code == 404


# --- REQ-CTS-NAT-004: consent propagation ---------------------------------


async def test_withdrawal_reaches_dispensing_visits_and_the_participant_surface(
    seeded_client: AsyncClient,
) -> None:
    """The propagation defect this family exists to close."""

    studies = (await seeded_client.get("/api/v1/studies")).json()
    study = studies[0]
    subject = next(
        s
        for s in (
            await seeded_client.get(f"/api/v1/subjects?study_id={study['id']}")
        ).json()
        if s["enrolment_status"] == "enrolled"
    )
    visit = await seeded_client.post(
        "/api/v1/visits",
        json={
            "subject_id": subject["id"],
            "visit_definition_id": "V9",
            "scheduled_date": "2026-11-01",
            "window_min_date": "2026-10-28",
            "window_max_date": "2026-11-05",
        },
    )
    assert visit.status_code == 200
    before = (
        await seeded_client.get(f"/api/v1/participants/{subject['id']}/summary")
    ).json()
    assert before["upcoming_visits"], "precondition: the subject has a future visit"

    withdrawn = await seeded_client.post(
        f"/api/v1/subjects/{subject['id']}/withdraw"
        "?reason=participant+request&withdrawal_scope=full"
    )
    assert withdrawn.status_code == 200
    assert withdrawn.json()["consent_state"] == "withdrawn"

    after = (
        await seeded_client.get(f"/api/v1/participants/{subject['id']}/summary")
    ).json()
    assert after["consent_state"] == "withdrawn"
    assert after["upcoming_visits"] == []

    blocked = await seeded_client.post(
        "/api/v1/ip/dispenses",
        json={
            "subject_id": subject["id"],
            "product_id": 1,
            "quantity_dispensed": 1,
            "dispensed_by": "pharm_unit",
        },
    )
    assert blocked.status_code == 422
    assert "consent state" in blocked.json()["detail"]

    dispatched = (await seeded_client.get(f"/api/v1/visits/{visit.json()['id']}")).json()
    assert dispatched["status"] == "missed"


async def test_dispense_to_an_unknown_subject_or_product_is_refused(
    seeded_client: AsyncClient,
) -> None:
    subject = (await seeded_client.get("/api/v1/subjects")).json()[0]
    assert (
        await seeded_client.post(
            "/api/v1/ip/dispenses",
            json={
                "subject_id": 999999,
                "product_id": 1,
                "quantity_dispensed": 1,
                "dispensed_by": "pharm_unit",
            },
        )
    ).status_code == 404
    assert (
        await seeded_client.post(
            "/api/v1/ip/dispenses",
            json={
                "subject_id": subject["id"],
                "product_id": 999999,
                "quantity_dispensed": 1,
                "dispensed_by": "pharm_unit",
            },
        )
    ).status_code == 404


async def test_flag_reconsent_for_an_unknown_study_is_refused(
    seeded_client: AsyncClient,
) -> None:
    resp = await seeded_client.post(
        "/api/v1/studies/999999/flag-reconsent?protocol_version=v9.9"
    )
    assert resp.status_code == 404


# --- REQ-CTS-NAT-005: allocation ------------------------------------------


async def test_allocation_list_is_deterministic_and_balanced(
    seeded_client: AsyncClient,
) -> None:
    """Same study + stratum must reproduce the same list, or audit is impossible."""

    from app import crud, models
    from app.database import get_db
    from app.main import app

    gen = app.dependency_overrides[get_db]()
    db = await gen.__anext__()
    study = (await crud.list_studies(db))[0]
    first = await crud.ensure_allocation_list(db, study, "unit|stratum")
    codes = [(a.sequence_number, a.arm_code) for a in first]
    again = await crud.ensure_allocation_list(db, study, "unit|stratum")
    assert [(a.sequence_number, a.arm_code) for a in again] == codes
    # Permuted blocks stay balanced within each block of four.
    for start in range(0, len(codes), 4):
        block = [arm for _, arm in codes[start : start + 4]]
        assert block.count("arm_a") == 2 and block.count("arm_b") == 2, block
    assert crud.stratum_key(None) == "default"
    assert crud.stratum_key({"b": 2, "a": 1}) == "a=1|b=2"
    assert isinstance(first[0], models.RandomisationAllocation)


async def test_allocation_exhaustion_is_refused_not_reused(
    seeded_client: AsyncClient,
) -> None:
    study = (await seeded_client.get("/api/v1/studies")).json()[0]
    site = (await seeded_client.get(f"/api/v1/sites?study_id={study['id']}")).json()[0]
    factors = {"stratum": "tiny"}
    created: list[int] = []
    for index in range(34):
        subject = (
            await seeded_client.post(
                "/api/v1/subjects",
                json={
                    "study_id": study["id"],
                    "site_id": site["id"],
                    "screening_id": f"EXH-{index:03d}",
                },
            )
        ).json()
        created.append(subject["id"])
    statuses = []
    for subject_id in created:
        resp = await seeded_client.post(
            f"/api/v1/subjects/{subject_id}/randomise",
            json={"stratification_factors": factors, "randomised_by": "crc_unit"},
        )
        statuses.append(resp.status_code)
    assert statuses.count(200) == 32, statuses
    assert statuses[-1] == 409
    assert "exhausted" in (
        await seeded_client.post(
            f"/api/v1/subjects/{created[-1]}/randomise",
            json={"stratification_factors": factors},
        )
    ).json()["detail"]


async def test_self_authorised_unblinding_is_flagged(seeded_client: AsyncClient) -> None:
    study = (await seeded_client.get("/api/v1/studies")).json()[0]
    site = (await seeded_client.get(f"/api/v1/sites?study_id={study['id']}")).json()[0]
    subject = (
        await seeded_client.post(
            "/api/v1/subjects",
            json={
                "study_id": study["id"],
                "site_id": site["id"],
                "screening_id": "UNBLIND-001",
            },
        )
    ).json()
    randomised = await seeded_client.post(
        f"/api/v1/subjects/{subject['id']}/randomise",
        json={"stratification_factors": {"stratum": "unblind"}},
    )
    assert randomised.status_code == 200
    event = await seeded_client.post(
        f"/api/v1/subjects/{subject['id']}/unblind",
        json={
            "requested_by": "dr_solo",
            "authorised_by": "dr_solo",
            "reason": "no second authoriser available overnight",
        },
    )
    assert event.status_code == 200
    assert event.json()["self_authorised"] is True
    assert event.json()["arm_revealed"] in {"arm_a", "arm_b"}
    assert (
        await seeded_client.post(
            "/api/v1/subjects/999999/unblind",
            json={"requested_by": "a", "authorised_by": "b", "reason": "c"},
        )
    ).status_code == 404
    assert (
        await seeded_client.get("/api/v1/subjects/999999/allocation")
    ).status_code == 404


# --- REQ-CTS-NAT-006: safety submissions ----------------------------------


async def test_overdue_safety_submission_is_reported(seeded_client: AsyncClient) -> None:
    studies = (await seeded_client.get("/api/v1/studies")).json()
    study = studies[0]
    subject = (
        await seeded_client.get(f"/api/v1/subjects?study_id={study['id']}")
    ).json()[0]
    ae = (
        await seeded_client.post(
            "/api/v1/adverse-events",
            json={
                "study_id": study["id"],
                "subject_id": subject["id"],
                "onset_date": "2026-01-02",
                "severity": "severe",
                "seriousness": "life_threatening",
                "causality": "related",
                "expectedness": "unexpected",
            },
        )
    ).json()
    submission = await seeded_client.post(
        f"/api/v1/adverse-events/{ae['id']}/safety-submissions",
        json={"submitted_by": "safety_officer_unit", "submission_reference": "LATE-1"},
    )
    assert submission.status_code == 200
    overdue = (
        await seeded_client.get(f"/api/v1/reports/safety-overdue/{study['id']}")
    ).json()
    assert overdue["count"] >= 1
    assert any(o["submission_id"] == submission.json()["id"] for o in overdue["overdue"])

    rejected = await seeded_client.post(
        f"/api/v1/safety-submissions/{submission.json()['id']}/acknowledgement",
        json={
            "acknowledgement_reference": "MHRA-REJ-1",
            "accepted": False,
            "rejection_reason": "narrative section incomplete",
        },
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    accepted = await seeded_client.post(
        f"/api/v1/safety-submissions/{submission.json()['id']}/acknowledgement",
        json={"acknowledgement_reference": "MHRA-ACK-1"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "acknowledged"
    after = (
        await seeded_client.get(f"/api/v1/reports/safety-overdue/{study['id']}")
    ).json()
    assert all(
        o["submission_id"] != submission.json()["id"] for o in after["overdue"]
    ), "an acknowledged submission is no longer overdue"
    assert (
        await seeded_client.post(
            f"/api/v1/safety-submissions/{submission.json()['id']}/acknowledgement",
            json={"acknowledgement_reference": "MHRA-ACK-2"},
        )
    ).status_code == 409
    listing = (
        await seeded_client.get(f"/api/v1/adverse-events/{ae['id']}/safety-submissions")
    ).json()
    assert len(listing) == 1


async def test_submission_without_a_statutory_clock_is_refused(
    seeded_client: AsyncClient,
) -> None:
    studies = (await seeded_client.get("/api/v1/studies")).json()
    study = studies[0]
    subject = (
        await seeded_client.get(f"/api/v1/subjects?study_id={study['id']}")
    ).json()[0]
    ae = (
        await seeded_client.post(
            "/api/v1/adverse-events",
            json={
                "study_id": study["id"],
                "subject_id": subject["id"],
                "onset_date": "2026-07-01",
                "severity": "mild",
                "seriousness": "non_serious",
                "causality": "unrelated",
            },
        )
    ).json()
    assert ae["regulatory_report_deadline"] is None
    resp = await seeded_client.post(
        f"/api/v1/adverse-events/{ae['id']}/safety-submissions",
        json={"submitted_by": "safety_officer_unit", "submission_reference": "NS-1"},
    )
    assert resp.status_code == 422
    assert (
        await seeded_client.post(
            "/api/v1/adverse-events/999999/safety-submissions",
            json={"submitted_by": "x", "submission_reference": "y"},
        )
    ).status_code == 404
    assert (
        await seeded_client.post(
            "/api/v1/safety-submissions/999999/acknowledgement",
            json={"acknowledgement_reference": "z"},
        )
    ).status_code == 404


# --- REQ-CTS-NAT-008: participant surface and payments --------------------


async def test_reimbursement_policy_comes_from_the_country_pack(
    seeded_client: AsyncClient,
) -> None:
    studies = (await seeded_client.get("/api/v1/studies")).json()
    ie_study = next(s for s in studies if s["jurisdiction"] == "IE")
    ie_site = (
        await seeded_client.get(f"/api/v1/sites?study_id={ie_study['id']}")
    ).json()[0]
    subject = (
        await seeded_client.post(
            "/api/v1/subjects",
            json={
                "study_id": ie_study["id"],
                "site_id": ie_site["id"],
                "screening_id": "IE-REIMB-001",
            },
        )
    ).json()
    payment = await seeded_client.post(
        "/api/v1/reimbursements",
        json={"subject_id": subject["id"], "category": "travel", "amount": 40.0},
    )
    assert payment.status_code == 200
    assert payment.json()["currency"] == "EUR", "IE pack currency, not the UK default"
    assert payment.json()["exceeds_guidance_cap"] is False
    over = await seeded_client.post(
        "/api/v1/reimbursements",
        json={"subject_id": subject["id"], "category": "inconvenience", "amount": 140.0},
    )
    assert over.status_code == 200
    assert over.json()["exceeds_guidance_cap"] is True
    approved = await seeded_client.post(
        f"/api/v1/reimbursements/{over.json()['id']}/approve?approved_by=finance_ie_1"
    )
    assert approved.status_code == 200
    assert approved.json()["approved_by"] == "finance_ie_1"
    blank = await seeded_client.post(
        f"/api/v1/reimbursements/{payment.json()['id']}/approve?approved_by=%20"
    )
    assert blank.status_code == 422
    assert (
        await seeded_client.post(
            "/api/v1/reimbursements/999999/approve?approved_by=x"
        )
    ).status_code == 404
    assert (
        await seeded_client.post(
            "/api/v1/reimbursements",
            json={"subject_id": 999999, "category": "travel", "amount": 10.0},
        )
    ).status_code == 404


async def test_participant_summary_carries_the_jurisdiction_contract(
    seeded_client: AsyncClient,
) -> None:
    studies = (await seeded_client.get("/api/v1/studies")).json()
    ie_study = next(s for s in studies if s["jurisdiction"] == "IE")
    subject = (
        await seeded_client.get(f"/api/v1/subjects?study_id={ie_study['id']}")
    ).json()[0]
    summary = (
        await seeded_client.get(f"/api/v1/participants/{subject['id']}/summary")
    ).json()
    assert summary["jurisdiction"] == "IE"
    assert summary["reimbursement_currency"] == "EUR"
    assert summary["withdrawal_effective_immediately"] is True
    assert summary["results_available"] is False


# --- Residual policy/refusal branches -------------------------------------


async def test_unknown_jurisdiction_on_a_study_is_refused_not_defaulted(
    seeded_client: AsyncClient,
) -> None:
    """A study pointing at a pack that does not exist must fail loudly.

    Defaulting to the IE pack would silently apply Irish statutory deadlines to
    a trial run somewhere else.
    """

    study = (
        await seeded_client.post(
            "/api/v1/studies",
            json={
                "protocol_number": "NAT-ZZ-0001",
                "title": "Study with an unknown jurisdiction",
                "phase": "I",
                "indication": "x",
                "therapeutic_area": "oncology",
                "sponsor": "Symphonix",
                "jurisdiction": "ZZ",
            },
        )
    ).json()
    resp = await seeded_client.post(
        "/api/v1/trial-registrations", json={"study_id": study["id"]}
    )
    assert resp.status_code == 422
    assert "unknown jurisdiction" in resp.json()["detail"]


async def test_delegation_expiring_after_it_was_written_is_reclassified_on_read(
    seeded_client: AsyncClient,
) -> None:
    """An active delegation whose GCP lapsed since is downgraded when listed."""

    from app import models
    from app.database import get_db
    from app.main import app

    sites = (await seeded_client.get("/api/v1/sites")).json()
    site_id = sites[0]["id"]
    gen = app.dependency_overrides[get_db]()
    db = await gen.__anext__()
    db.add(
        models.InvestigatorDelegation(
            site_id=site_id,
            person_id="drifted_rn_1",
            person_name="Drifted Nurse",
            role="research_nurse",
            delegated_tasks=["vital_signs"],
            delegated_by="dr_sarah_chen",
            gcp_training_date=dt.date(2020, 1, 1),
            # Written as ACTIVE with an expiry already in the past: the state a
            # row reaches by sitting in the table while its certificate lapses.
            gcp_training_expiry=dt.date(2021, 1, 1),
            start_date=dt.date(2020, 2, 1),
            status=models.DelegationStatus.active.value,
        )
    )
    await db.commit()
    listing = (await seeded_client.get(f"/api/v1/delegations?site_id={site_id}")).json()
    drifted = next(d for d in listing if d["person_id"] == "drifted_rn_1")
    assert drifted["status"] == "expired"


async def test_unblinding_an_arm_with_no_allocation_is_refused(
    seeded_client: AsyncClient,
) -> None:
    """An arm no allocation list assigned cannot be reconciled, so it is not revealed."""

    from app import models
    from app.database import get_db
    from app.main import app

    studies = (await seeded_client.get("/api/v1/studies")).json()
    study = studies[0]
    site = (await seeded_client.get(f"/api/v1/sites?study_id={study['id']}")).json()[0]
    subject = (
        await seeded_client.post(
            "/api/v1/subjects",
            json={
                "study_id": study["id"],
                "site_id": site["id"],
                "screening_id": "ORPHAN-ARM-001",
            },
        )
    ).json()
    gen = app.dependency_overrides[get_db]()
    db = await gen.__anext__()
    row = await db.get(models.Subject, subject["id"])
    row.randomisation_arm = "arm_a"  # written directly, as legacy data was
    await db.commit()
    resp = await seeded_client.post(
        f"/api/v1/subjects/{subject['id']}/unblind",
        json={
            "requested_by": "crc_unit",
            "authorised_by": "dr_unit",
            "reason": "probe: arm with no allocation",
        },
    )
    assert resp.status_code == 409
    assert "not traceable" in resp.json()["detail"]


async def test_a_pack_may_forbid_inconvenience_payments(
    seeded_client: AsyncClient,
) -> None:
    """The refusal is policy-driven, so it is provable by changing the policy."""

    pack = pack_loader.get_pack("UK")
    original = pack["participant_reimbursement"]["inconvenience_payment_permitted"]
    pack["participant_reimbursement"]["inconvenience_payment_permitted"] = False
    try:
        subject = (await seeded_client.get("/api/v1/subjects")).json()[0]
        resp = await seeded_client.post(
            "/api/v1/reimbursements",
            json={
                "subject_id": subject["id"],
                "category": "inconvenience",
                "amount": 20.0,
            },
        )
        assert resp.status_code == 422
        assert "not permitted in UK" in resp.json()["detail"]
    finally:
        pack["participant_reimbursement"]["inconvenience_payment_permitted"] = original
    assert (
        pack_loader.get_pack("UK")["participant_reimbursement"][
            "inconvenience_payment_permitted"
        ]
        is True
    )
