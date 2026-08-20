"""National-capability domain operations (REQ-CTS-NAT-001..008).

Everything in this module obeys three rules taken from the national
capability benchmark:

* **Country policy is data.** Registry formats, approval authorities,
  statutory deadlines, consent rules and reimbursement caps come from
  ``app.country_packs``; there is no ``if jurisdiction == ...`` branch here.
* **Human authority is preserved.** Ethics/regulatory decisions, unblinding
  and eligibility overrides all carry a named decider. Nothing auto-approves.
* **Dispatch is not completion.** Registry submissions and safety reports are
  queued through the BulletTrain hub and only reach a terminal state when an
  acknowledgement carrying a receipt reference comes back.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, cast

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.connectors import integration_engine
from app.country_packs import CountryPackError, get_pack, validate_registry_identifier

_TERMINAL_DECISIONS = {
    models.ApprovalDecision.approved.value,
    models.ApprovalDecision.approved_with_conditions.value,
    models.ApprovalDecision.rejected.value,
    models.ApprovalDecision.withdrawn.value,
}


async def _require_study(db: AsyncSession, study_id: int) -> models.Study:
    study = await crud.get_study(db, study_id)
    if study is None:
        raise HTTPException(status_code=404, detail="Study not found")
    return study


def _pack_or_422(jurisdiction: str) -> dict[str, Any]:
    try:
        return get_pack(jurisdiction)
    except CountryPackError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# --- REQ-CTS-NAT-001: trial registry + investigator credentialing -----------


async def submit_trial_registration(
    db: AsyncSession, obj_in: schemas.TrialRegistrationCreate
) -> models.TrialRegistration:
    """Submit a study to its jurisdiction's public trial registry."""

    study = await _require_study(db, obj_in.study_id)
    pack = _pack_or_422(study.jurisdiction)
    registry_code = obj_in.registry_code or pack["trial_registry"]["code"]
    existing = await db.execute(
        select(models.TrialRegistration)
        .where(models.TrialRegistration.study_id == study.id)
        .where(models.TrialRegistration.registry_code == registry_code)
    )
    registration = existing.scalar_one_or_none()
    if registration is None:
        registration = models.TrialRegistration(
            study_id=study.id,
            jurisdiction=study.jurisdiction,
            registry_code=registry_code,
            public_disclosure_url=obj_in.public_disclosure_url,
        )
        db.add(registration)
        await db.commit()
        await db.refresh(registration)
    registration.status = models.RegistrationStatus.submitted.value
    registration.submitted_at = dt.datetime.utcnow()
    registration.correlation_id = f"ctms-trial-registration-{registration.id}"
    await db.commit()
    await db.refresh(registration)
    try:
        await integration_engine.notify_trial_registration_submitted(
            db,
            registration_id=registration.id,
            study_id=study.id,
            jurisdiction=study.jurisdiction,
            registry_code=registry_code,
            correlation_id=registration.correlation_id,
        )
    except integration_engine.IntegrationError:  # pragma: no cover - policy guard
        pass
    await crud.create_audit_entry(
        db,
        schemas.AuditEntryCreate(
            study_id=study.id,
            actor_id="system",
            purpose_of_use="trial_registration",
            action=f"submit_registration:{registry_code}",
            resource_type="TrialRegistration",
            resource_id=registration.id,
        ),
    )
    return registration


async def record_registration_receipt(
    db: AsyncSession, registration: models.TrialRegistration, receipt: schemas.TrialRegistrationReceipt
) -> models.TrialRegistration:
    """Close the registry loop with the registry's own acknowledgement.

    The registry identifier is validated against the jurisdiction pack's
    format, so an acknowledgement carrying an identifier from the wrong
    registry is refused rather than silently stored.
    """

    if registration.status not in {
        models.RegistrationStatus.submitted.value,
        models.RegistrationStatus.registered.value,
    }:
        raise HTTPException(
            status_code=409,
            detail=f"registration is {registration.status!r}, not submitted",
        )
    if not receipt.accepted:
        registration.status = models.RegistrationStatus.rejected.value
        registration.rejection_reason = receipt.rejection_reason or "rejected by registry"
        registration.acknowledged_at = dt.datetime.utcnow()
        await db.commit()
        await db.refresh(registration)
        return registration
    if not validate_registry_identifier(receipt.registry_identifier, registration.jurisdiction):
        pack = get_pack(registration.jurisdiction)["trial_registry"]
        raise HTTPException(
            status_code=422,
            detail=(
                f"{receipt.registry_identifier!r} is not a valid "
                f"{pack['identifier_label']} (expected e.g. {pack['identifier_example']})"
            ),
        )
    registration.registry_identifier = receipt.registry_identifier
    registration.receipt_reference = receipt.receipt_reference
    registration.acknowledged_at = dt.datetime.utcnow()
    registration.status = models.RegistrationStatus.registered.value
    await db.commit()
    await db.refresh(registration)
    return registration


