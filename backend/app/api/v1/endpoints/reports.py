"""Report endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/recruitment/{study_id}", response_model=schemas.RecruitmentReport)
async def recruitment_report(study_id: int, db: AsyncSession = Depends(get_db)) -> schemas.RecruitmentReport:
    return await crud.recruitment_report(db, study_id)


@router.get("/safety/{study_id}", response_model=schemas.SafetyReport)
async def safety_report(study_id: int, db: AsyncSession = Depends(get_db)) -> schemas.SafetyReport:
    return await crud.safety_report(db, study_id)


@router.get("/etmf/{study_id}", response_model=schemas.eTMFReport)
async def etmf_report(study_id: int, db: AsyncSession = Depends(get_db)) -> schemas.eTMFReport:
    return await crud.etmf_report(db, study_id)


@router.get("/ip-accountability/{study_id}/{site_id}", response_model=schemas.AccountabilityReport)
async def ip_accountability_report(study_id: int, site_id: int, db: AsyncSession = Depends(get_db)) -> schemas.AccountabilityReport:
    try:
        return await crud.ip_accountability_report(db, study_id, site_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
