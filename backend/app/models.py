"""SQLAlchemy domain models for CTMS."""

from __future__ import annotations

import datetime as dt
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StudyStatus(str, PyEnum):
    draft = "draft"
    approved = "approved"
    recruiting = "recruiting"
    active = "active"
    suspended = "suspended"
    completed = "completed"
    closed = "closed"


class SiteActivationStatus(str, PyEnum):
    pending = "pending"
    activated = "activated"
    suspended = "suspended"
    closed = "closed"


class EnrolmentStatus(str, PyEnum):
    screening = "screening"
    enrolled = "enrolled"
    completed = "completed"
    early_terminated = "early_terminated"
    withdrawn = "withdrawn"


class VisitStatus(str, PyEnum):
    scheduled = "scheduled"
    completed = "completed"
    missed = "missed"
    early_terminated = "early_terminated"


class AESeriousness(str, PyEnum):
    non_serious = "non_serious"
    serious = "serious"
    life_threatening = "life_threatening"
    fatal = "fatal"


class AEStatus(str, PyEnum):
    reported = "reported"
    assessed = "assessed"
    submitted = "submitted"
    closed = "closed"


class DocumentType(str, PyEnum):
    protocol = "protocol"
    ibc = "ibc"
    ethics_approval = "ethics_approval"
    dsmb = "dsmb"
    insurance = "insurance"
    investigator_brochure = "investigator_brochure"


class QueryStatus(str, PyEnum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    cancelled = "cancelled"


class AgentAutonomy(str, PyEnum):
    shadow = "shadow"
    advisory = "advisory"
    auto_with_threshold_hitl = "auto_with_threshold_hitl"


class AgentRegistrationSource(str, PyEnum):
    global_agent_registry = "global_agent_registry"
    nexus_a2a_protocol = "nexus_a2a_protocol"
    direct = "direct"


class AgentAttestationType(str, PyEnum):
    clinical_safety = "clinical_safety"
    model_card = "model_card"
    bias_audit = "bias_audit"
    security_review = "security_review"


class CohortType(str, PyEnum):
    single_agent = "single_agent"
    multi_agent = "multi_agent"
    human_ai_mixed = "human_ai_mixed"


class Study(Base):
    __tablename__ = "studies"

    id: Mapped[int] = mapped_column(primary_key=True)
    protocol_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    phase: Mapped[str] = mapped_column(String(16))
    indication: Mapped[str] = mapped_column(String(128))
    therapeutic_area: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default=StudyStatus.draft.value)
    sponsor: Mapped[str] = mapped_column(String(128))
    planned_sites: Mapped[int] = mapped_column(default=0)
    planned_subjects: Mapped[int] = mapped_column(default=0)
    start_date: Mapped[dt.date | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[dt.date | None] = mapped_column(DateTime, nullable=True)
    fhir_research_study_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    protocol_versions: Mapped[list["ProtocolVersion"]] = relationship(back_populates="study", lazy="selectin")
    sites: Mapped[list["Site"]] = relationship(back_populates="study", lazy="selectin")
    subjects: Mapped[list["Subject"]] = relationship(back_populates="study", lazy="selectin")
    adverse_events: Mapped[list["AdverseEvent"]] = relationship(back_populates="study", lazy="selectin")


class ProtocolVersion(Base):
    __tablename__ = "protocol_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"))
    version_number: Mapped[str] = mapped_column(String(16))
    approval_date: Mapped[dt.date | None] = mapped_column(DateTime, nullable=True)
    effective_date: Mapped[dt.date | None] = mapped_column(DateTime, nullable=True)
    amendment_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_document_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    study: Mapped["Study"] = relationship(back_populates="protocol_versions")


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"), index=True)
    site_code: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(255))
    organisation_id: Mapped[str] = mapped_column(String(64))
    principal_investigator_id: Mapped[str] = mapped_column(String(64))
    activation_status: Mapped[str] = mapped_column(String(16), default=SiteActivationStatus.pending.value)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    capacity: Mapped[int] = mapped_column(default=0)

    study: Mapped["Study"] = relationship(back_populates="sites")
    subjects: Mapped[list["Subject"]] = relationship(back_populates="site", lazy="selectin")

    __table_args__ = (Index("ix_sites_study_code", "study_id", "site_code", unique=True),)