async def list_trial_registrations(db: AsyncSession, study_id: int) -> list[models.TrialRegistration]:
    result = await db.execute(select(models.TrialRegistration).where(models.TrialRegistration.study_id == study_id))
    return list(result.scalars().all())


async def create_investigator_delegation(
    db: AsyncSession, obj_in: schemas.InvestigatorDelegationCreate
) -> models.InvestigatorDelegation:
    """Add a delegation-log entry, deriving GCP expiry from the country pack."""

    site = await crud.get_site(db, obj_in.site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    study = await _require_study(db, site.study_id)
    pack = _pack_or_422(study.jurisdiction)
    validity = int(pack["site_credentialing"]["gcp_training_validity_days"])
    expiry = obj_in.gcp_training_date + dt.timedelta(days=validity)
    delegation = models.InvestigatorDelegation(
        **obj_in.model_dump(),
        gcp_training_expiry=expiry,
        status=(
            models.DelegationStatus.active.value if expiry >= dt.date.today() else models.DelegationStatus.expired.value
        ),
    )
    db.add(delegation)
    await db.commit()
    await db.refresh(delegation)
    await crud.create_audit_entry(
        db,
        schemas.AuditEntryCreate(
            study_id=study.id,
            actor_id=obj_in.delegated_by,
            purpose_of_use="site_credentialing",
            action=f"delegate:{obj_in.role}",
            resource_type="InvestigatorDelegation",
            resource_id=delegation.id,
        ),
    )
    return delegation


async def list_investigator_delegations(db: AsyncSession, site_id: int) -> list[models.InvestigatorDelegation]:
    result = await db.execute(
        select(models.InvestigatorDelegation).where(models.InvestigatorDelegation.site_id == site_id)
    )
    delegations = list(result.scalars().all())
    today = dt.date.today()
    changed = False
    for delegation in delegations:
        if delegation.status == models.DelegationStatus.active.value and delegation.gcp_training_expiry < today:
            delegation.status = models.DelegationStatus.expired.value
            changed = True
    if changed:
        await db.commit()
    return delegations


async def site_readiness(db: AsyncSession, site_id: int) -> schemas.SiteReadinessOut:
    """Whether a site may be activated, and every reason it may not.

    FR-C-22 / FR-C-53 / REQ-CTS-NAT-001. The blocking reasons are returned
    explicitly rather than collapsed to a boolean so an operator can see what
    to fix.
    """

    site = await crud.get_site(db, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    study = await _require_study(db, site.study_id)
    pack = _pack_or_422(study.jurisdiction)
    checklist = await crud.get_site_checklist(db, site_id)
    checklist_complete = bool(checklist) and all(t.status == "complete" for t in checklist)
    delegations = await list_investigator_delegations(db, site_id)
    active = [d for d in delegations if d.status == models.DelegationStatus.active.value]
    expired = [d for d in delegations if d.status == models.DelegationStatus.expired.value]
    approvals = await db.execute(
        select(models.RegulatoryApproval)
        .where(models.RegulatoryApproval.study_id == study.id)
        .where(models.RegulatoryApproval.authority_kind == "ethics")
    )
    today = dt.date.today()
    ethics_approved = any(
        a.decision
        in {
            models.ApprovalDecision.approved.value,
            models.ApprovalDecision.approved_with_conditions.value,
        }
        and (a.approval_expiry is None or a.approval_expiry >= today)
        for a in approvals.scalars().all()
    )
    reasons: list[str] = []
    if not checklist_complete:
        reasons.append("site activation checklist incomplete")
    if pack["site_credentialing"]["investigator_delegation_log_required"] and not active:
        reasons.append("no active investigator delegation on the delegation log")
    if expired:
        reasons.append(f"{len(expired)} delegation(s) with expired GCP training")
    if not ethics_approved:
        reasons.append("no current ethics approval for the study")
    return schemas.SiteReadinessOut(
        site_id=site_id,
        jurisdiction=study.jurisdiction,
        checklist_complete=checklist_complete,
        delegation_log_present=bool(delegations),
        delegations_active=len(active),
        delegations_expired=len(expired),
        ethics_approved=ethics_approved,
        blocking_reasons=reasons,
        ready_for_activation=not reasons,
    )


# --- REQ-CTS-NAT-002: ethics / regulatory approval pack --------------------


async def create_regulatory_approval(
    db: AsyncSession, obj_in: schemas.RegulatoryApprovalCreate
) -> models.RegulatoryApproval:
    """Record a submission to the jurisdiction's ethics or competent authority."""

    study = await _require_study(db, obj_in.study_id)
    pack = _pack_or_422(study.jurisdiction)
    if obj_in.authority_kind not in {"ethics", "competent_authority"}:
        raise HTTPException(
            status_code=422,
            detail="authority_kind must be 'ethics' or 'competent_authority'",
        )
    if obj_in.submission_type not in {t.value for t in models.SubmissionType}:
        raise HTTPException(
            status_code=422,
            detail=f"unknown submission_type {obj_in.submission_type!r}",
        )
    authority = pack["ethics_authority"] if obj_in.authority_kind == "ethics" else pack["competent_authority"]
    approval = models.RegulatoryApproval(
        **obj_in.model_dump(),
        jurisdiction=study.jurisdiction,
        authority_code=authority["code"],
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    await crud.create_audit_entry(
        db,
        schemas.AuditEntryCreate(
            study_id=study.id,
            actor_id="system",
            purpose_of_use="regulatory_submission",
            action=f"submit:{obj_in.authority_kind}:{obj_in.submission_type}",
            resource_type="RegulatoryApproval",
            resource_id=approval.id,
        ),
    )
    return approval


async def record_approval_decision(
    db: AsyncSession, approval: models.RegulatoryApproval, decision: schemas.RegulatoryDecision
) -> models.RegulatoryApproval:
    """Record a NAMED human's ethics/regulatory decision.

    Nothing auto-approves: ``decided_by`` is required, the decision must be a
    known outcome, and a decision may not be overwritten once terminal.
    """

    if approval.decision in _TERMINAL_DECISIONS:
        raise HTTPException(
            status_code=409,
            detail=f"decision already recorded as {approval.decision!r}",
        )
    if decision.decision not in _TERMINAL_DECISIONS:
        raise HTTPException(status_code=422, detail=f"unknown decision {decision.decision!r}")
    if not decision.decided_by.strip():
        raise HTTPException(status_code=422, detail="decided_by is required")
    if decision.decision == models.ApprovalDecision.approved_with_conditions.value and not decision.conditions:
        raise HTTPException(
            status_code=422,
            detail="approved_with_conditions requires at least one condition",
        )
    pack = _pack_or_422(approval.jurisdiction)
    approval.decision = decision.decision
    approval.decided_by = decision.decided_by
    approval.decision_at = dt.datetime.utcnow()
    approval.conditions = decision.conditions
    approval.approval_expiry = decision.approval_expiry
    if decision.decision in {
        models.ApprovalDecision.approved.value,
        models.ApprovalDecision.approved_with_conditions.value,
    }:
        interval = int(pack["safety_reporting"]["annual_safety_report_interval_days"])
        approval.next_report_due = approval.decision_at.date() + dt.timedelta(days=interval)
    await db.commit()
    await db.refresh(approval)
    await crud.create_audit_entry(
        db,
        schemas.AuditEntryCreate(
            study_id=approval.study_id,
            actor_id=decision.decided_by,
            purpose_of_use="regulatory_decision",
            action=f"decide:{decision.decision}",
            resource_type="RegulatoryApproval",
            resource_id=approval.id,
        ),
    )
    return approval


async def list_regulatory_approvals(db: AsyncSession, study_id: int) -> list[models.RegulatoryApproval]:
    result = await db.execute(select(models.RegulatoryApproval).where(models.RegulatoryApproval.study_id == study_id))
    return list(result.scalars().all())


async def approvals_due(db: AsyncSession, study_id: int, within_days: int = 60) -> dict[str, Any]:
    """Approvals expiring, and statutory reports falling due, within a window."""

    horizon = dt.date.today() + dt.timedelta(days=within_days)
    approvals = await list_regulatory_approvals(db, study_id)
    expiring = [a for a in approvals if a.approval_expiry is not None and a.approval_expiry <= horizon]
    reports = [a for a in approvals if a.next_report_due is not None and a.next_report_due <= horizon]
    return {
        "study_id": study_id,
        "within_days": within_days,
        "expiring_approvals": [
            {
                "id": a.id,
                "authority_code": a.authority_code,
                "submission_type": a.submission_type,
                "approval_expiry": cast(dt.date, a.approval_expiry).isoformat(),
            }
            for a in expiring
        ],
        "reports_due": [
            {
                "id": a.id,
                "authority_code": a.authority_code,
                "next_report_due": cast(dt.date, a.next_report_due).isoformat(),
            }
            for a in reports
        ],
    }


# --- REQ-CTS-NAT-003: hub-mediated eligibility pre-screening ---------------


async def request_eligibility_screening(
    db: AsyncSession, obj_in: schemas.EligibilityScreeningCreate
) -> models.EligibilityScreening:
    """Queue a criteria-only pre-screen request through the hub."""

    await _require_study(db, obj_in.study_id)
    if not obj_in.criteria_requested:
        raise HTTPException(status_code=422, detail="criteria_requested must not be empty")
    screening = models.EligibilityScreening(**obj_in.model_dump())
    db.add(screening)
    await db.commit()
    await db.refresh(screening)
    screening.correlation_id = f"ctms-eligibility-{screening.id}"
    await db.commit()
    try:
        await integration_engine.request_eligibility_prescreen(
            db,
            screening_id=screening.id,
            study_id=screening.study_id,
            candidate_reference=screening.candidate_reference,
            criteria_requested=list(screening.criteria_requested),
            consent_basis=screening.consent_basis,
            correlation_id=screening.correlation_id,
        )
    except integration_engine.IntegrationError:  # pragma: no cover - policy guard
        pass
    await db.refresh(screening)
    return screening


async def record_eligibility_outcome(
    db: AsyncSession, screening: models.EligibilityScreening, payload: schemas.EligibilityOutcomeIn
) -> models.EligibilityScreening:
    """Apply the criterion-level verdicts returned through the hub.

    The OUTCOME is derived from the criteria, not accepted from the caller:
    any failed criterion is ineligible, any unevaluable criterion needs human
    review, and only an all-pass result is eligible.
    """

    evaluated = payload.criteria_evaluated
    missing = [c for c in screening.criteria_requested if c not in evaluated]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"criteria not evaluated: {sorted(missing)}",
        )
    values = [evaluated[c] for c in screening.criteria_requested]
    if any(v is False for v in values):
        outcome = models.EligibilityOutcome.ineligible.value
    elif all(v is True for v in values):
        outcome = models.EligibilityOutcome.eligible.value
    else:
        outcome = models.EligibilityOutcome.pending_review.value
    screening.criteria_evaluated = evaluated
    screening.outcome = outcome
    screening.outcome_at = dt.datetime.utcnow()
    screening.reviewed_by = payload.reviewed_by
    screening.source_system = payload.source_system
    await db.commit()
    await db.refresh(screening)
    await crud.create_audit_entry(
        db,
        schemas.AuditEntryCreate(
            study_id=screening.study_id,
            actor_id=payload.reviewed_by or payload.source_system,
            purpose_of_use="eligibility_prescreen",
            action=f"eligibility:{outcome}",
            resource_type="EligibilityScreening",
            resource_id=screening.id,
        ),
    )
    return screening


async def list_eligibility_screenings(db: AsyncSession, study_id: int) -> list[models.EligibilityScreening]:
    result = await db.execute(
        select(models.EligibilityScreening).where(models.EligibilityScreening.study_id == study_id)
    )
    return list(result.scalars().all())


# --- REQ-CTS-NAT-006: expedited safety reporting closed loop ---------------


async def submit_safety_report(
    db: AsyncSession, ae: models.AdverseEvent, payload: schemas.SafetySubmissionCreate
) -> models.SafetySubmission:
    """Submit an expedited safety report and start waiting for the receipt."""

    if ae.regulatory_report_deadline is None:
        raise HTTPException(
            status_code=422,
            detail="adverse event carries no statutory reporting deadline",
        )
    pack = _pack_or_422(ae.jurisdiction)
    recipients = list(pack["safety_reporting"]["recipients"])
    recipient = payload.recipient_code or recipients[0]
    if recipient not in recipients:
        raise HTTPException(
            status_code=422,
            detail=f"{recipient!r} is not a safety recipient for {ae.jurisdiction}",
        )
    submission = models.SafetySubmission(
        adverse_event_id=ae.id,
        jurisdiction=ae.jurisdiction,
        recipient_code=recipient,
        report_type="susar" if ae.susar_flag else "serious_adverse_event",
        due_at=ae.regulatory_report_deadline,
        submitted_at=dt.datetime.utcnow(),
        submitted_by=payload.submitted_by,
        submission_reference=payload.submission_reference,
        status=models.SafetySubmissionStatus.submitted.value,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    submission.correlation_id = f"ctms-safety-submission-{submission.id}"
    ae.status = models.AEStatus.submitted.value
    ae.submission_reference = payload.submission_reference
    await db.commit()
    await db.refresh(submission)
    try:
        await integration_engine.notify_safety_report_submitted(
            db,
            submission_id=submission.id,
            adverse_event_id=ae.id,
            jurisdiction=ae.jurisdiction,
            recipient_code=recipient,
            report_type=submission.report_type,
            due_at=submission.due_at.isoformat() if submission.due_at else None,
            correlation_id=submission.correlation_id,
        )
    except integration_engine.IntegrationError:  # pragma: no cover - policy guard
        pass
    await crud.create_audit_entry(
        db,
        schemas.AuditEntryCreate(
            study_id=ae.study_id,
            actor_id=payload.submitted_by,
            purpose_of_use="safety_reporting",
            action=f"submit_safety_report:{recipient}",
            resource_type="SafetySubmission",
            resource_id=submission.id,
        ),
    )
    return submission


async def record_safety_acknowledgement(
    db: AsyncSession,
    submission: models.SafetySubmission,
    payload: schemas.SafetyAcknowledgement,
) -> models.SafetySubmission:
    """Close the safety loop with the authority's acknowledgement.

    REQ-CTS-NAT-006. Until this runs, the report is ``submitted`` -- dispatched
    but unreceipted -- which is exactly the state the benchmark forbids
    treating as completion.
    """

    if submission.status not in {
        models.SafetySubmissionStatus.submitted.value,
        models.SafetySubmissionStatus.rejected.value,
    }:
        raise HTTPException(
            status_code=409,
            detail=f"submission is {submission.status!r}, not submitted",
        )
    submission.acknowledged_at = dt.datetime.utcnow()
    submission.acknowledgement_reference = payload.acknowledgement_reference
    if payload.accepted:
        submission.status = models.SafetySubmissionStatus.acknowledged.value
        submission.rejection_reason = None
    else:
        submission.status = models.SafetySubmissionStatus.rejected.value
        submission.rejection_reason = payload.rejection_reason or "rejected by authority"
    await db.commit()
    await db.refresh(submission)
    return submission


async def overdue_safety_submissions(
    db: AsyncSession, study_id: int, as_of: dt.datetime | None = None
) -> list[dict[str, Any]]:
    """Reports past their statutory clock without an acknowledgement."""

    now = as_of or dt.datetime.utcnow()
    result = await db.execute(
        select(models.SafetySubmission, models.AdverseEvent)
        .join(models.AdverseEvent, models.SafetySubmission.adverse_event_id == models.AdverseEvent.id)
        .where(models.AdverseEvent.study_id == study_id)
    )
    overdue: list[dict[str, Any]] = []
    for submission, ae in result.all():
        if submission.status == models.SafetySubmissionStatus.acknowledged.value:
            continue
        if submission.due_at is not None and submission.due_at < now:
            overdue.append(
                {
                    "submission_id": submission.id,
                    "adverse_event_id": ae.id,
                    "recipient_code": submission.recipient_code,
                    "due_at": submission.due_at.isoformat(),
                    "status": submission.status,
                    "deadline_basis": ae.deadline_basis,
                }
            )
    return overdue


async def list_safety_submissions(db: AsyncSession, adverse_event_id: int) -> list[models.SafetySubmission]:
    result = await db.execute(
        select(models.SafetySubmission).where(models.SafetySubmission.adverse_event_id == adverse_event_id)
    )
    return list(result.scalars().all())


# --- REQ-CTS-NAT-008: participant surface + reimbursement ------------------


async def create_reimbursement(
    db: AsyncSession, obj_in: schemas.ParticipantReimbursementCreate
) -> models.ParticipantReimbursement:
    """Record a participant expense / inconvenience payment request."""

    subject = await crud.get_subject(db, obj_in.subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    study = await _require_study(db, subject.study_id)
    policy = _pack_or_422(study.jurisdiction)["participant_reimbursement"]
    if obj_in.amount <= 0:
        raise HTTPException(status_code=422, detail="amount must be positive")
    if obj_in.category == "inconvenience" and not policy["inconvenience_payment_permitted"]:
        raise HTTPException(
            status_code=422,
            detail=f"inconvenience payments are not permitted in {study.jurisdiction}",
        )
    reimbursement = models.ParticipantReimbursement(
        **obj_in.model_dump(),
        currency=policy["currency"],
        exceeds_guidance_cap=obj_in.amount > float(policy["per_visit_guidance_cap"]),
    )
    db.add(reimbursement)
    await db.commit()
    await db.refresh(reimbursement)
    try:
        await integration_engine.notify_participant_reimbursement(
            db,
            reimbursement_id=reimbursement.id,
            subject_id=reimbursement.subject_id,
            amount=reimbursement.amount,
            currency=reimbursement.currency,
            status=reimbursement.status,
        )
    except integration_engine.IntegrationError:  # pragma: no cover - policy guard
        pass
    return reimbursement


async def approve_reimbursement(
    db: AsyncSession, reimbursement: models.ParticipantReimbursement, approved_by: str
) -> models.ParticipantReimbursement:
    """Approve a payment. A payment over the pack's cap needs a named approver."""

    if reimbursement.status != models.ReimbursementStatus.requested.value:
        raise HTTPException(status_code=409, detail=f"reimbursement is {reimbursement.status!r}")
    if not approved_by.strip():
        raise HTTPException(status_code=422, detail="approved_by is required")
    reimbursement.status = models.ReimbursementStatus.approved.value
    reimbursement.approved_by = approved_by
    await db.commit()
    await db.refresh(reimbursement)
    return reimbursement


async def participant_summary(db: AsyncSession, subject_id: int) -> schemas.ParticipantSummaryOut:
    """The participant-facing projection that citizen-portal renders.

    REQ-CTS-NAT-008 (MIGRATE-SURFACE). CTMS stays the canonical owner of
    visits, consent and payments; citizen-portal renders this contract rather
    than keeping its own copy of research state.
    """

    subject = await crud.get_subject(db, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    study = await _require_study(db, subject.study_id)
    pack = _pack_or_422(study.jurisdiction)
    payments = await db.execute(
        select(models.ParticipantReimbursement).where(models.ParticipantReimbursement.subject_id == subject_id)
    )
    withdrawn = subject.consent_state == models.ConsentState.withdrawn.value
    upcoming = [
        {
            "visit_id": v.id,
            "visit_definition_id": v.visit_definition_id,
            "scheduled_date": v.scheduled_date.isoformat(),
            "status": v.status,
        }
        for v in subject.visits
        if v.status == models.VisitStatus.scheduled.value
    ]
    return schemas.ParticipantSummaryOut(
        subject_id=subject.id,
        subject_number=subject.subject_number,
        study_title=study.title,
        jurisdiction=study.jurisdiction,
        consent_state=subject.consent_state,
        consent_version=subject.consent_version,
        re_consent_required=(subject.consent_state == models.ConsentState.re_consent_required.value),
        withdrawal_effective_immediately=bool(pack["consent"]["withdrawal_effective_immediately"]),
        # A withdrawn participant sees no upcoming visits: the withdrawal has
        # to reach this surface too, not just the visit table.
        upcoming_visits=[] if withdrawn else upcoming,
        reimbursements=[
            {
                "id": p.id,
                "category": p.category,
                "amount": p.amount,
                "currency": p.currency,
                "status": p.status,
            }
            for p in payments.scalars().all()
        ],
        reimbursement_currency=pack["participant_reimbursement"]["currency"],
        results_available=study.status in {models.StudyStatus.completed.value, models.StudyStatus.closed.value},
    )
