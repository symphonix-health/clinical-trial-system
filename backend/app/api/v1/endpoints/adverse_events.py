"""Adverse event endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/adverse-events", tags=["adverse-events"])


@router.post("", response_model=schemas.AdverseEventOut)
async def create_adverse_event(data: schemas.AdverseEventCreate, db: AsyncSession = Depends(get_db)) -> schemas.AdverseEventOut:
    ae = await crud.create_adverse_event(db, data)
    return schemas.AdverseEventOut.model_validate(ae)


@router.get("", response_model=list[schemas.AdverseEventOut])
async def list_adverse_events(study_id: int | None = None, db: AsyncSession = Depends(get_db)) -> list[schemas.AdverseEventOut]:
    aes = await crud.list_adverse_events(db, study_id=study_id)
    return [schemas.AdverseEventOut.model_validate(ae) for ae in aes]


@router.get("/{ae_id}", response_model=schemas.AdverseEventOut)
async def get_adverse_event(ae_id: int, db: AsyncSession = Depends(get_db)) -> schemas.AdverseEventOut:
    ae = await crud.get_adverse_event(db, ae_id)
    if not ae:
        raise HTTPException(status_code=404, detail="Adverse event not found")
    return schemas.AdverseEventOut.model_validate(ae)


@router.patch("/{ae_id}", response_model=schemas.AdverseEventOut)
async def update_adverse_event(ae_id: int, data: schemas.AdverseEventUpdate, db: AsyncSession = Depends(get_db)) -> schemas.AdverseEventOut:
    ae = await crud.get_adverse_event(db, ae_id)
    if not ae:
        raise HTTPException(status_code=404, detail="Adverse event not found")
    updated = await crud.update_adverse_event(db, ae, data)
    return schemas.AdverseEventOut.model_validate(updated)