class SiteActivationChecklist(Base):
    __tablename__ = "site_activation_checklists"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"))
    task_name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    evidence_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"), index=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True)
    subject_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    screening_id: Mapped[str] = mapped_column(String(32))
    enrolment_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    enrolment_status: Mapped[str] = mapped_column(String(16), default=EnrolmentStatus.screening.value)
    consent_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    consent_date: Mapped[dt.date | None] = mapped_column(DateTime, nullable=True)
    randomisation_arm: Mapped[str | None] = mapped_column(String(32), nullable=True)
    stratification_factors: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    demographics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    study: Mapped["Study"] = relationship(back_populates="subjects")
    site: Mapped["Site"] = relationship(back_populates="subjects")
    visits: Mapped[list["SubjectVisit"]] = relationship(back_populates="subject", lazy="selectin")


class InformedConsent(Base):
    __tablename__ = "informed_consents"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    consent_version: Mapped[str] = mapped_column(String(16))
    consent_date: Mapped[dt.datetime] = mapped_column(DateTime)
    withdrawn_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    withdrawal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)


class SubjectVisit(Base):
    __tablename__ = "subject_visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    visit_definition_id: Mapped[str] = mapped_column(String(64))
    scheduled_date: Mapped[dt.date] = mapped_column(DateTime)
    actual_date: Mapped[dt.date | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default=VisitStatus.scheduled.value)
    window_min_date: Mapped[dt.date] = mapped_column(DateTime)
    window_max_date: Mapped[dt.date] = mapped_column(DateTime)
    fhir_encounter_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    assessments: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    monitoring_status: Mapped[str | None] = mapped_column(String(16), nullable=True)

    subject: Mapped["Subject"] = relationship(back_populates="visits")


class AdverseEvent(Base):
    __tablename__ = "adverse_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    onset_date: Mapped[dt.date] = mapped_column(DateTime)
    severity: Mapped[str] = mapped_column(String(32))
    seriousness: Mapped[str] = mapped_column(String(32))
    causality: Mapped[str] = mapped_column(String(32))
    outcome: Mapped[str | None] = mapped_column(String(64), nullable=True)
    susar_flag: Mapped[bool] = mapped_column(default=False)
    regulatory_report_deadline: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default=AEStatus.reported.value)
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    submission_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)

    study: Mapped["Study"] = relationship(back_populates="adverse_events")


class ProtocolDeviation(Base):
    __tablename__ = "protocol_deviations"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"))
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subjects.id"), nullable=True)
    category: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(32))
    reported_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)


class InvestigationalProduct(Base):
    __tablename__ = "investigational_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    lot_number: Mapped[str] = mapped_column(String(64))
    expiry_date: Mapped[dt.date] = mapped_column(DateTime)
    storage_conditions: Mapped[str] = mapped_column(String(64))
    accountability_unit: Mapped[str] = mapped_column(String(32))
    quantity_on_hand: Mapped[int] = mapped_column(default=0)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"), nullable=True)


class IpShipment(Base):
    __tablename__ = "ip_shipments"

    id: Mapped[int] = mapped_column(primary_key=True)
    shipment_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("investigational_products.id"))
    from_organisation: Mapped[str] = mapped_column(String(128))
    to_site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"))
    quantity_shipped: Mapped[int] = mapped_column(default=0)
    received_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    received_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    condition_ok: Mapped[bool | None] = mapped_column(default=None)


class IpDispense(Base):
    __tablename__ = "ip_dispenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    visit_id: Mapped[int | None] = mapped_column(ForeignKey("subject_visits.id"), nullable=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("investigational_products.id"))
    quantity_dispensed: Mapped[int] = mapped_column(default=0)
    quantity_returned: Mapped[int] = mapped_column(default=0)
    destroyed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    destroyed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)


class Query(Base):
    __tablename__ = "queries"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"))
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subjects.id"), nullable=True)
    raised_by: Mapped[str] = mapped_column(String(128))
    assigned_to: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default=QueryStatus.open.value)
    due_date: Mapped[dt.date | None] = mapped_column(DateTime, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    linked_resource: Mapped[str | None] = mapped_column(String(255), nullable=True)


class RegulatoryDocument(Base):
    __tablename__ = "regulatory_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"))
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"), nullable=True)
    document_type: Mapped[str] = mapped_column(String(32))
    document_reference: Mapped[str] = mapped_column(String(255))
    expiry_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    version: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="active")


class StudyBudget(Base):
    __tablename__ = "study_budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"))
    budget_category: Mapped[str] = mapped_column(String(64))
    planned_amount: Mapped[float] = mapped_column(default=0.0)
    actual_amount: Mapped[float] = mapped_column(default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"))
    sponsor_id: Mapped[str] = mapped_column(String(64))
    amount: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    due_date: Mapped[dt.date | None] = mapped_column(DateTime, nullable=True)
    linked_items: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_id: Mapped[int | None] = mapped_column(ForeignKey("studies.id"), nullable=True)
    actor_id: Mapped[str] = mapped_column(String(128))
    purpose_of_use: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(128))
    resource_type: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[int | None] = mapped_column(nullable=True)
    previous_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entry_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())


