"""Budget and invoice endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=schemas.StudyBudgetOut)
async def create_budget(data: schemas.StudyBudgetCreate, db: AsyncSession = Depends(get_db)) -> schemas.StudyBudgetOut:
    budget = await crud.create_study_budget(db, data)
    return schemas.StudyBudgetOut.model_validate(budget)


@router.patch("/{budget_id}", response_model=schemas.StudyBudgetOut)
async def update_budget(budget_id: int, data: schemas.StudyBudgetUpdate, db: AsyncSession = Depends(get_db)) -> schemas.StudyBudgetOut:
    budget = await crud.get_study_budget(db, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    updated = await crud.update_study_budget(db, budget, data)
    return schemas.StudyBudgetOut.model_validate(updated)


@router.post("/invoices", response_model=schemas.InvoiceOut)
async def create_invoice(data: schemas.InvoiceCreate, db: AsyncSession = Depends(get_db)) -> schemas.InvoiceOut:
    invoice = await crud.create_invoice(db, data)
    return schemas.InvoiceOut.model_validate(invoice)
