"""Pydantic v2 schemas for CTMS."""

from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Studies
class StudyCreate(BaseSchema):
    protocol_number: str
    title: str
    phase: str
    indication: str
    therapeutic_area: str
    sponsor: str
    jurisdiction: str = "IE"
    sponsor_organisation_id: str | None = None
    planned_sites: int = 0
    planned_subjects: int = 0
    start_date: dt.date | None = None
    end_date: dt.date | None = None
    fhir_research_study_json: dict[str, Any] | None = None


class StudyUpdate(BaseSchema):
    title: str | None = None
    status: str | None = None
    start_date: dt.date | None = None
    end_date: dt.date | None = None
    fhir_research_study_json: dict[str, Any] | None = None


class StudyOut(BaseSchema):
    id: int
    protocol_number: str
    title: str
    phase: str
    indication: str
    therapeutic_area: str
    status: str
    sponsor: str
    jurisdiction: str
    sponsor_organisation_id: str | None
    planned_sites: int
    planned_subjects: int
    start_date: dt.date | None
    end_date: dt.date | None
    created_at: dt.datetime
    updated_at: dt.datetime


# Protocol versions
class ProtocolVersionCreate(BaseSchema):
    study_id: int
    version_number: str
    approval_date: dt.date | None = None
    effective_date: dt.date | None = None
    amendment_reason: str | None = None
    pdf_document_reference: str | None = None


class ProtocolVersionOut(BaseSchema):
    id: int
    study_id: int
    version_number: str
    approval_date: dt.date | None
    effective_date: dt.date | None
    amendment_reason: str | None
    pdf_document_reference: str | None


# Sites
class SiteCreate(BaseSchema):
    study_id: int
    site_code: str
    name: str
    organisation_id: str
    principal_investigator_id: str
    address: str | None = None
    capacity: int = 0


class SiteUpdate(BaseSchema):
    name: str | None = None
    activation_status: str | None = None
    principal_investigator_id: str | None = None
    capacity: int | None = None


class SiteOut(BaseSchema):
    id: int
    study_id: int
    site_code: str
    name: str
    organisation_id: str
    principal_investigator_id: str
    activation_status: str
    address: str | None
    capacity: int


class SiteActivationChecklistOut(BaseSchema):
    id: int
    site_id: int
    task_name: str
    status: str
    evidence_reference: str | None


# Subjects
class SubjectCreate(BaseSchema):
    study_id: int
    site_id: int
    screening_id: str
    demographics: dict[str, Any] | None = None


class SubjectUpdate(BaseSchema):
    enrolment_status: str | None = None
    consent_version: str | None = None
    consent_date: dt.date | None = None
    randomisation_arm: str | None = None
    stratification_factors: dict[str, Any] | None = None


class SubjectOut(BaseSchema):
    id: int
    study_id: int
    site_id: int
    subject_number: str
    screening_id: str
    enrolment_id: str | None
    enrolment_status: str
    consent_version: str | None
    consent_date: dt.date | None
    randomisation_arm: str | None
    stratification_factors: dict[str, Any] | None
    demographics: dict[str, Any] | None
    consent_state: str
    consent_withdrawn_at: dt.datetime | None
    kit_code: str | None


class InformedConsentCreate(BaseSchema):
    subject_id: int
    consent_version: str
    consent_date: dt.datetime
    document_reference: str | None = None
    consent_type: str = "initial"
    protocol_version: str | None = None
    given_by: str = "subject"
    witnessed_by: str | None = None
    future_use_opt_in: bool = False


class InformedConsentOut(BaseSchema):
    id: int
    subject_id: int
    consent_version: str
    consent_date: dt.datetime
    withdrawn_at: dt.datetime | None
    withdrawal_reason: str | None
    document_reference: str | None
    consent_type: str
    protocol_version: str | None
    given_by: str
    witnessed_by: str | None
    future_use_opt_in: bool
    withdrawal_scope: str | None
    jurisdiction: str


class RandomiseSubject(BaseSchema):
    stratification_factors: dict[str, Any] | None = None
    randomised_by: str | None = None


# Visits
class SubjectVisitCreate(BaseSchema):
    subject_id: int
    visit_definition_id: str
    scheduled_date: dt.date
    window_min_date: dt.date
    window_max_date: dt.date
    fhir_encounter_json: dict[str, Any] | None = None


class SubjectVisitUpdate(BaseSchema):
    actual_date: dt.date | None = None
    status: str | None = None
    assessments: dict[str, Any] | None = None
    monitoring_status: str | None = None
    fhir_encounter_json: dict[str, Any] | None = None


