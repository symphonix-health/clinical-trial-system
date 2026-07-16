"""CRUD and domain operations."""

from __future__ import annotations

import datetime as dt
import hashlib
import secrets
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, schemas


def _next_subject_number(study_id: int, count: int) -> str:
    return f"S{study_id:03d}-{count + 1:04d}"


def _sha256_chain(previous_hash: str | None, payload: str) -> str:
    base = previous_hash or "0" * 64
    return hashlib.sha256(f"{base}:{payload}".encode()).hexdigest()


def _compute_susar_deadline(seriousness: str, onset_date: dt.date) -> dt.datetime | None:
    if seriousness in ("serious", "life_threatening", "fatal"):
        days = 7 if seriousness == "serious" else 1
        return dt.datetime.combine(onset_date + dt.timedelta(days=days), dt.time.max)
    return None


# Audit
async def create_audit_entry(
    db: AsyncSession, obj_in: schemas.AuditEntryCreate
) -> models.AuditEntry:
    last = await db.execute(
        select(models.AuditEntry).where(models.AuditEntry.study_id == obj_in.study_id).order_by(models.AuditEntry.id.desc()).limit(1)
    )
    previous = last.scalar_one_or_none()
    payload = f"{obj_in.actor_id}:{obj_in.action}:{obj_in.resource_type}:{obj_in.resource_id}"
    entry = models.AuditEntry(
        study_id=obj_in.study_id,
        actor_id=obj_in.actor_id,
        purpose_of_use=obj_in.purpose_of_use,
        action=obj_in.action,
        resource_type=obj_in.resource_type,
        resource_id=obj_in.resource_id,
        previous_hash=previous.entry_hash if previous else None,
        entry_hash=_sha256_chain(previous.entry_hash if previous else None, payload),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


# Studies
async def create_study(db: AsyncSession, obj_in: schemas.StudyCreate) -> models.Study:
    study = models.Study(**obj_in.model_dump())
    db.add(study)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Study with this protocol number already exists") from exc
    await db.refresh(study)
    await create_audit_entry(
        db,
        schemas.AuditEntryCreate(
            actor_id="system", purpose_of_use="study_setup", action="create_study", resource_type="Study", resource_id=study.id
        ),
    )
    return study


async def get_study(db: AsyncSession, study_id: int) -> models.Study | None:
    return await db.get(models.Study, study_id)


async def list_studies(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[models.Study]:
    result = await db.execute(select(models.Study).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_study(db: AsyncSession, study: models.Study, obj_in: schemas.StudyUpdate) -> models.Study:
    data = obj_in.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(study, field, value)
    await db.commit()
    await db.refresh(study)
    await create_audit_entry(
        db,
        schemas.AuditEntryCreate(
            actor_id="system", purpose_of_use="study_setup", action="update_study", resource_type="Study", resource_id=study.id
        ),
    )
    return study


async def approve_study(db: AsyncSession, study: models.Study, version_number: str) -> models.Study:
    study.status = models.StudyStatus.approved.value
    pv = models.ProtocolVersion(
        study_id=study.id,
        version_number=version_number,
        approval_date=dt.date.today(),
        effective_date=dt.date.today(),
    )
    db.add(pv)
    await db.commit()
    await db.refresh(study)
    return study


# Protocol versions
async def create_protocol_version(db: AsyncSession, obj_in: schemas.ProtocolVersionCreate) -> models.ProtocolVersion:
    pv = models.ProtocolVersion(**obj_in.model_dump())
    db.add(pv)
    await db.commit()
    await db.refresh(pv)
    return pv


# Sites
async def create_site(db: AsyncSession, obj_in: schemas.SiteCreate) -> models.Site:
    site = models.Site(**obj_in.model_dump())
    db.add(site)
    await db.commit()
    await db.refresh(site)
    for task in ("ethics", "contract", "delegation_log", "training", "pharmacy_setup"):
        db.add(models.SiteActivationChecklist(site_id=site.id, task_name=task))
    await db.commit()
    return site


async def get_site(db: AsyncSession, site_id: int) -> models.Site | None:
    return await db.get(models.Site, site_id)


async def list_sites(db: AsyncSession, study_id: int | None = None) -> list[models.Site]:
    stmt = select(models.Site)
    if study_id is not None:
        stmt = stmt.where(models.Site.study_id == study_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_site(db: AsyncSession, site: models.Site, obj_in: schemas.SiteUpdate) -> models.Site:
    for field, value in obj_in.model_dump(exclude_unset=True).items():
        setattr(site, field, value)
    await db.commit()
    await db.refresh(site)
    return site


async def get_site_checklist(db: AsyncSession, site_id: int) -> list[models.SiteActivationChecklist]:
    result = await db.execute(select(models.SiteActivationChecklist).where(models.SiteActivationChecklist.site_id == site_id))
    return list(result.scalars().all())


async def update_checklist_task(db: AsyncSession, site_id: int, task_name: str, status: str, evidence: str | None) -> models.SiteActivationChecklist | None:
    result = await db.execute(
        select(models.SiteActivationChecklist).where(
            models.SiteActivationChecklist.site_id == site_id,
            models.SiteActivationChecklist.task_name == task_name,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        return None
    task.status = status
    task.evidence_reference = evidence
    await db.commit()
    await db.refresh(task)
    return task


# Subjects
async def create_subject(db: AsyncSession, obj_in: schemas.SubjectCreate) -> models.Subject:
    count_result = await db.execute(select(func.count(models.Subject.id)).where(models.Subject.study_id == obj_in.study_id))
    count = count_result.scalar() or 0
    subject = models.Subject(
        **obj_in.model_dump(exclude={"screening_id"}),
        subject_number=_next_subject_number(obj_in.study_id, count),
        screening_id=obj_in.screening_id,
    )
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return subject


async def get_subject(db: AsyncSession, subject_id: int) -> models.Subject | None:
    result = await db.execute(
        select(models.Subject)
        .where(models.Subject.id == subject_id)
        .options(selectinload(models.Subject.visits))
    )
    return result.scalar_one_or_none()


async def list_subjects(db: AsyncSession, study_id: int | None = None, site_id: int | None = None) -> list[models.Subject]:
    stmt = select(models.Subject)
    if study_id is not None:
        stmt = stmt.where(models.Subject.study_id == study_id)
    if site_id is not None:
        stmt = stmt.where(models.Subject.site_id == site_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_subject(db: AsyncSession, subject: models.Subject, obj_in: schemas.SubjectUpdate) -> models.Subject:
    for field, value in obj_in.model_dump(exclude_unset=True).items():
        setattr(subject, field, value)
    await db.commit()
    await db.refresh(subject)
    return subject


async def record_consent(db: AsyncSession, subject: models.Subject, obj_in: schemas.InformedConsentCreate) -> models.InformedConsent:
    subject.consent_version = obj_in.consent_version
    subject.consent_date = obj_in.consent_date.date()
    subject.enrolment_status = models.EnrolmentStatus.enrolled.value
    consent = models.InformedConsent(**obj_in.model_dump())
    db.add(consent)
    await db.commit()
    await db.refresh(consent)
    return consent


async def withdraw_subject(db: AsyncSession, subject: models.Subject, reason: str) -> models.Subject:
    subject.enrolment_status = models.EnrolmentStatus.withdrawn.value
    consent_result = await db.execute(
        select(models.InformedConsent).where(models.InformedConsent.subject_id == subject.id).order_by(models.InformedConsent.id.desc()).limit(1)
    )
    consent = consent_result.scalar_one_or_none()
    if consent:
        consent.withdrawn_at = dt.datetime.utcnow()
        consent.withdrawal_reason = reason
    for visit in subject.visits:
        if visit.status == models.VisitStatus.scheduled.value:
            visit.status = models.VisitStatus.missed.value
    await db.commit()
    await db.refresh(subject)
    return subject


async def randomise_subject(db: AsyncSession, subject: models.Subject, arm: str, factors: dict[str, Any] | None) -> models.Subject:
    subject.randomisation_arm = arm
    subject.stratification_factors = factors or {}
    await db.commit()
    await db.refresh(subject)
    return subject


# Visits
async def create_visit(db: AsyncSession, obj_in: schemas.SubjectVisitCreate) -> models.SubjectVisit:
    visit = models.SubjectVisit(**obj_in.model_dump())
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    return visit


async def get_visit(db: AsyncSession, visit_id: int) -> models.SubjectVisit | None:
    result = await db.execute(
        select(models.SubjectVisit)
        .where(models.SubjectVisit.id == visit_id)
        .options(selectinload(models.SubjectVisit.subject))
    )
    return result.scalar_one_or_none()


async def update_visit(db: AsyncSession, visit: models.SubjectVisit, obj_in: schemas.SubjectVisitUpdate) -> models.SubjectVisit:
    for field, value in obj_in.model_dump(exclude_unset=True).items():
        setattr(visit, field, value)
    if visit.actual_date and visit.status == models.VisitStatus.scheduled.value:
        actual = visit.actual_date.date() if isinstance(visit.actual_date, dt.datetime) else visit.actual_date
        min_date = visit.window_min_date.date() if isinstance(visit.window_min_date, dt.datetime) else visit.window_min_date
        max_date = visit.window_max_date.date() if isinstance(visit.window_max_date, dt.datetime) else visit.window_max_date
        if actual < min_date or actual > max_date:
            await create_protocol_deviation(
                db,
                schemas.ProtocolDeviationCreate(
                    study_id=visit.subject.study_id,
                    subject_id=visit.subject_id,
                    category="visit_window",
                    description=f"Visit {visit.visit_definition_id} occurred outside scheduled window",
                    severity="minor",
                ),
            )
    await db.commit()
    await db.refresh(visit)
    return visit


async def flag_missed_visits(db: AsyncSession, as_of: dt.date | None = None) -> list[models.SubjectVisit]:
    as_of = as_of or dt.date.today()
    result = await db.execute(
        select(models.SubjectVisit)
        .options(selectinload(models.SubjectVisit.subject))
        .where(models.SubjectVisit.status == models.VisitStatus.scheduled.value)
        .where(models.SubjectVisit.window_max_date < as_of)
    )
    flagged: list[models.SubjectVisit] = []
    for visit in result.scalars().all():
        visit.status = models.VisitStatus.missed.value
        await create_protocol_deviation(
            db,
            schemas.ProtocolDeviationCreate(
                study_id=visit.subject.study_id,
                subject_id=visit.subject_id,
                category="missed_visit",
                description=f"Visit {visit.visit_definition_id} missed after {visit.window_max_date}",
                severity="major" if visit.visit_definition_id in ("V1", "V2") else "minor",
            ),
        )
        flagged.append(visit)
    await db.commit()
    return flagged


# Adverse events
async def create_adverse_event(db: AsyncSession, obj_in: schemas.AdverseEventCreate) -> models.AdverseEvent:
    data = obj_in.model_dump()
    computed_susar = obj_in.seriousness == "life_threatening" and obj_in.causality in {"related", "possibly_related"}
    data["susar_flag"] = obj_in.susar_flag or computed_susar
    deadline = _compute_susar_deadline(obj_in.seriousness, obj_in.onset_date)
    ae = models.AdverseEvent(
        **data,
        regulatory_report_deadline=deadline,
    )
    db.add(ae)
    await db.commit()
    await db.refresh(ae)
    return ae


async def get_adverse_event(db: AsyncSession, ae_id: int) -> models.AdverseEvent | None:
    return await db.get(models.AdverseEvent, ae_id)


async def list_adverse_events(db: AsyncSession, study_id: int | None = None) -> list[models.AdverseEvent]:
    stmt = select(models.AdverseEvent)
    if study_id is not None:
        stmt = stmt.where(models.AdverseEvent.study_id == study_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_adverse_event(db: AsyncSession, ae: models.AdverseEvent, obj_in: schemas.AdverseEventUpdate) -> models.AdverseEvent:
    for field, value in obj_in.model_dump(exclude_unset=True).items():
        setattr(ae, field, value)
    await db.commit()
    await db.refresh(ae)
    return ae


# Protocol deviations
async def create_protocol_deviation(db: AsyncSession, obj_in: schemas.ProtocolDeviationCreate) -> models.ProtocolDeviation:
    pd = models.ProtocolDeviation(**obj_in.model_dump())
    db.add(pd)
    await db.commit()
    await db.refresh(pd)
    return pd


async def list_protocol_deviations(db: AsyncSession, study_id: int | None = None) -> list[models.ProtocolDeviation]:
    stmt = select(models.ProtocolDeviation)
    if study_id is not None:
        stmt = stmt.where(models.ProtocolDeviation.study_id == study_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


# Investigational product
async def create_investigational_product(db: AsyncSession, obj_in: schemas.InvestigationalProductCreate) -> models.InvestigationalProduct:
    ip = models.InvestigationalProduct(**obj_in.model_dump())
    db.add(ip)
    await db.commit()
    await db.refresh(ip)
    return ip


async def get_investigational_product(db: AsyncSession, product_id: int) -> models.InvestigationalProduct | None:
    return await db.get(models.InvestigationalProduct, product_id)


async def receive_shipment(db: AsyncSession, shipment: models.IpShipment, received_by: str, condition_ok: bool) -> models.IpShipment:
    shipment.received_at = dt.datetime.utcnow()
    shipment.received_by = received_by
    shipment.condition_ok = condition_ok
    if condition_ok:
        product = await get_investigational_product(db, shipment.product_id)
        if product:
            product.quantity_on_hand += shipment.quantity_shipped
    await db.commit()
    await db.refresh(shipment)
    return shipment


async def create_ip_shipment(db: AsyncSession, obj_in: schemas.IpShipmentCreate) -> models.IpShipment:
    shipment = models.IpShipment(**obj_in.model_dump())
    db.add(shipment)
    await db.commit()
    await db.refresh(shipment)
    return shipment


async def create_ip_dispense(db: AsyncSession, obj_in: schemas.IpDispenseCreate) -> models.IpDispense:
    dispense = models.IpDispense(**obj_in.model_dump())
    db.add(dispense)
    product = await get_investigational_product(db, obj_in.product_id)
    if product:
        product.quantity_on_hand -= obj_in.quantity_dispensed
    await db.commit()
    await db.refresh(dispense)
    return dispense


async def destroy_ip_dispense(db: AsyncSession, dispense: models.IpDispense, payload: schemas.IpDestroy) -> models.IpDispense:
    dispense.destroyed_at = payload.destroyed_at
    dispense.destroyed_by = payload.destroyed_by
    await db.commit()
    await db.refresh(dispense)
    return dispense


# Regulatory documents
async def create_regulatory_document(db: AsyncSession, obj_in: schemas.RegulatoryDocumentCreate) -> models.RegulatoryDocument:
    doc = models.RegulatoryDocument(**obj_in.model_dump())
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def list_regulatory_documents(db: AsyncSession, study_id: int) -> list[models.RegulatoryDocument]:
    result = await db.execute(select(models.RegulatoryDocument).where(models.RegulatoryDocument.study_id == study_id))
    return list(result.scalars().all())


# Queries
async def create_query(db: AsyncSession, obj_in: schemas.QueryCreate) -> models.Query:
    query = models.Query(**obj_in.model_dump())
    db.add(query)
    await db.commit()
    await db.refresh(query)
    return query


async def get_query(db: AsyncSession, query_id: int) -> models.Query | None:
    return await db.get(models.Query, query_id)


async def update_query(db: AsyncSession, query: models.Query, obj_in: schemas.QueryUpdate) -> models.Query:
    for field, value in obj_in.model_dump(exclude_unset=True).items():
        setattr(query, field, value)
    await db.commit()
    await db.refresh(query)
    return query


async def list_queries(db: AsyncSession, study_id: int | None = None) -> list[models.Query]:
    stmt = select(models.Query)
    if study_id is not None:
        stmt = stmt.where(models.Query.study_id == study_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


# Budget and invoices
async def create_study_budget(db: AsyncSession, obj_in: schemas.StudyBudgetCreate) -> models.StudyBudget:
    budget = models.StudyBudget(**obj_in.model_dump())
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return budget


async def get_study_budget(db: AsyncSession, budget_id: int) -> models.StudyBudget | None:
    return await db.get(models.StudyBudget, budget_id)


async def update_study_budget(db: AsyncSession, budget: models.StudyBudget, obj_in: schemas.StudyBudgetUpdate) -> models.StudyBudget:
    if obj_in.actual_amount is not None:
        budget.actual_amount = obj_in.actual_amount
    await db.commit()
    await db.refresh(budget)
    return budget


async def create_invoice(db: AsyncSession, obj_in: schemas.InvoiceCreate) -> models.Invoice:
    invoice = models.Invoice(**obj_in.model_dump())
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice


# Agent subjects
async def create_agent_subject(db: AsyncSession, obj_in: schemas.AgentSubjectCreate) -> models.AgentSubject:
    agent = models.AgentSubject(**obj_in.model_dump())
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


async def get_agent_subject(db: AsyncSession, agent_id: int) -> models.AgentSubject | None:
    return await db.get(models.AgentSubject, agent_id)


async def list_agent_subjects(db: AsyncSession, enrolled_study_id: int | None = None) -> list[models.AgentSubject]:
    stmt = select(models.AgentSubject)
    if enrolled_study_id is not None:
        stmt = stmt.where(models.AgentSubject.enrolled_study_id == enrolled_study_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_agent_subject(db: AsyncSession, agent: models.AgentSubject, obj_in: schemas.AgentSubjectUpdate) -> models.AgentSubject:
    for field, value in obj_in.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)
    await db.commit()
    await db.refresh(agent)
    return agent


async def create_agent_attestation(db: AsyncSession, obj_in: schemas.AgentAttestationCreate) -> models.AgentAttestation:
    att = models.AgentAttestation(**obj_in.model_dump())
    db.add(att)
    agent = await get_agent_subject(db, obj_in.agent_subject_id)
    if agent:
        agent.attestation_status = "valid"
    await db.commit()
    await db.refresh(att)
    return att


async def create_agent_consent_contract(db: AsyncSession, obj_in: schemas.AgentConsentContractCreate) -> models.AgentConsentContract:
    contract = models.AgentConsentContract(**obj_in.model_dump())
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    return contract


# Agent cohorts
async def create_agent_cohort(db: AsyncSession, obj_in: schemas.AgentCohortCreate) -> models.AgentCohort:
    cohort = models.AgentCohort(**obj_in.model_dump())
    db.add(cohort)
    await db.commit()
    await db.refresh(cohort)
    return cohort


async def get_agent_cohort(db: AsyncSession, cohort_id: int) -> models.AgentCohort | None:
    return await db.get(models.AgentCohort, cohort_id)


async def add_agent_to_cohort(db: AsyncSession, cohort_id: int, agent_subject_id: int) -> models.AgentCohortMembership:
    membership = models.AgentCohortMembership(cohort_id=cohort_id, agent_subject_id=agent_subject_id)
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership


# Synthetic environments
async def create_synthetic_environment(db: AsyncSession, obj_in: schemas.SyntheticEnvironmentCreate) -> models.SyntheticEnvironment:
    env = models.SyntheticEnvironment(
        **obj_in.model_dump(),
        reset_token=secrets.token_urlsafe(16),
        reproducibility_hash=hashlib.sha256(str(obj_in.model_dump_json()).encode()).hexdigest(),
    )
    db.add(env)
    await db.commit()
    await db.refresh(env)
    return env


async def get_synthetic_environment(db: AsyncSession, env_id: int) -> models.SyntheticEnvironment | None:
    return await db.get(models.SyntheticEnvironment, env_id)


# Agent runs
async def create_agent_run(db: AsyncSession, obj_in: schemas.AgentRunCreate) -> models.AgentRun:
    run = models.AgentRun(
        environment_id=obj_in.environment_id,
        agent_subject_ids=obj_in.agent_subject_ids,
        reproducibility_hash=secrets.token_urlsafe(16),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


async def get_agent_run(db: AsyncSession, run_id: int) -> models.AgentRun | None:
    return await db.get(models.AgentRun, run_id)


async def complete_agent_run(db: AsyncSession, run: models.AgentRun, metrics: dict[str, Any], trace_url: str | None) -> models.AgentRun:
    run.completed_at = dt.datetime.utcnow()
    run.metrics_snapshot = metrics
    run.trace_artifact_url = trace_url
    db.add(run)
    await db.commit()
    await db.refresh(run)
    for metric_name, value in metrics.items():
        threshold = 0.5 if "rate" in metric_name else 0.8
        pass_flag = value >= threshold
        db.add(
            models.AgentMetric(
                run_id=run.id,
                metric_name=metric_name,
                value=value,
                threshold=threshold,
                pass_flag=pass_flag,
            )
        )
    await db.commit()
    return run


async def list_agent_metrics(db: AsyncSession, run_id: int | None = None) -> list[models.AgentMetric]:
    stmt = select(models.AgentMetric)
    if run_id is not None:
        stmt = stmt.where(models.AgentMetric.run_id == run_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_agent_trial_arm(db: AsyncSession, obj_in: schemas.AgentTrialArmCreate) -> models.AgentTrialArm:
    arm = models.AgentTrialArm(**obj_in.model_dump())
    db.add(arm)
    await db.commit()
    await db.refresh(arm)
    return arm


async def create_agent_bias_report(db: AsyncSession, obj_in: schemas.AgentBiasReportCreate) -> models.AgentBiasReport:
    report = models.AgentBiasReport(**obj_in.model_dump())
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def evaluate_release_gate(db: AsyncSession, cohort_id: int) -> schemas.ReleaseGateResult:
    result = await db.execute(select(models.AgentMetric).where(models.AgentMetric.run_id.in_(
        select(models.AgentRun.id).where(models.AgentRun.environment_id.in_(
            select(models.SyntheticEnvironment.id)  # simplified; real impl uses cohort linkage
        ))
    )))
    metrics = list(result.scalars().all())
    passed: list[str] = []
    failed: list[dict[str, Any]] = []
    for metric in metrics:
        if metric.pass_flag:
            passed.append(metric.metric_name)
        else:
            failed.append({"metric": metric.metric_name, "value": metric.value, "threshold": metric.threshold})
    status = "promoted" if not failed else "blocked"
    return schemas.ReleaseGateResult(cohort_id=cohort_id, status=status, passed_metrics=passed, failed_metrics=failed)


# Reports
async def recruitment_report(db: AsyncSession, study_id: int) -> schemas.RecruitmentReport:
    subjects = await list_subjects(db, study_id=study_id)
    sites = await list_sites(db, study_id=study_id)
    by_site = []
    for site in sites:
        site_subjects = [s for s in subjects if s.site_id == site.id]
        by_site.append(
            {
                "site_id": site.id,
                "site_code": site.site_code,
                "enrolled": sum(1 for s in site_subjects if s.enrolment_status == models.EnrolmentStatus.enrolled.value),
                "screening": sum(1 for s in site_subjects if s.enrolment_status == models.EnrolmentStatus.screening.value),
                "withdrawn": sum(1 for s in site_subjects if s.enrolment_status == models.EnrolmentStatus.withdrawn.value),
            }
        )
    study = await get_study(db, study_id)
    return schemas.RecruitmentReport(
        study_id=study_id,
        planned=study.planned_subjects if study else 0,
        enrolled=sum(1 for s in subjects if s.enrolment_status == models.EnrolmentStatus.enrolled.value),
        screen_failed=sum(1 for s in subjects if s.enrolment_status == models.EnrolmentStatus.screening.value and s.randomisation_arm is None),
        withdrawn=sum(1 for s in subjects if s.enrolment_status == models.EnrolmentStatus.withdrawn.value),
        by_site=by_site,
    )


async def safety_report(db: AsyncSession, study_id: int) -> schemas.SafetyReport:
    aes = await list_adverse_events(db, study_id=study_id)
    by_severity: dict[str, int] = {}
    by_seriousness: dict[str, int] = {}
    days_to_report: list[int] = []
    pending_susars = 0
    now = dt.datetime.utcnow()
    for ae in aes:
        by_severity[ae.severity] = by_severity.get(ae.severity, 0) + 1
        by_seriousness[ae.seriousness] = by_seriousness.get(ae.seriousness, 0) + 1
        if ae.susar_flag and ae.status != models.AEStatus.submitted.value:
            pending_susars += 1
        if ae.regulatory_report_deadline:
            days = (ae.regulatory_report_deadline - now).days
            days_to_report.append(days)
    return schemas.SafetyReport(
        study_id=study_id,
        total_aes=len(aes),
        by_severity=by_severity,
        by_seriousness=by_seriousness,
        pending_susars=pending_susars,
        days_to_report=days_to_report,
    )


async def etmf_report(db: AsyncSession, study_id: int) -> schemas.eTMFReport:
    docs = await list_regulatory_documents(db, study_id)
    folders: dict[str, dict[str, Any]] = {}
    expired = 0
    today = dt.date.today()
    for doc in docs:
        folder = doc.document_type
        folders.setdefault(folder, {"required": 5, "uploaded": 0, "expired": 0})
        folders[folder]["uploaded"] += 1
        if doc.expiry_date and doc.expiry_date < today:
            folders[folder]["expired"] += 1
            expired += 1
    return schemas.eTMFReport(
        study_id=study_id,
        folders=[{"name": k, **v} for k, v in folders.items()],
        expired_count=expired,
    )


async def ip_accountability_report(db: AsyncSession, study_id: int, site_id: int) -> schemas.AccountabilityReport:
    site = await get_site(db, site_id)
    if not site or site.study_id != study_id:
        raise ValueError("Invalid site for study")
    shipments = await db.execute(
        select(models.IpShipment).where(models.IpShipment.to_site_id == site_id, models.IpShipment.condition_ok == True)
    )
    shipped = sum(s.quantity_shipped for s in shipments.scalars().all())
    dispenses_result = await db.execute(
        select(models.IpDispense).join(models.InvestigationalProduct).where(models.InvestigationalProduct.site_id == site_id)
    )
    dispenses = list(dispenses_result.scalars().all())
    dispensed = sum(d.quantity_dispensed for d in dispenses)
    returned = sum(d.quantity_returned for d in dispenses)
    destroyed = sum(d.quantity_dispensed - d.quantity_returned for d in dispenses if d.destroyed_at)
    on_hand_result = await db.execute(
        select(func.sum(models.InvestigationalProduct.quantity_on_hand)).where(models.InvestigationalProduct.site_id == site_id)
    )
    on_hand = on_hand_result.scalar() or 0
    return schemas.AccountabilityReport(
        study_id=study_id,
        site_id=site_id,
        shipped=shipped,
        dispensed=dispensed,
        returned=returned,
        destroyed=destroyed,
        on_hand=int(on_hand),
    )
