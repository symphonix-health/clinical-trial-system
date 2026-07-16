"""Subject endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.post("", response_model=schemas.SubjectOut)
async def create_subject(data: schemas.SubjectCreate, db: AsyncSession = Depends(get_db)) -> schemas.SubjectOut:
    subject = await crud.create_subject(db, data)
    return schemas.SubjectOut.model_validate(subject)


@router.get("", response_model=list[schemas.SubjectOut])
async def list_subjects(study_id: int | None = None, site_id: int | None = None, db: AsyncSession = Depends(get_db)) -> list[schemas.SubjectOut]:
    subjects = await crud.list_subjects(db, study_id=study_id, site_id=site_id)
    return [schemas.SubjectOut.model_validate(s) for s in subjects]


@router.get("/{subject_id}", response_model=schemas.SubjectOut)
async def get_subject(subject_id: int, db: AsyncSession = Depends(get_db)) -> schemas.SubjectOut:
    subject = await crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return schemas.SubjectOut.model_validate(subject)


@router.patch("/{subject_id}", response_model=schemas.SubjectOut)
async def update_subject(subject_id: int, data: schemas.SubjectUpdate, db: AsyncSession = Depends(get_db)) -> schemas.SubjectOut:
    subject = await crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    updated = await crud.update_subject(db, subject, data)
    return schemas.SubjectOut.model_validate(updated)


@router.post("/{subject_id}/consent", response_model=schemas.InformedConsentOut)
async def record_consent(subject_id: int, data: schemas.InformedConsentCreate, db: AsyncSession = Depends(get_db)) -> schemas.InformedConsentOut:
    subject = await crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    data.subject_id = subject_id
    consent = await crud.record_consent(db, subject, data)
    return schemas.InformedConsentOut.model_validate(consent)


@router.post("/{subject_id}/withdraw", response_model=schemas.SubjectOut)
async def withdraw_subject(subject_id: int, reason: str, db: AsyncSession = Depends(get_db)) -> schemas.SubjectOut:
    subject = await crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    updated = await crud.withdraw_subject(db, subject, reason)
    return schemas.SubjectOut.model_validate(updated)


@router.post("/{subject_id}/randomise", response_model=schemas.SubjectOut)
async def randomise_subject(subject_id: int, data: schemas.RandomiseSubject, db: AsyncSession = Depends(get_db)) -> schemas.SubjectOut:
    subject = await crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    import random

    arm = random.choice(["arm_a", "arm_b"])
    updated = await crud.randomise_subject(db, subject, arm, data.stratification_factors)
    return schemas.SubjectOut.model_validate(updated)