class SubjectVisitOut(BaseSchema):
    id: int
    subject_id: int
    visit_definition_id: str
    scheduled_date: dt.date
    actual_date: dt.date | None
    status: str
    window_min_date: dt.date
    window_max_date: dt.date
    fhir_encounter_json: dict[str, Any] | None
    assessments: dict[str, Any] | None
    monitoring_status: str | None


# Adverse events
class AdverseEventCreate(BaseSchema):
    study_id: int
    subject_id: int
    onset_date: dt.date
    severity: str
    seriousness: str
    causality: str
    outcome: str | None = None
    susar_flag: bool = False
    narrative: str | None = None
    expectedness: str = "expected"


class AdverseEventUpdate(BaseSchema):
    severity: str | None = None
    seriousness: str | None = None
    causality: str | None = None
    outcome: str | None = None
    susar_flag: bool | None = None
    narrative: str | None = None
    status: str | None = None
    submission_reference: str | None = None
    expectedness: str | None = None


class AdverseEventOut(BaseSchema):
    id: int
    study_id: int
    subject_id: int
    onset_date: dt.date
    severity: str
    seriousness: str
    causality: str
    outcome: str | None
    susar_flag: bool
    regulatory_report_deadline: dt.datetime | None
    status: str
    narrative: str | None
    submission_reference: str | None
    expectedness: str
    jurisdiction: str
    deadline_basis: str | None


# Protocol deviations
class ProtocolDeviationCreate(BaseSchema):
    study_id: int
    subject_id: int | None = None
    category: str
    description: str
    severity: str
    corrective_action: str | None = None


class ProtocolDeviationOut(BaseSchema):
    id: int
    study_id: int
    subject_id: int | None
    category: str
    description: str
    severity: str
    reported_at: dt.datetime
    corrective_action: str | None


# Investigational product
class InvestigationalProductCreate(BaseSchema):
    sku: str
    name: str
    lot_number: str
    expiry_date: dt.date
    storage_conditions: str
    accountability_unit: str
    quantity_on_hand: int = 0
    site_id: int | None = None


class InvestigationalProductOut(BaseSchema):
    id: int
    sku: str
    name: str
    lot_number: str
    expiry_date: dt.date
    storage_conditions: str
    accountability_unit: str
    quantity_on_hand: int
    site_id: int | None


class IpShipmentCreate(BaseSchema):
    shipment_id: str
    product_id: int
    from_organisation: str
    to_site_id: int
    quantity_shipped: int
    received_at: dt.datetime | None = None
    received_by: str | None = None
    condition_ok: bool | None = None


class IpShipmentOut(BaseSchema):
    id: int
    shipment_id: str
    product_id: int
    from_organisation: str
    to_site_id: int
    quantity_shipped: int
    received_at: dt.datetime | None
    received_by: str | None
    condition_ok: bool | None


class IpDispenseCreate(BaseSchema):
    subject_id: int
    visit_id: int | None = None
    product_id: int
    quantity_dispensed: int
    quantity_returned: int = 0
    dispensed_by: str | None = None


class IpDispenseOut(BaseSchema):
    id: int
    subject_id: int
    visit_id: int | None
    product_id: int
    quantity_dispensed: int
    quantity_returned: int
    dispensed_by: str | None
    destroyed_at: dt.datetime | None
    destroyed_by: str | None


class IpDestroy(BaseSchema):
    destroyed_at: dt.datetime
    destroyed_by: str


# Regulatory documents
class RegulatoryDocumentCreate(BaseSchema):
    study_id: int
    site_id: int | None = None
    document_type: str
    document_reference: str
    expiry_date: dt.date | None = None
    version: str


class RegulatoryDocumentOut(BaseSchema):
    id: int
    study_id: int
    site_id: int | None
    document_type: str
    document_reference: str
    expiry_date: dt.date | None
    version: str
    status: str


# Queries
class QueryCreate(BaseSchema):
    study_id: int
    subject_id: int | None = None
    raised_by: str
    assigned_to: str | None = None
    due_date: dt.date | None = None
    description: str | None = None
    linked_resource: str | None = None


class QueryUpdate(BaseSchema):
    assigned_to: str | None = None
    status: str | None = None
    resolution: str | None = None


class QueryOut(BaseSchema):
    id: int
    study_id: int
    subject_id: int | None
    raised_by: str
    description: str | None
    assigned_to: str | None
    status: str
    due_date: dt.date | None
    resolution: str | None
    linked_resource: str | None


