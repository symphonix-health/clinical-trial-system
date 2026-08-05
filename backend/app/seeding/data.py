"""Seed data definitions."""

from __future__ import annotations

import datetime as dt
from typing import Any

STUDIES: list[dict[str, Any]] = [
    {
        "protocol_number": "ONCO-2026-001",
        "title": "Phase II study of novel kinase inhibitor in advanced solid tumours",
        "phase": "II",
        "indication": "advanced solid tumours",
        "therapeutic_area": "oncology",
        "sponsor": "Symphonix Oncology Ltd",
        "sponsor_organisation_id": "ORG-SYM-ONC-001",
        "jurisdiction": "UK",
        "planned_sites": 5,
        "planned_subjects": 20,
        "start_date": dt.date(2026, 1, 15),
        "end_date": dt.date(2027, 1, 15),
        "status": "recruiting",
    },
    {
        "protocol_number": "CARD-2026-002",
        "title": "Phase III outcomes study in post-MI heart failure",
        "phase": "III",
        "indication": "post-MI heart failure",
        "therapeutic_area": "cardiology",
        "sponsor": "Symphonix Cardiovascular Ltd",
        "sponsor_organisation_id": "ORG-SYM-CAR-002",
        "jurisdiction": "UK",
        "planned_sites": 3,
        "planned_subjects": 15,
        "start_date": dt.date(2026, 2, 1),
        "end_date": dt.date(2027, 2, 1),
        "status": "active",
    },
    {
        "protocol_number": "VACC-2026-003",
        "title": "Phase I paediatric vaccine immunogenicity study",
        "phase": "I",
        "indication": "paediatric vaccine immunogenicity",
        "therapeutic_area": "infectious disease",
        "sponsor": "Symphonix Vaccines Ltd",
        "sponsor_organisation_id": "ORG-SYM-VAC-003",
        "jurisdiction": "IE",
        "planned_sites": 2,
        "planned_subjects": 5,
        "start_date": dt.date(2026, 3, 1),
        "end_date": dt.date(2026, 9, 1),
        "status": "recruiting",
    },
]

SITES: list[dict[str, Any]] = [
    {"study_index": 0, "site_code": "ONC-01", "name": "Royal Marsden Hospital",
     "pi": "dr_sarah_chen", "capacity": 8, "status": "activated"},
    {"study_index": 0, "site_code": "ONC-02", "name": "Memorial Cancer Centre",
     "pi": "dr_james_oliver", "capacity": 5, "status": "activated"},
    {"study_index": 0, "site_code": "ONC-03", "name": "Northwest Oncology Unit",
     "pi": "dr_lisa_park", "capacity": 4, "status": "activated"},
    {"study_index": 0, "site_code": "ONC-04", "name": "Midlands Cancer Research",
     "pi": "dr_ahmed_khan", "capacity": 2, "status": "pending"},
    {"study_index": 0, "site_code": "ONC-05", "name": "Southern Oncology Day Unit",
     "pi": "dr_emma_white", "capacity": 1, "status": "pending"},
    {"study_index": 1, "site_code": "CAR-01", "name": "Guy's and St Thomas' NHS Trust",
     "pi": "dr_robert_brown", "capacity": 8, "status": "activated"},
    {"study_index": 1, "site_code": "CAR-02", "name": "Barts Heart Centre",
     "pi": "dr_nina_patel", "capacity": 4, "status": "activated"},
    {"study_index": 1, "site_code": "CAR-03", "name": "Manchester Heart Unit",
     "pi": "dr_david_lee", "capacity": 3, "status": "activated"},
    {"study_index": 2, "site_code": "VAC-01", "name": "Children's Health Ireland at Crumlin",
     "pi": "dr_maria_garcia", "capacity": 4, "status": "activated"},
    {"study_index": 2, "site_code": "VAC-02", "name": "University Hospital Galway",
     "pi": "dr_tom_wilson", "capacity": 1, "status": "pending"},
]

