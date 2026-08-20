"""National-capability endpoints (REQ-CTS-NAT-001..008)."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, national, schemas
from app.country_packs import CountryPackError, get_pack, list_packs
from app.auth import require_auth
from app.database import get_db

router = APIRouter(tags=["national"])


# --- Country packs ---------------------------------------------------------


@router.get("/country-packs", response_model=list[schemas.CountryPackOut])
async def get_country_packs() -> list[schemas.CountryPackOut]:
    return [schemas.CountryPackOut.model_validate(p) for p in list_packs()]


@router.get("/country-packs/{code}", response_model=schemas.CountryPackOut)
async def get_country_pack(code: str) -> schemas.CountryPackOut:
    try:
        return schemas.CountryPackOut.model_validate(get_pack(code))
    except CountryPackError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# --- REQ-CTS-NAT-001: trial registry --------------------------------------


@router.post("/trial-registrations", response_model=schemas.TrialRegistrationOut)
async def submit_trial_registration(
    data: schemas.TrialRegistrationCreate, db: AsyncSession = Depends(get_db)
) -> schemas.TrialRegistrationOut:
    registration = await national.submit_trial_registration(db, data)
    return schemas.TrialRegistrationOut.model_validate(registration)


@router.get("/trial-registrations", response_model=list[schemas.TrialRegistrationOut])
async def list_trial_registrations(
    study_id: int, db: AsyncSession = Depends(get_db)
) -> list[schemas.TrialRegistrationOut]:
    rows = await national.list_trial_registrations(db, study_id)
    return [schemas.TrialRegistrationOut.model_validate(r) for r in rows]


@router.post(
    "/trial-registrations/{registration_id}/receipt",
    response_model=schemas.TrialRegistrationOut,
)
async def record_registration_receipt(
    registration_id: int,
    data: schemas.TrialRegistrationReceipt,
    db: AsyncSession = Depends(get_db),
) -> schemas.TrialRegistrationOut:
    registration = await db.get(models.TrialRegistration, registration_id)
    if not registration:
        raise HTTPException(status_code=404, detail="Trial registration not found")
    updated = await national.record_registration_receipt(db, registration, data)
    return schemas.TrialRegistrationOut.model_validate(updated)


# --- REQ-CTS-NAT-001: investigator delegation + site readiness -------------


@router.post("/delegations", response_model=schemas.InvestigatorDelegationOut)
async def create_delegation(
    data: schemas.InvestigatorDelegationCreate, db: AsyncSession = Depends(get_db)
) -> schemas.InvestigatorDelegationOut:
    delegation = await national.create_investigator_delegation(db, data)
    return schemas.InvestigatorDelegationOut.model_validate(delegation)


@router.get("/delegations", response_model=list[schemas.InvestigatorDelegationOut])
async def list_delegations(site_id: int, db: AsyncSession = Depends(get_db)) -> list[schemas.InvestigatorDelegationOut]:
    rows = await national.list_investigator_delegations(db, site_id)
    return [schemas.InvestigatorDelegationOut.model_validate(r) for r in rows]


@router.get("/sites/{site_id}/readiness", response_model=schemas.SiteReadinessOut)
async def site_readiness(site_id: int, db: AsyncSession = Depends(get_db)) -> schemas.SiteReadinessOut:
    return await national.site_readiness(db, site_id)


# --- REQ-CTS-NAT-002: ethics / regulatory approvals -----------------------


@router.post("/regulatory-approvals", response_model=schemas.RegulatoryApprovalOut)
async def create_regulatory_approval(
    data: schemas.RegulatoryApprovalCreate, db: AsyncSession = Depends(get_db)
) -> schemas.RegulatoryApprovalOut:
    approval = await national.create_regulatory_approval(db, data)
    return schemas.RegulatoryApprovalOut.model_validate(approval)


@router.get("/regulatory-approvals", response_model=list[schemas.RegulatoryApprovalOut])
async def list_regulatory_approvals(
    study_id: int, db: AsyncSession = Depends(get_db)
) -> list[schemas.RegulatoryApprovalOut]:
    rows = await national.list_regulatory_approvals(db, study_id)
    return [schemas.RegulatoryApprovalOut.model_validate(r) for r in rows]


@router.post(
    "/regulatory-approvals/{approval_id}/decision",
    response_model=schemas.RegulatoryApprovalOut,
)
async def record_approval_decision(
    approval_id: int,
    data: schemas.RegulatoryDecision,
    db: AsyncSession = Depends(get_db),
) -> schemas.RegulatoryApprovalOut:
    approval = await db.get(models.RegulatoryApproval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Regulatory approval not found")
    updated = await national.record_approval_decision(db, approval, data)
    return schemas.RegulatoryApprovalOut.model_validate(updated)


@router.get("/regulatory-approvals/due/{study_id}")
async def approvals_due(study_id: int, within_days: int = 60, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    return await national.approvals_due(db, study_id, within_days)


# --- REQ-CTS-NAT-003: eligibility pre-screening ---------------------------


@router.post("/eligibility-screenings", response_model=schemas.EligibilityScreeningOut)
async def request_eligibility_screening(
    data: schemas.EligibilityScreeningCreate,
    _auth: dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> schemas.EligibilityScreeningOut:
    screening = await national.request_eligibility_screening(db, data)
    return schemas.EligibilityScreeningOut.model_validate(screening)


@router.get("/eligibility-screenings", response_model=list[schemas.EligibilityScreeningOut])
async def list_eligibility_screenings(
    study_id: int,
    _auth: dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> list[schemas.EligibilityScreeningOut]:
    rows = await national.list_eligibility_screenings(db, study_id)
    return [schemas.EligibilityScreeningOut.model_validate(r) for r in rows]


@router.post(
    "/eligibility-screenings/{screening_id}/outcome",
    response_model=schemas.EligibilityScreeningOut,
)
async def record_eligibility_outcome(
    screening_id: int,
    data: schemas.EligibilityOutcomeIn,
    _auth: dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> schemas.EligibilityScreeningOut:
    screening = await db.get(models.EligibilityScreening, screening_id)
    if not screening:
        raise HTTPException(status_code=404, detail="Eligibility screening not found")
    updated = await national.record_eligibility_outcome(db, screening, data)
    return schemas.EligibilityScreeningOut.model_validate(updated)


# --- REQ-CTS-NAT-006: expedited safety reporting --------------------------


@router.post(
    "/adverse-events/{ae_id}/safety-submissions",
    response_model=schemas.SafetySubmissionOut,
)
async def submit_safety_report(
    ae_id: int, data: schemas.SafetySubmissionCreate, db: AsyncSession = Depends(get_db)
) -> schemas.SafetySubmissionOut:
    ae = await crud.get_adverse_event(db, ae_id)
    if not ae:
        raise HTTPException(status_code=404, detail="Adverse event not found")
    submission = await national.submit_safety_report(db, ae, data)
    return schemas.SafetySubmissionOut.model_validate(submission)


@router.get(
    "/adverse-events/{ae_id}/safety-submissions",
    response_model=list[schemas.SafetySubmissionOut],
)
async def list_safety_submissions(ae_id: int, db: AsyncSession = Depends(get_db)) -> list[schemas.SafetySubmissionOut]:
    rows = await national.list_safety_submissions(db, ae_id)
    return [schemas.SafetySubmissionOut.model_validate(r) for r in rows]


@router.post(
    "/safety-submissions/{submission_id}/acknowledgement",
    response_model=schemas.SafetySubmissionOut,
)
async def record_safety_acknowledgement(
    submission_id: int,
    data: schemas.SafetyAcknowledgement,
    db: AsyncSession = Depends(get_db),
) -> schemas.SafetySubmissionOut:
    submission = await db.get(models.SafetySubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Safety submission not found")
    updated = await national.record_safety_acknowledgement(db, submission, data)
    return schemas.SafetySubmissionOut.model_validate(updated)


@router.get("/reports/safety-overdue/{study_id}")
async def overdue_safety_submissions(study_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    rows = await national.overdue_safety_submissions(db, study_id)
    return {"study_id": study_id, "overdue": rows, "count": len(rows)}


# --- REQ-CTS-NAT-008: participant surface ---------------------------------


@router.get("/participants/{subject_id}/summary", response_model=schemas.ParticipantSummaryOut)
async def participant_summary(subject_id: int, db: AsyncSession = Depends(get_db)) -> schemas.ParticipantSummaryOut:
    return await national.participant_summary(db, subject_id)


@router.post("/reimbursements", response_model=schemas.ParticipantReimbursementOut)
async def create_reimbursement(
    data: schemas.ParticipantReimbursementCreate, db: AsyncSession = Depends(get_db)
) -> schemas.ParticipantReimbursementOut:
    reimbursement = await national.create_reimbursement(db, data)
    return schemas.ParticipantReimbursementOut.model_validate(reimbursement)


@router.post(
    "/reimbursements/{reimbursement_id}/approve",
    response_model=schemas.ParticipantReimbursementOut,
)
async def approve_reimbursement(
    reimbursement_id: int, approved_by: str, db: AsyncSession = Depends(get_db)
) -> schemas.ParticipantReimbursementOut:
    reimbursement = await db.get(models.ParticipantReimbursement, reimbursement_id)
    if not reimbursement:
        raise HTTPException(status_code=404, detail="Reimbursement not found")
    updated = await national.approve_reimbursement(db, reimbursement, approved_by)
    return schemas.ParticipantReimbursementOut.model_validate(updated)