# Budget and invoices
class StudyBudgetCreate(BaseSchema):
    study_id: int
    budget_category: str
    planned_amount: float
    currency: str = "USD"


class StudyBudgetUpdate(BaseSchema):
    actual_amount: float | None = None


class StudyBudgetOut(BaseSchema):
    id: int
    study_id: int
    budget_category: str
    planned_amount: float
    actual_amount: float
    currency: str


class InvoiceCreate(BaseSchema):
    study_id: int
    sponsor_id: str
    amount: float
    due_date: dt.date | None = None
    linked_items: list[dict[str, Any]] | None = None


class InvoiceOut(BaseSchema):
    id: int
    study_id: int
    sponsor_id: str
    amount: float
    status: str
    due_date: dt.date | None
    linked_items: list[dict[str, Any]] | None


# Audit entries
class AuditEntryCreate(BaseSchema):
    study_id: int | None = None
    actor_id: str
    purpose_of_use: str
    action: str
    resource_type: str
    resource_id: int | None = None


class AuditEntryOut(BaseSchema):
    id: int
    study_id: int | None
    actor_id: str
    purpose_of_use: str
    action: str
    resource_type: str
    resource_id: int | None
    previous_hash: str | None
    entry_hash: str
    created_at: dt.datetime


# Agent subjects
class AgentSubjectCreate(BaseSchema):
    principal_id: str
    persona_key: str
    superpersona_contract_id: str
    model_version: str
    agent_owner_id: str
    autonomy_level: str = "shadow"
    safety_class: str
    registration_source: str = "direct"


class AgentSubjectUpdate(BaseSchema):
    autonomy_level: str | None = None
    attestation_status: str | None = None
    enrolled_study_id: int | None = None


class AgentSubjectOut(BaseSchema):
    id: int
    principal_id: str
    persona_key: str
    superpersona_contract_id: str
    model_version: str
    agent_owner_id: str
    autonomy_level: str
    safety_class: str
    attestation_status: str
    registration_source: str
    enrolled_study_id: int | None


class AgentCohortCreate(BaseSchema):
    name: str
    cohort_type: str
    capability_profile: str
    model_family: str
    evaluation_objective: str


class AgentCohortOut(BaseSchema):
    id: int
    name: str
    cohort_type: str
    capability_profile: str
    model_family: str
    evaluation_objective: str


class SyntheticEnvironmentCreate(BaseSchema):
    name: str
    task_script_json: dict[str, Any]
    synthetic_patient_cohort: list[dict[str, Any]]
    golden_path_steps: list[str]
    perturbation_set: list[dict[str, Any]]


class SyntheticEnvironmentOut(BaseSchema):
    id: int
    name: str
    task_script_json: dict[str, Any]
    synthetic_patient_cohort: list[dict[str, Any]]
    golden_path_steps: list[str]
    perturbation_set: list[dict[str, Any]]
    reset_token: str
    reproducibility_hash: str


class AgentTrialArmCreate(BaseSchema):
    agent_subject_id: int
    study_id: int
    randomisation_arm: str | None = None
    stratification_factors: dict[str, Any] | None = None
    consent_contract_version: str | None = None


class AgentTrialArmOut(BaseSchema):
    id: int
    agent_subject_id: int
    study_id: int
    randomisation_arm: str | None
    stratification_factors: dict[str, Any] | None
    consent_contract_version: str | None


class AgentRunCreate(BaseSchema):
    environment_id: int
    agent_subject_ids: list[int]


class AgentRunOut(BaseSchema):
    id: int
    environment_id: int
    agent_subject_ids: list[int]
    started_at: dt.datetime
    completed_at: dt.datetime | None
    metrics_snapshot: dict[str, Any] | None
    trace_artifact_url: str | None
    reproducibility_hash: str | None


class AgentMetricCreate(BaseSchema):
    run_id: int
    metric_name: str
    value: float
    threshold: float | None = None
    pass_flag: bool | None = None
    agent_subject_id: int | None = None


class AgentMetricOut(BaseSchema):
    id: int
    run_id: int
    agent_subject_id: int | None
    metric_name: str
    value: float
    threshold: float | None
    pass_flag: bool | None


class AgentAttestationCreate(BaseSchema):
    agent_subject_id: int
    attestation_type: str
    issuer: str
    signature: str
    expires_at: dt.datetime
    claims_json: dict[str, Any]