SUBJECT_TEMPLATES: list[dict[str, Any]] = [
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-001", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-002", "status": "enrolled", "arm": "arm_b",
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-003", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-004", "status": "withdrawn", "arm": None,
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-005", "status": "enrolled", "arm": "arm_b",
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 1, "screening_id": "ONC-S-006", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {
     "study_index": 0,
     "site_index": 1,
     "screening_id": "ONC-S-007",
     "status": "screening",
     "arm": None,
     "consent": None
    },
    {"study_index": 0, "site_index": 1, "screening_id": "ONC-S-008", "status": "enrolled", "arm": "arm_b",
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 2, "screening_id": "ONC-S-009", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 2, "screening_id": "ONC-S-010", "status": "enrolled", "arm": "arm_b",
     "consent": "v1.0"},
    {
     "study_index": 0,
     "site_index": 2,
     "screening_id": "ONC-S-011",
     "status": "screening",
     "arm": None,
     "consent": None
    },
    {"study_index": 0, "site_index": 1, "screening_id": "ONC-S-012", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-013", "status": "enrolled", "arm": "arm_b",
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-014", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-015", "status": "early_terminated", "arm": "arm_b",
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 2, "screening_id": "ONC-S-016", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 2, "screening_id": "ONC-S-017", "status": "enrolled", "arm": "arm_b",
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 1, "screening_id": "ONC-S-018", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 1, "screening_id": "ONC-S-019", "status": "withdrawn", "arm": None,
     "consent": "v1.0"},
    {"study_index": 0, "site_index": 2, "screening_id": "ONC-S-020", "status": "enrolled", "arm": "arm_b",
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 5, "screening_id": "CAR-S-001", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 5, "screening_id": "CAR-S-002", "status": "enrolled", "arm": "arm_b",
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 5, "screening_id": "CAR-S-003", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 6, "screening_id": "CAR-S-004", "status": "enrolled", "arm": "arm_b",
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 6, "screening_id": "CAR-S-005", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 6, "screening_id": "CAR-S-006", "status": "withdrawn", "arm": None,
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 7, "screening_id": "CAR-S-007", "status": "enrolled", "arm": "arm_b",
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 7, "screening_id": "CAR-S-008", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 7, "screening_id": "CAR-S-009", "status": "early_terminated", "arm": "arm_b",
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 5, "screening_id": "CAR-S-010", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 5, "screening_id": "CAR-S-011", "status": "enrolled", "arm": "arm_b",
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 6, "screening_id": "CAR-S-012", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 6, "screening_id": "CAR-S-013", "status": "enrolled", "arm": "arm_b",
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 7, "screening_id": "CAR-S-014", "status": "enrolled", "arm": "arm_a",
     "consent": "v1.0"},
    {"study_index": 1, "site_index": 7, "screening_id": "CAR-S-015", "status": "enrolled", "arm": "arm_b",
     "consent": "v1.0"},
    {
     "study_index": 2,
     "site_index": 8,
     "screening_id": "VAC-S-001",
     "status": "screening",
     "arm": None,
     "consent": None
    },
    {
     "study_index": 2,
     "site_index": 8,
     "screening_id": "VAC-S-002",
     "status": "screening",
     "arm": None,
     "consent": None
    },
    {
     "study_index": 2,
     "site_index": 8,
     "screening_id": "VAC-S-003",
     "status": "screening",
     "arm": None,
     "consent": None
    },
    {
     "study_index": 2,
     "site_index": 8,
     "screening_id": "VAC-S-004",
     "status": "screening",
     "arm": None,
     "consent": None
    },
    {
     "study_index": 2,
     "site_index": 8,
     "screening_id": "VAC-S-005",
     "status": "screening",
     "arm": None,
     "consent": None
    },
]

