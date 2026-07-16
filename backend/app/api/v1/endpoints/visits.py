"""Visit endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/visits", tags=["visits"])


@router.post("", response_model=schemas.SubjectVisitOut)
async def create_visit(data: schemas.SubjectVisitCreate, db: AsyncSession = Depends(get_db)) -> schemas.SubjectVisitOut:
    visit = await crud.create_visit(db, data)
    return schemas.SubjectVisitOut.model_validate(visit)


@router.get("/{visit_id}", response_model=schemas.SubjectVisitOut)
async def get_visit(visit_id: int, db: AsyncSession = Depends(get_db)) -> schemas.SubjectVisitOut:
    visit = await crud.get_visit(db, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    return schemas.SubjectVisitOut.model_validate(visit)


@router.patch("/{visit_id}", response_model=schemas.SubjectVisitOut)
async def update_visit(visit_id: int, data: schemas.SubjectVisitUpdate, db: AsyncSession = Depends(get_db)) -> schemas.SubjectVisitOut:
    visit = await crud.get_visit(db, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    updated = await crud.update_visit(db, visit, data)
    return schemas.SubjectVisitOut.model_validate(updated)


@router.post("/flag-missed", response_model=list[schemas.SubjectVisitOut])
async def flag_missed_visits(db: AsyncSession = Depends(get_db)) -> list[schemas.SubjectVisitOut]:
    visits = await crud.flag_missed_visits(db)
    return [schemas.SubjectVisitOut.model_validate(v) for v in visits]