class AgentAttestationOut(BaseSchema):
    id: int
    agent_subject_id: int
    attestation_type: str
    issuer: str
    signature: str
    expires_at: dt.datetime
    claims_json: dict[str, Any]


class AgentConsentContractCreate(BaseSchema):
    agent_subject_id: int
    purpose_of_use: str = "research"
    allowed_systems: list[str]
    data_retention_days: int = 2555
    model_owner_consent: bool = False
    human_oversight_required: bool = True
    withdrawal_mechanism: str


class AgentConsentContractOut(BaseSchema):
    id: int
    agent_subject_id: int
    purpose_of_use: str
    allowed_systems: list[str]
    data_retention_days: int
    model_owner_consent: bool
    human_oversight_required: bool
    withdrawal_mechanism: str


class AgentBiasReportCreate(BaseSchema):
    cohort_id: int
    demographic_strata: dict[str, Any]
    metric_disparities: dict[str, Any]
    drift_flags: list[str]
    reviewer_notes: str | None = None


class AgentBiasReportOut(BaseSchema):
    id: int
    cohort_id: int
    demographic_strata: dict[str, Any]
    metric_disparities: dict[str, Any]
    drift_flags: list[str]
    reviewer_notes: str | None


class ReleaseGateResult(BaseSchema):
    cohort_id: int
    status: str
    passed_metrics: list[str]
    failed_metrics: list[dict[str, Any]]


# Webhooks
class WebhookPayload(BaseSchema):
    event: str
    data: dict[str, Any]
    signature: str | None = None


# Reference valuesets
class ValuesetOut(BaseSchema):
    name: str
    values: list[str]


class HealthOut(BaseSchema):
    status: str
    version: str
    timestamp: dt.datetime


# Reports
class RecruitmentReport(BaseSchema):
    study_id: int
    planned: int
    enrolled: int
    screen_failed: int
    withdrawn: int
    by_site: list[dict[str, Any]]


class SafetyReport(BaseSchema):
    study_id: int
    total_aes: int
    by_severity: dict[str, int]
    by_seriousness: dict[str, int]
    pending_susars: int
    days_to_report: list[int]


class ETMFReport(BaseSchema):
    study_id: int
    folders: list[dict[str, Any]]
    expired_count: int


class AccountabilityReport(BaseSchema):
    study_id: int
    site_id: int
    shipped: int
    dispensed: int
    returned: int
    destroyed: int
    on_hand: int


# --- National capability schemas (REQ-CTS-NAT-001..008) ---------------------


class CountryPackOut(BaseSchema):
    code: str
    name: str
    pack_version: str
    effective_from: dt.date
    competent_authority: dict[str, Any]
    ethics_authority: dict[str, Any]
    trial_registry: dict[str, Any]
    safety_reporting: dict[str, Any]
    consent: dict[str, Any]
    site_credentialing: dict[str, Any]
    participant_reimbursement: dict[str, Any]
    sources: list[dict[str, Any]]


class TrialRegistrationCreate(BaseSchema):
    study_id: int
    registry_code: str | None = None
    public_disclosure_url: str | None = None


class TrialRegistrationReceipt(BaseSchema):
    registry_identifier: str
    receipt_reference: str
    accepted: bool = True
    rejection_reason: str | None = None


class TrialRegistrationOut(BaseSchema):
    id: int
    study_id: int
    jurisdiction: str
    registry_code: str
    registry_identifier: str | None
    status: str
    submitted_at: dt.datetime | None
    acknowledged_at: dt.datetime | None
    receipt_reference: str | None
    rejection_reason: str | None
    public_disclosure_url: str | None
    correlation_id: str | None


class InvestigatorDelegationCreate(BaseSchema):
    site_id: int
    person_id: str
    person_name: str
    role: str
    delegated_tasks: list[str]
    delegated_by: str
    gcp_training_date: dt.date
    professional_registration: str | None = None
    start_date: dt.date
    end_date: dt.date | None = None


class InvestigatorDelegationOut(BaseSchema):
    id: int
    site_id: int
    person_id: str
    person_name: str
    role: str
    delegated_tasks: list[str]
    delegated_by: str
    gcp_training_date: dt.date
    gcp_training_expiry: dt.date
    professional_registration: str | None
    start_date: dt.date
    end_date: dt.date | None
    status: str


class SiteReadinessOut(BaseSchema):
    site_id: int
    jurisdiction: str
    checklist_complete: bool
    delegation_log_present: bool
    delegations_active: int
    delegations_expired: int
    ethics_approved: bool
    blocking_reasons: list[str]
    ready_for_activation: bool