ADVERSE_EVENTS: list[dict[str, Any]] = [
    {"study_index": 0, "subject_index": 0, "onset_date": dt.date(2026, 4, 1), "severity": "mild",
     "seriousness": "non_serious", "causality": "unrelated", "susar": False},
    {"study_index": 0, "subject_index": 1, "onset_date": dt.date(2026, 4, 5), "severity": "severe",
     "seriousness": "serious", "causality": "related", "susar": False},
    {"study_index": 0, "subject_index": 2, "onset_date": dt.date(2026, 4, 10), "severity": "severe",
     "seriousness": "life_threatening", "causality": "related", "susar": True, "expectedness": "unexpected"},
    {"study_index": 1, "subject_index": 20, "onset_date": dt.date(2026, 5, 12), "severity": "moderate",
     "seriousness": "serious", "causality": "possibly_related", "susar": True, "expectedness": "unexpected"},
    {"study_index": 1, "subject_index": 21, "onset_date": dt.date(2026, 5, 20), "severity": "mild",
     "seriousness": "non_serious", "causality": "unrelated", "susar": False},
]

PROTOCOL_DEVIATIONS: list[dict[str, Any]] = [
    {"study_index": 0, "subject_index": 3, "category": "eligibility", "description": "Subject enrolled outside window",
     "severity": "major"},
    {"study_index": 0, "subject_index": 6, "category": "visit_window", "description": "Visit 2 occurred 3 days late",
     "severity": "minor"},
    {"study_index": 0, "subject_index": 1, "category": "ip_dosing", "description": "Dose administered 2 hours late",
     "severity": "minor"},
    {"study_index": 1, "subject_index": 22, "category": "eligibility", "description": "ECG performed out of window",
     "severity": "minor"},
    {"study_index": 1, "subject_index": 23, "category": "missed_visit", "description": "Week 4 follow-up missed",
     "severity": "major"},
]

PRODUCTS: list[dict[str, Any]] = [
    {"sku": "ONCO-IP-001", "name": "Kinase inhibitor capsules 50mg", "lot": "LOT-A001", "site_study": 0,
     "site_code": "ONC-01", "qty": 200},
    {"sku": "ONCO-IP-002", "name": "Kinase inhibitor capsules 50mg", "lot": "LOT-A002", "site_study": 0,
     "site_code": "ONC-02", "qty": 150},
    {"sku": "CARD-IP-001", "name": "Cardioprotective tablets 10mg", "lot": "LOT-B001", "site_study": 1,
     "site_code": "CAR-01", "qty": 300},
]

REGULATORY_DOCUMENTS: list[dict[str, Any]] = [
    {"study_index": 0, "type": "protocol", "reference": "ONCO-PROTO-v1.0.pdf", "version": "v1.0", "expiry": None},
    {"study_index": 0, "type": "ethics_approval", "reference": "ONCO-ETHICS-001.pdf", "version": "1",
     "expiry": dt.date(2026, 12, 31)},
    {"study_index": 0, "type": "insurance", "reference": "ONCO-INS-001.pdf", "version": "1",
     "expiry": dt.date(2027, 1, 1)},
    {"study_index": 1, "type": "protocol", "reference": "CARD-PROTO-v1.0.pdf", "version": "v1.0", "expiry": None},
    {"study_index": 1, "type": "ethics_approval", "reference": "CARD-ETHICS-001.pdf", "version": "1",
     "expiry": dt.date(2026, 11, 30)},
    {"study_index": 1, "type": "insurance", "reference": "CARD-INS-001.pdf", "version": "1",
     "expiry": dt.date(2027, 2, 1)},
    {"study_index": 2, "type": "protocol", "reference": "VACC-PROTO-v1.0.pdf", "version": "v1.0", "expiry": None},
    {"study_index": 2, "type": "ethics_approval", "reference": "VACC-ETHICS-001.pdf", "version": "1",
     "expiry": dt.date(2026, 10, 15)},
]

QUERIES: list[dict[str, Any]] = [
    {"study_index": 0, "subject_index": 0, "raised_by": "cra_1", "assigned": "crc_1", "status": "open",
     "due": dt.date(2026, 5, 1)},
    {"study_index": 0, "subject_index": 1, "raised_by": "cra_1", "assigned": "crc_2", "status": "resolved",
     "due": dt.date(2026, 4, 20)},
    {"study_index": 1, "subject_index": 20, "raised_by": "cra_2", "assigned": "crc_3", "status": "open",
     "due": dt.date(2026, 6, 1)},
    {"study_index": 1, "subject_index": 22, "raised_by": "cra_2", "assigned": "crc_4", "status": "in_progress",
     "due": dt.date(2026, 5, 25)},
    {"study_index": 0, "subject_index": 2, "raised_by": "cra_1", "assigned": "crc_1", "status": "open",
     "due": dt.date(2026, 4, 15)},
]

