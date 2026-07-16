"""Query endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/queries", tags=["queries"])


@router.post("", response_model=schemas.QueryOut)
async def create_query(data: schemas.QueryCreate, db: AsyncSession = Depends(get_db)) -> schemas.QueryOut:
    query = await crud.create_query(db, data)
    return schemas.QueryOut.model_validate(query)


@router.get("", response_model=list[schemas.QueryOut])
async def list_queries(study_id: int | None = None, db: AsyncSession = Depends(get_db)) -> list[schemas.QueryOut]:
    queries = await crud.list_queries(db, study_id=study_id)
    return [schemas.QueryOut.model_validate(q) for q in queries]


@router.get("/{query_id}", response_model=schemas.QueryOut)
async def get_query(query_id: int, db: AsyncSession = Depends(get_db)) -> schemas.QueryOut:
    query = await crud.get_query(db, query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    return schemas.QueryOut.model_validate(query)


@router.patch("/{query_id}", response_model=schemas.QueryOut)
async def update_query(query_id: int, data: schemas.QueryUpdate, db: AsyncSession = Depends(get_db)) -> schemas.QueryOut:
    query = await crud.get_query(db, query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    updated = await crud.update_query(db, query, data)
    return schemas.QueryOut.model_validate(updated)
