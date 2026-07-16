"""Site endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/sites", tags=["sites"])


@router.post("", response_model=schemas.SiteOut)
async def create_site(data: schemas.SiteCreate, db: AsyncSession = Depends(get_db)) -> schemas.SiteOut:
    site = await crud.create_site(db, data)
    return schemas.SiteOut.model_validate(site)


@router.get("", response_model=list[schemas.SiteOut])
async def list_sites(study_id: int | None = None, db: AsyncSession = Depends(get_db)) -> list[schemas.SiteOut]:
    sites = await crud.list_sites(db, study_id=study_id)
    return [schemas.SiteOut.model_validate(s) for s in sites]


@router.get("/{site_id}", response_model=schemas.SiteOut)
async def get_site(site_id: int, db: AsyncSession = Depends(get_db)) -> schemas.SiteOut:
    site = await crud.get_site(db, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return schemas.SiteOut.model_validate(site)


@router.patch("/{site_id}", response_model=schemas.SiteOut)
async def update_site(site_id: int, data: schemas.SiteUpdate, db: AsyncSession = Depends(get_db)) -> schemas.SiteOut:
    site = await crud.get_site(db, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    updated = await crud.update_site(db, site, data)
    return schemas.SiteOut.model_validate(updated)


@router.get("/{site_id}/checklist", response_model=list[schemas.SiteActivationChecklistOut])
async def get_site_checklist(site_id: int, db: AsyncSession = Depends(get_db)) -> list[schemas.SiteActivationChecklistOut]:
    tasks = await crud.get_site_checklist(db, site_id)
    return [schemas.SiteActivationChecklistOut.model_validate(t) for t in tasks]


@router.patch("/{site_id}/checklist/{task_name}", response_model=schemas.SiteActivationChecklistOut)
async def update_checklist_task(
    site_id: int,
    task_name: str,
    status: str,
    evidence: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> schemas.SiteActivationChecklistOut:
    task = await crud.update_checklist_task(db, site_id, task_name, status, evidence)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return schemas.SiteActivationChecklistOut.model_validate(task)