BUDGETS: list[dict[str, Any]] = [
    {"study_index": 0, "category": "start_up", "planned": 50000, "actual": 35000},
    {"study_index": 0, "category": "per_subject", "planned": 200000, "actual": 120000},
    {"study_index": 0, "category": "procedures", "planned": 75000, "actual": 30000},
    {"study_index": 1, "category": "start_up", "planned": 40000, "actual": 40000},
    {"study_index": 1, "category": "per_subject", "planned": 150000, "actual": 90000},
    {"study_index": 2, "category": "start_up", "planned": 30000, "actual": 10000},
]

AGENT_SUBJECTS: list[dict[str, Any]] = [
    {
        "principal": "agent://triage-chest-pain/v1", "persona": "triage_chest_pain",
        "contract": "contract-001", "model": "v1.2.0", "owner": "ai_team_1",
        "autonomy": "shadow", "safety": "low", "source": "global_agent_registry",
    },
    {
        "principal": "agent://med-rec/v1", "persona": "medication_reconciliation",
        "contract": "contract-002", "model": "v2.0.1", "owner": "ai_team_2",
        "autonomy": "advisory", "safety": "medium", "source": "nexus_a2a_protocol",
    },
    {
        "principal": "agent://discharge/v1", "persona": "discharge_planning",
        "contract": "contract-003", "model": "v1.5.0", "owner": "ai_team_3",
        "autonomy": "auto_with_threshold_hitl", "safety": "high", "source": "direct",
    },
    {
        "principal": "agent://triage-chest-pain/v2", "persona": "triage_chest_pain",
        "contract": "contract-004", "model": "v1.3.0", "owner": "ai_team_1",
        "autonomy": "advisory", "safety": "low", "source": "global_agent_registry",
    },
    {
        "principal": "agent://med-rec/v2", "persona": "medication_reconciliation",
        "contract": "contract-005", "model": "v2.1.0", "owner": "ai_team_2",
        "autonomy": "shadow", "safety": "medium", "source": "nexus_a2a_protocol",
    },
    {
        "principal": "agent://discharge/v2", "persona": "discharge_planning",
        "contract": "contract-006", "model": "v1.6.0", "owner": "ai_team_3",
        "autonomy": "advisory", "safety": "high", "source": "direct",
    },
    {
        "principal": "agent://differential/v1", "persona": "differential_review",
        "contract": "contract-007", "model": "v0.9.0", "owner": "ai_team_4",
        "autonomy": "shadow", "safety": "critical", "source": "global_agent_registry",
    },
    {
        "principal": "agent://treatment/v1", "persona": "treatment_plan",
        "contract": "contract-008", "model": "v1.0.0", "owner": "ai_team_5",
        "autonomy": "advisory", "safety": "high", "source": "nexus_a2a_protocol",
    },
    {
        "principal": "agent://safety-esc/v1", "persona": "safety_escalation",
        "contract": "contract-009", "model": "v1.1.0", "owner": "safety_team",
        "autonomy": "auto_with_threshold_hitl", "safety": "critical", "source": "direct",
    },
]

AGENT_COHORTS: list[dict[str, Any]] = [
    {
        "name": "Triage agents", "type": "single_agent", "profile": "chest_pain_triage",
        "family": "clinical_triage",
        "objective": "Evaluate safety of autonomous chest-pain triage",
    },
    {
        "name": "Medication reconciliation agents", "type": "single_agent",
        "profile": "med_rec", "family": "medication_safety",
        "objective": "Reduce discharge reconciliation errors",
    },
    {
        "name": "Mixed council", "type": "multi_agent", "profile": "clinical_council",
        "family": "multi_agent_council",
        "objective": "Deliberate on complex treatment plans",
    },
]

