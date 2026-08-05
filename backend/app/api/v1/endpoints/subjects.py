"""Subject endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.post("", response_model=schemas.SubjectOut)
async def create_subject(data: schemas.SubjectCreate, db: AsyncSession = Depends(get_db)) -> schemas.SubjectOut:
    subject = await crud.create_subject(db, data)
    return schemas.SubjectOut.model_validate(subject)


@router.get("", response_model=list[schemas.SubjectOut])
async def list_subjects(
    study_id: int | None = None,
    site_id: int | None = None,
    db: AsyncSession = Depends(get_db)
) -> list[schemas.SubjectOut]:
    subjects = await crud.list_subjects(db, study_id=study_id, site_id=site_id)
    return [schemas.SubjectOut.model_validate(s) for s in subjects]


@router.get("/{subject_id}", response_model=schemas.SubjectOut)
async def get_subject(subject_id: int, db: AsyncSession = Depends(get_db)) -> schemas.SubjectOut:
    subject = await crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return schemas.SubjectOut.model_validate(subject)


@router.patch("/{subject_id}", response_model=schemas.SubjectOut)
async def update_subject(
    subject_id: int,
    data: schemas.SubjectUpdate,
    db: AsyncSession = Depends(get_db)
) -> schemas.SubjectOut:
    subject = await crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    updated = await crud.update_subject(db, subject, data)
    return schemas.SubjectOut.model_validate(updated)


@router.post("/{subject_id}/consent", response_model=schemas.InformedConsentOut)
async def record_consent(
    subject_id: int,
    data: schemas.InformedConsentCreate,
    db: AsyncSession = Depends(get_db)
) -> schemas.InformedConsentOut:
    subject = await crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    data.subject_id = subject_id
    consent = await crud.record_consent(db, subject, data)
    return schemas.InformedConsentOut.model_validate(consent)


@router.post("/{subject_id}/withdraw", response_model=schemas.SubjectOut)
async def withdraw_subject(
    subject_id: int,
    reason: str,
    withdrawal_scope: str = "full",
    db: AsyncSession = Depends(get_db),
) -> schemas.SubjectOut:
    subject = await crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    updated = await crud.withdraw_subject(db, subject, reason, withdrawal_scope)
    return schemas.SubjectOut.model_validate(updated)


@router.post("/{subject_id}/randomise", response_model=schemas.SubjectOut)
async def randomise_subject(
    subject_id: int,
    data: schemas.RandomiseSubject,
    db: AsyncSession = Depends(get_db)
) -> schemas.SubjectOut:
    """Allocate the subject to the next free slot of its stratum.

    REQ-CTS-NAT-005. The handler no longer decides the arm: it consumes a
    pre-generated, stratified, permuted-block allocation list so the
    allocation is reproducible and auditable.
    """

    subject = await crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    updated, _allocation = await crud.randomise_subject(
        db, subject, data.stratification_factors, data.randomised_by
    )
    return schemas.SubjectOut.model_validate(updated)


@router.get("/{subject_id}/allocation", response_model=schemas.RandomisationResult)
async def get_allocation(
    subject_id: int, db: AsyncSession = Depends(get_db)
) -> schemas.RandomisationResult:
    """Blinded allocation read: kit code only, never the treatment arm."""

    subject = await crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    result = await db.execute(
        select(models.RandomisationAllocation).where(
            models.RandomisationAllocation.allocated_subject_id == subject_id
        )
    )
    allocation = result.scalars().first()
    if allocation is None:
        raise HTTPException(status_code=404, detail="Subject is not randomised")
    return schemas.RandomisationResult(
        subject_id=subject_id,
        stratum_key=allocation.stratum_key,
        kit_code=allocation.kit_code,
        sequence_number=allocation.sequence_number,
    )


@router.post("/{subject_id}/unblind", response_model=schemas.UnblindingEventOut)
async def unblind_subject(
    subject_id: int, data: schemas.UnblindingRequest, db: AsyncSession = Depends(get_db)
) -> schemas.UnblindingEventOut:
    """Emergency unblinding: reveals the arm, recorded against a named authoriser."""

    subject = await crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    event = await crud.unblind_subject(db, subject, data)
    return schemas.UnblindingEventOut.model_validate(event)