class RegulatoryApprovalCreate(BaseSchema):
    study_id: int
    site_id: int | None = None
    authority_kind: str = "ethics"
    submission_type: str = "initial"
    submission_reference: str
    protocol_version: str | None = None


class RegulatoryDecision(BaseSchema):
    decision: str
    decided_by: str
    conditions: list[dict[str, Any]] | None = None
    approval_expiry: dt.date | None = None


class RegulatoryApprovalOut(BaseSchema):
    id: int
    study_id: int
    site_id: int | None
    jurisdiction: str
    authority_code: str
    authority_kind: str
    submission_type: str
    submission_reference: str
    submitted_at: dt.datetime
    decision: str
    decision_at: dt.datetime | None
    decided_by: str | None
    conditions: list[dict[str, Any]] | None
    approval_expiry: dt.date | None
    next_report_due: dt.date | None
    protocol_version: str | None


class EligibilityScreeningCreate(BaseSchema):
    study_id: int
    site_id: int | None = None
    candidate_reference: str
    consent_basis: str
    requested_by: str
    criteria_requested: list[str]


class EligibilityOutcomeIn(BaseSchema):
    criteria_evaluated: dict[str, Any]
    reviewed_by: str | None = None
    source_system: str = "bullettrain-hub"


class EligibilityScreeningOut(BaseSchema):
    id: int
    study_id: int
    site_id: int | None
    subject_id: int | None
    candidate_reference: str
    consent_basis: str
    requested_by: str
    requested_at: dt.datetime
    criteria_requested: list[str]
    criteria_evaluated: dict[str, Any] | None
    outcome: str
    outcome_at: dt.datetime | None
    reviewed_by: str | None
    source_system: str | None
    correlation_id: str | None


class RandomisationAllocationOut(BaseSchema):
    id: int
    study_id: int
    stratum_key: str
    sequence_number: int
    kit_code: str
    block_id: str
    allocated_subject_id: int | None
    allocated_at: dt.datetime | None
    allocated_by: str | None


class RandomisationResult(BaseSchema):
    """Blinded response: the caller receives a kit code, not the arm."""

    subject_id: int
    stratum_key: str
    kit_code: str
    sequence_number: int
    blinded: bool = True


class UnblindingRequest(BaseSchema):
    requested_by: str
    authorised_by: str
    reason: str
    urgency: str = "emergency"


class UnblindingEventOut(BaseSchema):
    id: int
    subject_id: int
    allocation_id: int | None
    requested_by: str
    authorised_by: str
    reason: str
    urgency: str
    arm_revealed: str
    unblinded_at: dt.datetime
    self_authorised: bool


class SafetySubmissionCreate(BaseSchema):
    submitted_by: str
    recipient_code: str | None = None
    submission_reference: str


class SafetyAcknowledgement(BaseSchema):
    acknowledgement_reference: str
    accepted: bool = True
    rejection_reason: str | None = None


class SafetySubmissionOut(BaseSchema):
    id: int
    adverse_event_id: int
    jurisdiction: str
    recipient_code: str
    report_type: str
    due_at: dt.datetime | None
    submitted_at: dt.datetime | None
    submitted_by: str | None
    submission_reference: str | None
    acknowledged_at: dt.datetime | None
    acknowledgement_reference: str | None
    rejection_reason: str | None
    status: str
    correlation_id: str | None


class ParticipantReimbursementCreate(BaseSchema):
    subject_id: int
    visit_id: int | None = None
    category: str
    amount: float
    notes: str | None = None


class ParticipantReimbursementOut(BaseSchema):
    id: int
    subject_id: int
    visit_id: int | None
    category: str
    amount: float
    currency: str
    status: str
    requested_at: dt.datetime
    approved_by: str | None
    paid_at: dt.datetime | None
    exceeds_guidance_cap: bool
    notes: str | None


class ParticipantSummaryOut(BaseSchema):
    """The participant-facing projection citizen-portal renders.

    CTMS remains the canonical owner (benchmark rule 1); citizen-portal is a
    surface over this contract, not a second source of truth.
    """

    subject_id: int
    subject_number: str
    study_title: str
    jurisdiction: str
    consent_state: str
    consent_version: str | None
    re_consent_required: bool
    withdrawal_effective_immediately: bool
    upcoming_visits: list[dict[str, Any]]
    reimbursements: list[dict[str, Any]]
    reimbursement_currency: str
    results_available: bool