SYNTHETIC_ENVIRONMENTS: list[dict[str, Any]] = [
    {
        "name": "Triage chest pain",
        "task": {"steps": ["present_history", "score_risk", "route_decision"]},
        "patients": [{"age": 65, "sex": "M", "presentation": "chest_pain"}],
        "golden": ["present_history", "score_risk", "route_decision"],
        "perturbations": [{"type": "missing_allergy"}],
    },
    {
        "name": "Medication reconciliation",
        "task": {"steps": ["load_home_meds", "compare_ip", "flag_interactions"]},
        "patients": [{"age": 72, "sex": "F", "meds": ["warfarin", "aspirin"]}],
        "golden": ["load_home_meds", "compare_ip", "flag_interactions"],
        "perturbations": [{"type": "duplicate_therapy"}],
    },
    {
        "name": "Discharge planning",
        "task": {"steps": ["assess_mobility", "schedule_follow_up", "education"]},
        "patients": [{"age": 80, "sex": "M", "disposition": "home_with_carer"}],
        "golden": ["assess_mobility", "schedule_follow_up", "education"],
        "perturbations": [{"type": "missed_follow_up"}],
    },
]


# --- National capability seed data (REQ-CTS-NAT-001..008) -------------------

# Public trial-registry entries at three different points of the closed loop:
# receipted, dispatched-but-unreceipted, and rejected. A corpus in which every
# registration is already `registered` cannot exercise the acknowledgement or
# rejection paths at all.
TRIAL_REGISTRATIONS: list[dict[str, Any]] = [
    {
        "study_index": 0,
        "jurisdiction": "UK",
        "registry_code": "ISRCTN",
        "registry_identifier": "ISRCTN48120977",
        "status": "registered",
        "submitted_at": dt.datetime(2026, 1, 8, 10, 0, 0),
        "acknowledged_at": dt.datetime(2026, 1, 11, 14, 30, 0),
        "receipt_reference": "ISRCTN-ACK-2026-004812",
        "rejection_reason": None,
        "public_disclosure_url": "https://www.isrctn.com/ISRCTN48120977",
    },
    {
        "study_index": 1,
        "jurisdiction": "UK",
        "registry_code": "ISRCTN",
        "registry_identifier": None,
        "status": "submitted",
        "submitted_at": dt.datetime(2026, 1, 26, 9, 15, 0),
        "acknowledged_at": None,
        "receipt_reference": None,
        "rejection_reason": None,
        "public_disclosure_url": None,
    },
    {
        "study_index": 2,
        "jurisdiction": "IE",
        "registry_code": "CTIS",
        "registry_identifier": None,
        "status": "rejected",
        "submitted_at": dt.datetime(2026, 2, 18, 8, 45, 0),
        "acknowledged_at": dt.datetime(2026, 2, 21, 16, 5, 0),
        "receipt_reference": None,
        "rejection_reason": "paediatric investigation plan reference missing from Part I",
        "public_disclosure_url": None,
    },
]