class AgentSubject(Base):
    __tablename__ = "agent_subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    principal_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    persona_key: Mapped[str] = mapped_column(String(128))
    superpersona_contract_id: Mapped[str] = mapped_column(String(128))
    model_version: Mapped[str] = mapped_column(String(64))
    agent_owner_id: Mapped[str] = mapped_column(String(128))
    autonomy_level: Mapped[str] = mapped_column(String(32), default=AgentAutonomy.shadow.value)
    safety_class: Mapped[str] = mapped_column(String(32))
    attestation_status: Mapped[str] = mapped_column(String(16), default="pending")
    registration_source: Mapped[str] = mapped_column(String(32), default=AgentRegistrationSource.direct.value)
    enrolled_study_id: Mapped[int | None] = mapped_column(ForeignKey("studies.id"), nullable=True)


class AgentCohort(Base):
    __tablename__ = "agent_cohorts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    cohort_type: Mapped[str] = mapped_column(String(32))
    capability_profile: Mapped[str] = mapped_column(String(128))
    model_family: Mapped[str] = mapped_column(String(64))
    evaluation_objective: Mapped[str] = mapped_column(Text)


class AgentCohortMembership(Base):
    __tablename__ = "agent_cohort_memberships"

    id: Mapped[int] = mapped_column(primary_key=True)
    cohort_id: Mapped[int] = mapped_column(ForeignKey("agent_cohorts.id"))
    agent_subject_id: Mapped[int] = mapped_column(ForeignKey("agent_subjects.id"))


class SyntheticEnvironment(Base):
    __tablename__ = "synthetic_environments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    task_script_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    synthetic_patient_cohort: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    golden_path_steps: Mapped[list[str]] = mapped_column(JSON)
    perturbation_set: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    reset_token: Mapped[str] = mapped_column(String(64))
    reproducibility_hash: Mapped[str] = mapped_column(String(64), index=True)


class AgentTrialArm(Base):
    __tablename__ = "agent_trial_arms"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_subject_id: Mapped[int] = mapped_column(ForeignKey("agent_subjects.id"))
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"))
    randomisation_arm: Mapped[str | None] = mapped_column(String(32), nullable=True)
    stratification_factors: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    consent_contract_version: Mapped[str | None] = mapped_column(String(16), nullable=True)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    environment_id: Mapped[int] = mapped_column(ForeignKey("synthetic_environments.id"))
    agent_subject_ids: Mapped[list[int]] = mapped_column(JSON)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    metrics_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    trace_artifact_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reproducibility_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)


class AgentMetric(Base):
    __tablename__ = "agent_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("agent_runs.id"))
    agent_subject_id: Mapped[int | None] = mapped_column(ForeignKey("agent_subjects.id"), nullable=True)
    metric_name: Mapped[str] = mapped_column(String(64))
    value: Mapped[float] = mapped_column(default=0.0)
    threshold: Mapped[float | None] = mapped_column(nullable=True)
    pass_flag: Mapped[bool | None] = mapped_column(default=None)


class AgentAttestation(Base):
    __tablename__ = "agent_attestations"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_subject_id: Mapped[int] = mapped_column(ForeignKey("agent_subjects.id"))
    attestation_type: Mapped[str] = mapped_column(String(32))
    issuer: Mapped[str] = mapped_column(String(255))
    signature: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime)
    claims_json: Mapped[dict[str, Any]] = mapped_column(JSON)


class AgentConsentContract(Base):
    __tablename__ = "agent_consent_contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_subject_id: Mapped[int] = mapped_column(ForeignKey("agent_subjects.id"), unique=True)
    purpose_of_use: Mapped[str] = mapped_column(String(64), default="research")
    allowed_systems: Mapped[list[str]] = mapped_column(JSON)
    data_retention_days: Mapped[int] = mapped_column(default=2555)
    model_owner_consent: Mapped[bool] = mapped_column(default=False)
    human_oversight_required: Mapped[bool] = mapped_column(default=True)
    withdrawal_mechanism: Mapped[str] = mapped_column(Text)


class AgentBiasReport(Base):
    __tablename__ = "agent_bias_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    cohort_id: Mapped[int] = mapped_column(ForeignKey("agent_cohorts.id"))
    demographic_strata: Mapped[dict[str, Any]] = mapped_column(JSON)
    metric_disparities: Mapped[dict[str, Any]] = mapped_column(JSON)
    drift_flags: Mapped[list[str]] = mapped_column(JSON)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
