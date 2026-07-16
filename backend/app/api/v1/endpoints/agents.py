"""Agentic subject endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/subjects", response_model=schemas.AgentSubjectOut)
async def create_agent_subject(data: schemas.AgentSubjectCreate, db: AsyncSession = Depends(get_db)) -> schemas.AgentSubjectOut:
    agent = await crud.create_agent_subject(db, data)
    return schemas.AgentSubjectOut.model_validate(agent)


@router.get("/subjects", response_model=list[schemas.AgentSubjectOut])
async def list_agent_subjects(enrolled_study_id: int | None = None, db: AsyncSession = Depends(get_db)) -> list[schemas.AgentSubjectOut]:
    agents = await crud.list_agent_subjects(db, enrolled_study_id=enrolled_study_id)
    return [schemas.AgentSubjectOut.model_validate(a) for a in agents]


@router.get("/subjects/{agent_id}", response_model=schemas.AgentSubjectOut)
async def get_agent_subject(agent_id: int, db: AsyncSession = Depends(get_db)) -> schemas.AgentSubjectOut:
    agent = await crud.get_agent_subject(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent subject not found")
    return schemas.AgentSubjectOut.model_validate(agent)


@router.patch("/subjects/{agent_id}", response_model=schemas.AgentSubjectOut)
async def update_agent_subject(agent_id: int, data: schemas.AgentSubjectUpdate, db: AsyncSession = Depends(get_db)) -> schemas.AgentSubjectOut:
    agent = await crud.get_agent_subject(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent subject not found")
    updated = await crud.update_agent_subject(db, agent, data)
    return schemas.AgentSubjectOut.model_validate(updated)


@router.post("/subjects/{agent_id}/attestations", response_model=schemas.AgentAttestationOut)
async def create_attestation(agent_id: int, data: schemas.AgentAttestationCreate, db: AsyncSession = Depends(get_db)) -> schemas.AgentAttestationOut:
    data.agent_subject_id = agent_id
    att = await crud.create_agent_attestation(db, data)
    return schemas.AgentAttestationOut.model_validate(att)


@router.post("/subjects/{agent_id}/consent-contracts", response_model=schemas.AgentConsentContractOut)
async def create_consent_contract(agent_id: int, data: schemas.AgentConsentContractCreate, db: AsyncSession = Depends(get_db)) -> schemas.AgentConsentContractOut:
    data.agent_subject_id = agent_id
    contract = await crud.create_agent_consent_contract(db, data)
    return schemas.AgentConsentContractOut.model_validate(contract)


@router.post("/cohorts", response_model=schemas.AgentCohortOut)
async def create_cohort(data: schemas.AgentCohortCreate, db: AsyncSession = Depends(get_db)) -> schemas.AgentCohortOut:
    cohort = await crud.create_agent_cohort(db, data)
    return schemas.AgentCohortOut.model_validate(cohort)


@router.post("/cohorts/{cohort_id}/members")
async def add_to_cohort(cohort_id: int, agent_subject_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    membership = await crud.add_agent_to_cohort(db, cohort_id, agent_subject_id)
    return {"membership_id": membership.id}


@router.post("/environments", response_model=schemas.SyntheticEnvironmentOut)
async def create_environment(data: schemas.SyntheticEnvironmentCreate, db: AsyncSession = Depends(get_db)) -> schemas.SyntheticEnvironmentOut:
    env = await crud.create_synthetic_environment(db, data)
    return schemas.SyntheticEnvironmentOut.model_validate(env)


@router.post("/runs", response_model=schemas.AgentRunOut)
async def create_run(data: schemas.AgentRunCreate, db: AsyncSession = Depends(get_db)) -> schemas.AgentRunOut:
    run = await crud.create_agent_run(db, data)
    return schemas.AgentRunOut.model_validate(run)


@router.post("/runs/{run_id}/complete", response_model=schemas.AgentRunOut)
async def complete_run(run_id: int, metrics: dict, trace_url: str | None = None, db: AsyncSession = Depends(get_db)) -> schemas.AgentRunOut:
    run = await crud.get_agent_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    updated = await crud.complete_agent_run(db, run, metrics, trace_url)
    return schemas.AgentRunOut.model_validate(updated)


@router.get("/runs/{run_id}/metrics", response_model=list[schemas.AgentMetricOut])
async def list_run_metrics(run_id: int, db: AsyncSession = Depends(get_db)) -> list[schemas.AgentMetricOut]:
    metrics = await crud.list_agent_metrics(db, run_id=run_id)
    return [schemas.AgentMetricOut.model_validate(m) for m in metrics]


@router.post("/trial-arms", response_model=schemas.AgentTrialArmOut)
async def create_trial_arm(data: schemas.AgentTrialArmCreate, db: AsyncSession = Depends(get_db)) -> schemas.AgentTrialArmOut:
    arm = await crud.create_agent_trial_arm(db, data)
    return schemas.AgentTrialArmOut.model_validate(arm)


@router.post("/bias-reports", response_model=schemas.AgentBiasReportOut)
async def create_bias_report(data: schemas.AgentBiasReportCreate, db: AsyncSession = Depends(get_db)) -> schemas.AgentBiasReportOut:
    report = await crud.create_agent_bias_report(db, data)
    return schemas.AgentBiasReportOut.model_validate(report)


@router.get("/cohorts/{cohort_id}/release-gate", response_model=schemas.ReleaseGateResult)
async def release_gate(cohort_id: int, db: AsyncSession = Depends(get_db)) -> schemas.ReleaseGateResult:
    return await crud.evaluate_release_gate(db, cohort_id)