# Site delegation log. VAC-01's pharmacist deliberately carries EXPIRED GCP
# training so the site-readiness block is reachable from seed alone.
DELEGATIONS: list[dict[str, Any]] = [
    {
        "site_index": 0,
        "person_id": "dr_sarah_chen",
        "person_name": "Dr Sarah Chen",
        "role": "principal_investigator",
        "delegated_tasks": ["informed_consent", "eligibility_confirmation", "ae_assessment"],
        "delegated_by": "dr_sarah_chen",
        "gcp_training_date": dt.date(2025, 3, 4),
        "gcp_training_expiry": dt.date(2027, 3, 4),
        "professional_registration": "GMC-7712045",
        "start_date": dt.date(2026, 1, 12),
        "status": "active",
    },
    {
        "site_index": 0,
        "person_id": "crc_1",
        "person_name": "Nuala Byrne",
        "role": "clinical_research_coordinator",
        "delegated_tasks": ["screening_data_entry", "visit_scheduling"],
        "delegated_by": "dr_sarah_chen",
        "gcp_training_date": dt.date(2025, 6, 18),
        "gcp_training_expiry": dt.date(2027, 6, 18),
        "professional_registration": "NMC-88231",
        "start_date": dt.date(2026, 1, 14),
        "status": "active",
    },
    {
        "site_index": 5,
        "person_id": "dr_robert_brown",
        "person_name": "Dr Robert Brown",
        "role": "principal_investigator",
        "delegated_tasks": ["informed_consent", "ae_assessment", "unblinding_authorisation"],
        "delegated_by": "dr_robert_brown",
        "gcp_training_date": dt.date(2025, 9, 1),
        "gcp_training_expiry": dt.date(2027, 9, 1),
        "professional_registration": "GMC-6120338",
        "start_date": dt.date(2026, 2, 2),
        "status": "active",
    },
    {
        "site_index": 8,
        "person_id": "pharm_vac_01",
        "person_name": "Aoife Ni Dhomhnaill",
        "role": "site_pharmacist",
        "delegated_tasks": ["ip_receipt", "ip_dispensing", "ip_accountability"],
        "delegated_by": "dr_maria_garcia",
        "gcp_training_date": dt.date(2022, 1, 10),
        "gcp_training_expiry": dt.date(2025, 1, 10),
        "professional_registration": "PSI-20114",
        "start_date": dt.date(2026, 3, 2),
        "status": "expired",
    },
]

# Ethics and competent-authority submissions. Every non-pending decision
# carries a NAMED decider -- research governance never auto-approves.
REGULATORY_APPROVALS: list[dict[str, Any]] = [
    {
        "study_index": 0,
        "jurisdiction": "UK",
        "authority_code": "HRA-REC",
        "authority_kind": "ethics",
        "submission_type": "initial",
        "submission_reference": "IRAS-318442",
        "submitted_at": dt.datetime(2025, 11, 3, 9, 0, 0),
        "decision": "approved",
        "decision_at": dt.datetime(2025, 12, 1, 15, 20, 0),
        "decided_by": "Prof Helen Whitmore (REC chair, London-Surrey Borders)",
        "conditions": None,
        "approval_expiry": dt.date(2027, 12, 1),
        "next_report_due": dt.date(2026, 12, 1),
        "protocol_version": "v1.0",
    },
    {
        "study_index": 0,
        "jurisdiction": "UK",
        "authority_code": "MHRA",
        "authority_kind": "competent_authority",
        "submission_type": "initial",
        "submission_reference": "CTA-21761-0042-0001",
        "submitted_at": dt.datetime(2025, 11, 3, 9, 5, 0),
        "decision": "approved_with_conditions",
        "decision_at": dt.datetime(2025, 12, 8, 11, 40, 0),
        "decided_by": "MHRA assessor R. Iyengar",
        "conditions": [
            {
                "reference": "COND-001",
                "text": "Submit updated Investigator Brochure section 5.4 before first dose.",
                "due": "2026-01-10",
                "status": "met",
            }
        ],
        "approval_expiry": dt.date(2027, 12, 8),
        "next_report_due": dt.date(2026, 12, 8),
        "protocol_version": "v1.0",
    },
    {
        "study_index": 1,
        "jurisdiction": "UK",
        "authority_code": "HRA-REC",
        "authority_kind": "ethics",
        "submission_type": "amendment",
        "submission_reference": "IRAS-318442-AM02",
        "submitted_at": dt.datetime(2026, 6, 2, 10, 30, 0),
        "decision": "pending",
        "decision_at": None,
        "decided_by": None,
        "conditions": None,
        "approval_expiry": None,
        "next_report_due": None,
        "protocol_version": "v2.0",
    },
    {
        "study_index": 2,
        "jurisdiction": "IE",
        "authority_code": "NREC-CT",
        "authority_kind": "ethics",
        "submission_type": "initial",
        "submission_reference": "NREC-2026-0117",
        "submitted_at": dt.datetime(2026, 1, 20, 9, 0, 0),
        "decision": "approved",
        "decision_at": dt.datetime(2026, 2, 17, 13, 0, 0),
        "decided_by": "Dr Cathal O Riain (NREC-CT chair)",
        "conditions": None,
        "approval_expiry": dt.date(2027, 2, 17),
        "next_report_due": dt.date(2027, 2, 17),
        "protocol_version": "v1.0",
    },
]

