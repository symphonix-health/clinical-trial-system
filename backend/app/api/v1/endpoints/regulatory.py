"""Regulatory document endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/regulatory-documents", tags=["regulatory"])


@router.post("", response_model=schemas.RegulatoryDocumentOut)
async def create_document(data: schemas.RegulatoryDocumentCreate, db: AsyncSession = Depends(get_db)) -> schemas.RegulatoryDocumentOut:
    doc = await crud.create_regulatory_document(db, data)
    return schemas.RegulatoryDocumentOut.model_validate(doc)


@router.get("", response_model=list[schemas.RegulatoryDocumentOut])
async def list_documents(study_id: int, db: AsyncSession = Depends(get_db)) -> list[schemas.RegulatoryDocumentOut]:
    docs = await crud.list_regulatory_documents(db, study_id)
    return [schemas.RegulatoryDocumentOut.model_validate(d) for d in docs]
