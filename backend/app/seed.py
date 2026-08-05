"""Canonical CTMS seeder.

Located at ``backend/app/seed.py`` deliberately: it is one of caid-agent's
ranked ``discover_seed`` candidates, so the Seeding Alignment Gate measures
the file the application actually imports. There is NO duplicate copy --
``app.seeding.loader`` re-exports from here, it does not restate the data
(the estate's stale-duplicate class of defect is exactly what that avoids).

Seed blocks carry ``# CAID-SEED-REQ:`` annotations IMMEDIATELY above the
constructor they describe; the gate's annotation walker only sees the
comment block directly above the call.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.database import async_session

# Imported by name, not reached through ``models.``: caid-agent's Seeding
# Alignment Gate matches a BARE ``ClassName(`` constructor, so
# ``db.add(models.InformedConsent(...))`` is invisible to it and the seeder
# parses as zero seed records. See docs/NATIONAL_CAPABILITY_DISPOSITION_LEDGER.md
# section 8.
from app.models import (
    EligibilityScreening,
    InformedConsent,
    InvestigatorDelegation,
    ParticipantReimbursement,
    RegulatoryApproval,
    SubjectVisit,
    TrialRegistration,
)
from app.seeding.data import (
    ADVERSE_EVENTS,
    AGENT_COHORTS,
    AGENT_SUBJECTS,
    BUDGETS,
    DELEGATIONS,
    ELIGIBILITY_SCREENINGS,
    PRODUCTS,
    PROTOCOL_DEVIATIONS,
    QUERIES,
    REGULATORY_APPROVALS,
    REGULATORY_DOCUMENTS,
    REIMBURSEMENTS,
    SITES,
    STUDIES,
    SUBJECT_TEMPLATES,
    SYNTHETIC_ENVIRONMENTS,
    TRIAL_REGISTRATIONS,
)


async def _already_seeded(db: AsyncSession) -> bool:  # pragma: no cover
    result = await db.execute(select(models.Study).limit(1))
    return result.scalar_one_or_none() is not None


async def seed_database() -> None:  # pragma: no cover
    async with async_session() as db:
        if await _already_seeded(db):
            return
        await seed_all(db)
        await db.commit()


async def seed_all(db: AsyncSession) -> None:
    """Populate a fresh database with the full CTMS demonstration cohort."""

    # Studies
    study_records: list[models.Study] = []
    for s in STUDIES:
        # CAID-SEED-REQ: FR-C-11, FR-C-12, FR-C-111
        study = await crud.create_study(db, schemas.StudyCreate(**s))
        study_records.append(study)

    # Sites
    site_records: list[models.Site] = []
    for site_data in SITES:
        study = study_records[site_data["study_index"]]
        # CAID-SEED-REQ: FR-C-21, FR-C-22
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
        # CAID-SEED-REQ: FR-C-31, FR-C-32
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
            # FR-C-143/FR-C-144: the consent posture every downstream guard
            # reads. Withdrawn subjects must land in ``withdrawn`` here or
            # the IP-dispensing guard would not see the withdrawal at all.
            subject.consent_state = (
                models.ConsentState.withdrawn.value
                if tmpl["status"] == models.EnrolmentStatus.withdrawn.value
                else models.ConsentState.active.value
            )
            if tmpl["status"] == models.EnrolmentStatus.withdrawn.value:
                subject.consent_withdrawn_at = dt.datetime(2026, 5, 2, 11, 0, 0)
            # CAID-SEED-REQ: FR-C-32, FR-C-34, FR-C-141
            db.add(
                InformedConsent(
                    subject_id=subject.id,
                    consent_version=tmpl["consent"],
                    consent_date=dt.datetime(2026, 1, 20, 9, 0, 0),
                    document_reference=f"consent_{tmpl['screening_id']}.pdf",
                    consent_type=models.ConsentType.initial.value,
                    protocol_version=tmpl["consent"],
                    given_by=tmpl.get("consent_given_by", "subject"),
                    jurisdiction=STUDIES[tmpl["study_index"]].get("jurisdiction", "IE"),
                    withdrawn_at=(
                        dt.datetime(2026, 5, 2, 11, 0, 0)
                        if tmpl["status"] == models.EnrolmentStatus.withdrawn.value
                        else None
                    ),
                    withdrawal_reason=(
                        "participant withdrew consent"
                        if tmpl["status"] == models.EnrolmentStatus.withdrawn.value
                        else None
                    ),
                    withdrawal_scope=(
                        "full"
                        if tmpl["status"] == models.EnrolmentStatus.withdrawn.value
                        else None
                    ),
                )
            )
        subject_records.append(subject)
    await db.commit()

    # Visits for enrolled subjects
    visit_date = dt.date(2026, 4, 1)
    for subject in subject_records:
        if subject.enrolment_status == models.EnrolmentStatus.enrolled.value:
            # CAID-SEED-REQ: FR-C-41, FR-C-42
            db.add(
                SubjectVisit(
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
        # CAID-SEED-REQ: FR-C-61, FR-C-62, FR-C-161
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
                expectedness=ae.get("expectedness", "expected"),
            ),
        )

    # Protocol deviations
    for pd in PROTOCOL_DEVIATIONS:
        # CAID-SEED-REQ: FR-C-43, FR-C-94
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
        site = next(
            (
                s
                for s in site_records
                if s.site_code == p["site_code"]
                and s.study_id == study_records[p["site_study"]].id
            ),
            None,
        )
        # CAID-SEED-REQ: FR-C-71, FR-C-72, FR-C-171
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
        # CAID-SEED-REQ: FR-C-51, FR-C-52, FR-C-53
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
        # CAID-SEED-REQ: FR-C-44, FR-C-93
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
        # CAID-SEED-REQ: FR-C-81, FR-C-82, FR-C-83
        await crud.create_study_budget(
            db,
            schemas.StudyBudgetCreate(
                study_id=study_records[b["study_index"]].id,
                budget_category=b["category"],
                planned_amount=b["planned"],
            ),
        )
        budget = (
            await db.execute(
                select(models.StudyBudget).order_by(models.StudyBudget.id.desc()).limit(1)
            )
        ).scalar_one()
        budget.actual_amount = b["actual"]
    await db.commit()

    await seed_national_records(db, study_records, site_records, subject_records)
    await seed_agentic_records(db, study_records)


async def seed_national_records(
    db: AsyncSession,
    study_records: list[models.Study],
    site_records: list[models.Site],
    subject_records: list[models.Subject],
) -> None:
    """National-capability records (FR-C-111..FR-C-192)."""

    # Public trial registry entries, one per study, at three different points
    # of the closed loop: registered (receipted), submitted (awaiting a
    # receipt) and rejected. A registry corpus where everything is already
    # 'registered' cannot exercise the acknowledgement path at all.
    for reg in TRIAL_REGISTRATIONS:
        study = study_records[reg["study_index"]]
        # CAID-SEED-REQ: FR-C-111, FR-C-112
        db.add(
            TrialRegistration(
                study_id=study.id,
                jurisdiction=reg["jurisdiction"],
                registry_code=reg["registry_code"],
                registry_identifier=reg["registry_identifier"],
                status=reg["status"],
                submitted_at=reg["submitted_at"],
                acknowledged_at=reg["acknowledged_at"],
                receipt_reference=reg["receipt_reference"],
                rejection_reason=reg["rejection_reason"],
                public_disclosure_url=reg["public_disclosure_url"],
                correlation_id=f"ctms-trial-registration-seed-{reg['study_index']}",
            )
        )

    # Site delegation log. One entry deliberately carries EXPIRED GCP
    # training so the site-readiness block is reachable from seed alone.
    for dg in DELEGATIONS:
        site = site_records[dg["site_index"]]
        # CAID-SEED-REQ: FR-C-113, FR-C-114
        db.add(
            InvestigatorDelegation(
                site_id=site.id,
                person_id=dg["person_id"],
                person_name=dg["person_name"],
                role=dg["role"],
                delegated_tasks=dg["delegated_tasks"],
                delegated_by=dg["delegated_by"],
                gcp_training_date=dg["gcp_training_date"],
                gcp_training_expiry=dg["gcp_training_expiry"],
                professional_registration=dg["professional_registration"],
                start_date=dg["start_date"],
                status=dg["status"],
            )
        )

    # Ethics / competent-authority submissions and decisions. Every approved
    # row carries a NAMED decider -- nothing auto-approves.
    for ap in REGULATORY_APPROVALS:
        study = study_records[ap["study_index"]]
        # CAID-SEED-REQ: FR-C-121, FR-C-122, FR-C-123
        db.add(
            RegulatoryApproval(
                study_id=study.id,
                jurisdiction=ap["jurisdiction"],
                authority_code=ap["authority_code"],
                authority_kind=ap["authority_kind"],
                submission_type=ap["submission_type"],
                submission_reference=ap["submission_reference"],
                submitted_at=ap["submitted_at"],
                decision=ap["decision"],
                decision_at=ap["decision_at"],
                decided_by=ap["decided_by"],
                conditions=ap["conditions"],
                approval_expiry=ap["approval_expiry"],
                next_report_due=ap["next_report_due"],
                protocol_version=ap["protocol_version"],
            )
        )

    # Hub-mediated eligibility pre-screens covering all three outcomes.
    for el in ELIGIBILITY_SCREENINGS:
        study = study_records[el["study_index"]]
        # CAID-SEED-REQ: FR-C-131, FR-C-132
        db.add(
            EligibilityScreening(
                study_id=study.id,
                site_id=site_records[el["site_index"]].id,
                candidate_reference=el["candidate_reference"],
                consent_basis=el["consent_basis"],
                requested_by=el["requested_by"],
                criteria_requested=el["criteria_requested"],
                criteria_evaluated=el["criteria_evaluated"],
                outcome=el["outcome"],
                outcome_at=el["outcome_at"],
                reviewed_by=el["reviewed_by"],
                source_system=el["source_system"],
                correlation_id=el["correlation_id"],
            )
        )

    # Participant expense / inconvenience payments.
    for rb in REIMBURSEMENTS:
        subject = subject_records[rb["subject_index"]]
        # CAID-SEED-REQ: FR-C-182, FR-C-183
        db.add(
            ParticipantReimbursement(
                subject_id=subject.id,
                category=rb["category"],
                amount=rb["amount"],
                currency=rb["currency"],
                status=rb["status"],
                approved_by=rb["approved_by"],
                exceeds_guidance_cap=rb["exceeds_guidance_cap"],
                notes=rb["notes"],
            )
        )
    await db.commit()

    # Randomisation allocation lists for the studies that have randomised
    # subjects, and BINDING of the historically-seeded arms to real slots.
    # Without the binding a seeded subject would carry an arm that no
    # allocation ever assigned -- exactly the state FR-C-154 refuses to
    # unblind, because such an arm cannot be reconciled to an allocation list.
    for study in study_records[:2]:
        allocations = await crud.ensure_allocation_list(db, study, "default")
        by_arm: dict[str, list[models.RandomisationAllocation]] = {}
        for allocation in allocations:
            by_arm.setdefault(allocation.arm_code, []).append(allocation)
        for subject in subject_records:
            if subject.study_id != study.id or not subject.randomisation_arm:
                continue
            pool = by_arm.get(subject.randomisation_arm)
            if not pool:  # pragma: no cover - the seeded arms fit the list
                # Defensive: the seeded cohort has exactly 16 armed subjects
                # per study against 32 slots, so no arm pool runs dry today.
                # Kept so growing the cohort degrades to "unallocated" rather
                # than raising during boot.
                continue
            allocation = pool.pop(0)
            allocation.allocated_subject_id = subject.id
            allocation.allocated_at = dt.datetime(2026, 1, 20, 9, 30, 0)
            allocation.allocated_by = "seed"
            subject.kit_code = allocation.kit_code
    await db.commit()


async def seed_agentic_records(db: AsyncSession, study_records: list[models.Study]) -> None:
    """Agentic-research records (FR-C-A11..A45)."""

    agent_records: list[models.AgentSubject] = []
    for agent in AGENT_SUBJECTS:
        # CAID-SEED-REQ: FR-C-A11, FR-C-A12
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

    cohort_records: list[models.AgentCohort] = []
    for cohort in AGENT_COHORTS:
        # CAID-SEED-REQ: FR-C-A13
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

    for idx, agent in enumerate(agent_records):
        cohort_idx = idx % 3
        await crud.add_agent_to_cohort(db, cohort_records[cohort_idx].id, agent.id)

    env_records: list[models.SyntheticEnvironment] = []
    for env in SYNTHETIC_ENVIRONMENTS:
        # CAID-SEED-REQ: FR-C-A21
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

    for idx, agent in enumerate(agent_records[:5]):
        env = env_records[idx % 3]
        # CAID-SEED-REQ: FR-C-A22, FR-C-A23
        run = await crud.create_agent_run(
            db, schemas.AgentRunCreate(environment_id=env.id, agent_subject_ids=[agent.id])
        )
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

    for agent in agent_records[:3]:
        # CAID-SEED-REQ: FR-C-A12, FR-C-A15
        await crud.create_agent_consent_contract(
            db,
            schemas.AgentConsentContractCreate(
                agent_subject_id=agent.id,
                allowed_systems=["ctms", "global-agent-registry"],
                model_owner_consent=True,
                withdrawal_mechanism="Revoke via registry portal",
            ),
        )

    # CAID-SEED-REQ: FR-C-A41
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