# Hub-mediated eligibility pre-screens covering all three outcomes, so the
# derived-outcome logic (any-false -> ineligible, any-unknown -> review,
# all-true -> eligible) is exercised end to end from seed.
ELIGIBILITY_SCREENINGS: list[dict[str, Any]] = [
    {
        "study_index": 0,
        "site_index": 0,
        "candidate_reference": "CAND-ONC-4471",
        "consent_basis": "research_contact_consent",
        "requested_by": "crc_1",
        "criteria_requested": ["age_18_or_over", "ecog_0_to_2", "no_prior_kinase_inhibitor"],
        "criteria_evaluated": {
            "age_18_or_over": True,
            "ecog_0_to_2": True,
            "no_prior_kinase_inhibitor": True,
        },
        "outcome": "eligible",
        "outcome_at": dt.datetime(2026, 3, 4, 10, 12, 0),
        "reviewed_by": "dr_sarah_chen",
        "source_system": "bullettrain-hub",
        "correlation_id": "ctms-eligibility-seed-0001",
    },
    {
        "study_index": 0,
        "site_index": 1,
        "candidate_reference": "CAND-ONC-4488",
        "consent_basis": "research_contact_consent",
        "requested_by": "crc_2",
        "criteria_requested": ["age_18_or_over", "ecog_0_to_2", "no_prior_kinase_inhibitor"],
        "criteria_evaluated": {
            "age_18_or_over": True,
            "ecog_0_to_2": False,
            "no_prior_kinase_inhibitor": True,
        },
        "outcome": "ineligible",
        "outcome_at": dt.datetime(2026, 3, 6, 8, 55, 0),
        "reviewed_by": "dr_james_oliver",
        "source_system": "bullettrain-hub",
        "correlation_id": "ctms-eligibility-seed-0002",
    },
    {
        "study_index": 1,
        "site_index": 5,
        "candidate_reference": "CAND-CAR-2210",
        "consent_basis": "research_contact_consent",
        "requested_by": "crc_3",
        "criteria_requested": ["lvef_below_40", "post_mi_within_12_months", "no_ckd_stage_5"],
        "criteria_evaluated": {
            "lvef_below_40": True,
            "post_mi_within_12_months": None,
            "no_ckd_stage_5": True,
        },
        "outcome": "pending_review",
        "outcome_at": dt.datetime(2026, 4, 2, 16, 40, 0),
        "reviewed_by": None,
        "source_system": "bullettrain-hub",
        "correlation_id": "ctms-eligibility-seed-0003",
    },
]

# Participant expense / inconvenience payments, including one deliberately
# over the jurisdiction's per-visit guidance cap so the flag is exercised.
REIMBURSEMENTS: list[dict[str, Any]] = [
    {
        "subject_index": 0,
        "category": "travel",
        "amount": 32.5,
        "currency": "GBP",
        "status": "paid",
        "approved_by": "finance_coordinator_1",
        "exceeds_guidance_cap": False,
        "notes": "Return rail fare, screening visit",
    },
    {
        "subject_index": 1,
        "category": "inconvenience",
        "amount": 60.0,
        "currency": "GBP",
        "status": "approved",
        "approved_by": "finance_coordinator_1",
        "exceeds_guidance_cap": False,
        "notes": "Extended pharmacokinetic sampling visit",
    },
    {
        "subject_index": 20,
        "category": "travel",
        "amount": 128.4,
        "currency": "GBP",
        "status": "requested",
        "approved_by": None,
        "exceeds_guidance_cap": True,
        "notes": "Overnight accommodation, cross-region site transfer",
    },
]
