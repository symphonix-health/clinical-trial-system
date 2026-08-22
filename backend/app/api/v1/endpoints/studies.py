"""Study endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.auth import require_auth
from app.database import get_db

router = APIRouter(prefix="/studies", tags=["studies"])


@router.post("", response_model=schemas.StudyOut)
async def create_study(
    data: schemas.StudyCreate,
    db: AsyncSession = Depends(get_db),
) -> schemas.StudyOut:
    study = await crud.create_study(db, data)
    return schemas.StudyOut.model_validate(study)


@router.get("", response_model=list[schemas.StudyOut])
async def list_studies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[schemas.StudyOut]:
    studies = await crud.list_studies(db, skip=skip, limit=limit)
    return [schemas.StudyOut.model_validate(s) for s in studies]


@router.get("/{study_id}", response_model=schemas.StudyOut)
async def get_study(
    study_id: int,
    db: AsyncSession = Depends(get_db),
) -> schemas.StudyOut:
    study = await crud.get_study(db, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return schemas.StudyOut.model_validate(study)


@router.patch("/{study_id}", response_model=schemas.StudyOut)
async def update_study(
    study_id: int,
    data: schemas.StudyUpdate,
    db: AsyncSession = Depends(get_db),
) -> schemas.StudyOut:
    study = await crud.get_study(db, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    updated = await crud.update_study(db, study, data)
    return schemas.StudyOut.model_validate(updated)


@router.post("/{study_id}/approve", response_model=schemas.StudyOut)
async def approve_study(
    study_id: int,
    version_number: str,
    db: AsyncSession = Depends(get_db),
) -> schemas.StudyOut:
    study = await crud.get_study(db, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    updated = await crud.approve_study(db, study, version_number)
    return schemas.StudyOut.model_validate(updated)


@router.post(
    "/{study_id}/protocol-versions",
    response_model=schemas.ProtocolVersionOut,
)
async def create_protocol_version(
    study_id: int,
    data: schemas.ProtocolVersionCreate,
    db: AsyncSession = Depends(get_db),
) -> schemas.ProtocolVersionOut:
    data.study_id = study_id
    pv = await crud.create_protocol_version(db, data)
    return schemas.ProtocolVersionOut.model_validate(pv)


@router.post(
    "/{study_id}/flag-reconsent",
    response_model=list[schemas.SubjectOut],
)
async def flag_reconsent(
    study_id: int,
    protocol_version: str,
    _auth: dict = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> list[schemas.SubjectOut]:
    """Flag enrolled subjects for re-consent against an amended protocol.

    FR-C-33 / REQ-CTS-NAT-004. Flagged subjects are suspended from further IP
    dispensing until a re-consent is recorded.
    """
    study = await crud.get_study(db, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    flagged = await crud.flag_reconsent_required(
        db,
        study_id,
        protocol_version,
    )
    return [schemas.SubjectOut.model_validate(s) for s in flagged]
