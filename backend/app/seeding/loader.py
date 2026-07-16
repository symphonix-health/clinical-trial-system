"""Seed the database with realistic CTMS data."""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.database import async_session
from app.seeding.data import (
    ADVERSE_EVENTS,
    AGENT_COHORTS,
    AGENT_SUBJECTS,
    BUDGETS,
    PRODUCTS,
    PROTOCOL_DEVIATIONS,
    QUERIES,
    REGULATORY_DOCUMENTS,
    SITES,
    STUDIES,
    SUBJECT_TEMPLATES,
    SYNTHETIC_ENVIRONMENTS,
)


async def _already_seeded(db: AsyncSession) -> bool:
    result = await db.execute(select(models.Study).limit(1))
    return result.scalar_one_or_none() is not None


async def seed_database() -> None:
    async with async_session() as db:
        if await _already_seeded(db):
            return
        await _seed(db)
        await db.commit()


async def _seed(db: AsyncSession) -> None:
    # Studies
    study_records: list[models.Study] = []
    for s in STUDIES:
        study = await crud.create_study(db, schemas.StudyCreate(**s))
        study_records.append(study)

    # Sites
    site_records: list[models.Site] = []
    for site_data in SITES:
        study = study_records[site_data["study_index"]]
        site = await crud.create_site(
            db,
            schemas.SiteCreate(
                study_id=study.id,
                site_code=site_data["site_code"],
                name=site_data["name"],
                organisation_id=f"org_{site_data['site_code'].lower()}",
                principal_investigator_id=site_data["pi"],
                capacity=site_data["capacity"],
            ),
        )
        if site_data["status"] == "activated":
            site.activation_status = models.SiteActivationStatus.activated.value
            for task in await crud.get_site_checklist(db, site.id):
                task.status = "complete"
        site_records.append(site)
    await db.commit()

    # Subjects
    subject_records: list[models.Subject] = []
    for tmpl in SUBJECT_TEMPLATES:
        study = study_records[tmpl["study_index"]]
        site = site_records[tmpl["site_index"]]
        subject = await crud.create_subject(
            db,
            schemas.SubjectCreate(
                study_id=study.id,
                site_id=site.id,
                screening_id=tmpl["screening_id"],
                demographics={"age": 50, "sex": "M"},
            ),
        )
        subject.enrolment_status = tmpl["status"]
        subject.randomisation_arm = tmpl["arm"]
        if tmpl["consent"]:
            subject.consent_version = tmpl["consent"]
            subject.consent_date = dt.date(2026, 1, 20)
            await db.execute(
                select(models.InformedConsent)
            )
            db.add(
                models.InformedConsent(
                    subject_id=subject.id,
                    consent_version=tmpl["consent"],
                    consent_date=dt.datetime(2026, 1, 20, 9, 0, 0),
                    document_reference=f"consent_{tmpl['screening_id']}.pdf",
                )
            )
        subject_records.append(subject)
    await db.commit()

    # Visits for enrolled subjects
    visit_date = dt.date(2026, 4, 1)
    for subject in subject_records:
        if subject.enrolment_status == models.EnrolmentStatus.enrolled.value:
            db.add(
                models.SubjectVisit(
                    subject_id=subject.id,
                    visit_definition_id="V1",
                    scheduled_date=visit_date,
                    window_min_date=visit_date - dt.timedelta(days=2),
                    window_max_date=visit_date + dt.timedelta(days=2),
                    status=models.VisitStatus.completed.value,
                    actual_date=visit_date,
                )
            )
    await db.commit()

    # Adverse events
    for ae in ADVERSE_EVENTS:
        await crud.create_adverse_event(
            db,
            schemas.AdverseEventCreate(
                study_id=study_records[ae["study_index"]].id,
                subject_id=subject_records[ae["subject_index"]].id,
                onset_date=ae["onset_date"],
                severity=ae["severity"],
                seriousness=ae["seriousness"],
                causality=ae["causality"],
                susar_flag=ae["susar"],
            ),
        )

    # Protocol deviations
    for pd in PROTOCOL_DEVIATIONS:
        await crud.create_protocol_deviation(
            db,
            schemas.ProtocolDeviationCreate(
                study_id=study_records[pd["study_index"]].id,
                subject_id=subject_records[pd["subject_index"]].id,
                category=pd["category"],
                description=pd["description"],
                severity=pd["severity"],
            ),
        )

    # IP products
    product_records: list[models.InvestigationalProduct] = []
    for p in PRODUCTS:
        site = next((s for s in site_records if s.site_code == p["site_code"] and s.study_id == study_records[p["site_study"]].id), None)
        product = await crud.create_investigational_product(
            db,
            schemas.InvestigationalProductCreate(
                sku=p["sku"],
                name=p["name"],
                lot_number=p["lot"],
                expiry_date=dt.date(2027, 1, 1),
                storage_conditions="2-8C",
                accountability_unit="capsule",
                quantity_on_hand=p["qty"],
                site_id=site.id if site else None,
            ),
        )
        product_records.append(product)

    # Regulatory documents
    for doc in REGULATORY_DOCUMENTS:
        await crud.create_regulatory_document(
            db,
            schemas.RegulatoryDocumentCreate(
                study_id=study_records[doc["study_index"]].id,
                document_type=doc["type"],
                document_reference=doc["reference"],
                version=doc["version"],
                expiry_date=doc["expiry"],
            ),
        )

    # Queries
    for q in QUERIES:
        await crud.create_query(
            db,
            schemas.QueryCreate(
                study_id=study_records[q["study_index"]].id,
                subject_id=subject_records[q["subject_index"]].id,
                raised_by=q["raised_by"],
                assigned_to=q["assigned"],
                due_date=q["due"],
            ),
        )

    # Budgets
    for b in BUDGETS:
        await crud.create_study_budget(
            db,
            schemas.StudyBudgetCreate(
                study_id=study_records[b["study_index"]].id,
                budget_category=b["category"],
                planned_amount=b["planned"],
            ),
        )
        # update actual amount
        budget = (await db.execute(select(models.StudyBudget).order_by(models.StudyBudget.id.desc()).limit(1))).scalar_one()
        budget.actual_amount = b["actual"]
    await db.commit()

    # Agent subjects
    agent_records: list[models.AgentSubject] = []
    for agent in AGENT_SUBJECTS:
        rec = await crud.create_agent_subject(
            db,
            schemas.AgentSubjectCreate(
                principal_id=agent["principal"],
                persona_key=agent["persona"],
                superpersona_contract_id=agent["contract"],
                model_version=agent["model"],
                agent_owner_id=agent["owner"],
                autonomy_level=agent["autonomy"],
                safety_class=agent["safety"],
                registration_source=agent["source"],
            ),
        )
        agent_records.append(rec)

    # Agent cohorts
    cohort_records: list[models.AgentCohort] = []
    for cohort in AGENT_COHORTS:
        rec = await crud.create_agent_cohort(
            db,
            schemas.AgentCohortCreate(
                name=cohort["name"],
                cohort_type=cohort["type"],
                capability_profile=cohort["profile"],
                model_family=cohort["family"],
                evaluation_objective=cohort["objective"],
            ),
        )
        cohort_records.append(rec)

    # Assign agents to cohorts
    for idx, agent in enumerate(agent_records):
        cohort_idx = idx % 3
        await crud.add_agent_to_cohort(db, cohort_records[cohort_idx].id, agent.id)

    # Synthetic environments
    env_records: list[models.SyntheticEnvironment] = []
    for env in SYNTHETIC_ENVIRONMENTS:
        rec = await crud.create_synthetic_environment(
            db,
            schemas.SyntheticEnvironmentCreate(
                name=env["name"],
                task_script_json=env["task"],
                synthetic_patient_cohort=env["patients"],
                golden_path_steps=env["golden"],
                perturbation_set=env["perturbations"],
            ),
        )
        env_records.append(rec)

    # Agent runs and metrics
    for idx, agent in enumerate(agent_records[:5]):
        env = env_records[idx % 3]
        run = await crud.create_agent_run(db, schemas.AgentRunCreate(environment_id=env.id, agent_subject_ids=[agent.id]))
        metrics = {
            "task_success": 0.9 - (idx * 0.05),
            "path_optimality": 0.85,
            "unsafe_action_rate": 0.1 if idx != 2 else 0.6,
            "permission_breach_rate": 0.05,
            "consent_breach_rate": 0.02 if idx != 3 else 0.25,
            "human_handoff_rate": 0.2 if idx == 4 else 0.05,
            "mean_steps_vs_golden": 0.95,
        }
        await crud.complete_agent_run(db, run, metrics, trace_url=f"https://traces.ctms/run/{run.id}")

    # Consent contracts for first 3 agents
    for agent in agent_records[:3]:
        await crud.create_agent_consent_contract(
            db,
            schemas.AgentConsentContractCreate(
                agent_subject_id=agent.id,
                allowed_systems=["ctms", "global-agent-registry"],
                model_owner_consent=True,
                withdrawal_mechanism="Revoke via registry portal",
            ),
        )

    # Bias reports
    await crud.create_agent_bias_report(
        db,
        schemas.AgentBiasReportCreate(
            cohort_id=cohort_records[0].id,
            demographic_strata={"age": ["<65", ">=65"], "sex": ["M", "F"]},
            metric_disparities={"task_success": {"<65": 0.9, ">=65": 0.75}},
            drift_flags=["model_drift_q2"],
            reviewer_notes="Review age disparity",
        ),
    )
    await db.commit()
