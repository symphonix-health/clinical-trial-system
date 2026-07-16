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
        "planned_sites": 2,
        "planned_subjects": 5,
        "start_date": dt.date(2026, 3, 1),
        "end_date": dt.date(2026, 9, 1),
        "status": "recruiting",
    },
]

SITES: list[dict[str, Any]] = [
    {"study_index": 0, "site_code": "ONC-01", "name": "Royal Marsden Hospital", "pi": "dr_sarah_chen", "capacity": 8, "status": "activated"},
    {"study_index": 0, "site_code": "ONC-02", "name": "Memorial Cancer Centre", "pi": "dr_james_oliver", "capacity": 5, "status": "activated"},
    {"study_index": 0, "site_code": "ONC-03", "name": "Northwest Oncology Unit", "pi": "dr_lisa_park", "capacity": 4, "status": "activated"},
    {"study_index": 0, "site_code": "ONC-04", "name": "Midlands Cancer Research", "pi": "dr_ahmed_khan", "capacity": 2, "status": "pending"},
    {"study_index": 0, "site_code": "ONC-05", "name": "Southern Oncology Day Unit", "pi": "dr_emma_white", "capacity": 1, "status": "pending"},
    {"study_index": 1, "site_code": "CAR-01", "name": "Guy's and St Thomas' NHS Trust", "pi": "dr_robert_brown", "capacity": 8, "status": "activated"},
    {"study_index": 1, "site_code": "CAR-02", "name": "Barts Heart Centre", "pi": "dr_nina_patel", "capacity": 4, "status": "activated"},
    {"study_index": 1, "site_code": "CAR-03", "name": "Manchester Heart Unit", "pi": "dr_david_lee", "capacity": 3, "status": "activated"},
    {"study_index": 2, "site_code": "VAC-01", "name": "Birmingham Children's Hospital", "pi": "dr_maria_garcia", "capacity": 4, "status": "activated"},
    {"study_index": 2, "site_code": "VAC-02", "name": "Royal Hospital for Children", "pi": "dr_tom_wilson", "capacity": 1, "status": "pending"},
]

SUBJECT_TEMPLATES: list[dict[str, Any]] = [
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-001", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-002", "status": "enrolled", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-003", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-004", "status": "withdrawn", "arm": None, "consent": "v1.0"},
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-005", "status": "enrolled", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 0, "site_index": 1, "screening_id": "ONC-S-006", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 0, "site_index": 1, "screening_id": "ONC-S-007", "status": "screening", "arm": None, "consent": None},
    {"study_index": 0, "site_index": 1, "screening_id": "ONC-S-008", "status": "enrolled", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 0, "site_index": 2, "screening_id": "ONC-S-009", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 0, "site_index": 2, "screening_id": "ONC-S-010", "status": "enrolled", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 0, "site_index": 2, "screening_id": "ONC-S-011", "status": "screening", "arm": None, "consent": None},
    {"study_index": 0, "site_index": 1, "screening_id": "ONC-S-012", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-013", "status": "enrolled", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-014", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 0, "site_index": 0, "screening_id": "ONC-S-015", "status": "early_terminated", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 0, "site_index": 2, "screening_id": "ONC-S-016", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 0, "site_index": 2, "screening_id": "ONC-S-017", "status": "enrolled", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 0, "site_index": 1, "screening_id": "ONC-S-018", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 0, "site_index": 1, "screening_id": "ONC-S-019", "status": "withdrawn", "arm": None, "consent": "v1.0"},
    {"study_index": 0, "site_index": 2, "screening_id": "ONC-S-020", "status": "enrolled", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 1, "site_index": 5, "screening_id": "CAR-S-001", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 1, "site_index": 5, "screening_id": "CAR-S-002", "status": "enrolled", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 1, "site_index": 5, "screening_id": "CAR-S-003", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 1, "site_index": 6, "screening_id": "CAR-S-004", "status": "enrolled", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 1, "site_index": 6, "screening_id": "CAR-S-005", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 1, "site_index": 6, "screening_id": "CAR-S-006", "status": "withdrawn", "arm": None, "consent": "v1.0"},
    {"study_index": 1, "site_index": 7, "screening_id": "CAR-S-007", "status": "enrolled", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 1, "site_index": 7, "screening_id": "CAR-S-008", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 1, "site_index": 7, "screening_id": "CAR-S-009", "status": "early_terminated", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 1, "site_index": 5, "screening_id": "CAR-S-010", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 1, "site_index": 5, "screening_id": "CAR-S-011", "status": "enrolled", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 1, "site_index": 6, "screening_id": "CAR-S-012", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 1, "site_index": 6, "screening_id": "CAR-S-013", "status": "enrolled", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 1, "site_index": 7, "screening_id": "CAR-S-014", "status": "enrolled", "arm": "arm_a", "consent": "v1.0"},
    {"study_index": 1, "site_index": 7, "screening_id": "CAR-S-015", "status": "enrolled", "arm": "arm_b", "consent": "v1.0"},
    {"study_index": 2, "site_index": 8, "screening_id": "VAC-S-001", "status": "screening", "arm": None, "consent": None},
    {"study_index": 2, "site_index": 8, "screening_id": "VAC-S-002", "status": "screening", "arm": None, "consent": None},
    {"study_index": 2, "site_index": 8, "screening_id": "VAC-S-003", "status": "screening", "arm": None, "consent": None},
    {"study_index": 2, "site_index": 8, "screening_id": "VAC-S-004", "status": "screening", "arm": None, "consent": None},
    {"study_index": 2, "site_index": 8, "screening_id": "VAC-S-005", "status": "screening", "arm": None, "consent": None},
]

ADVERSE_EVENTS: list[dict[str, Any]] = [
    {"study_index": 0, "subject_index": 0, "onset_date": dt.date(2026, 4, 1), "severity": "mild", "seriousness": "non_serious", "causality": "unrelated", "susar": False},
    {"study_index": 0, "subject_index": 1, "onset_date": dt.date(2026, 4, 5), "severity": "severe", "seriousness": "serious", "causality": "related", "susar": False},
    {"study_index": 0, "subject_index": 2, "onset_date": dt.date(2026, 4, 10), "severity": "severe", "seriousness": "life_threatening", "causality": "related", "susar": True},
    {"study_index": 1, "subject_index": 20, "onset_date": dt.date(2026, 5, 12), "severity": "moderate", "seriousness": "serious", "causality": "possibly_related", "susar": True},
    {"study_index": 1, "subject_index": 21, "onset_date": dt.date(2026, 5, 20), "severity": "mild", "seriousness": "non_serious", "causality": "unrelated", "susar": False},
]

PROTOCOL_DEVIATIONS: list[dict[str, Any]] = [
    {"study_index": 0, "subject_index": 3, "category": "eligibility", "description": "Subject enrolled outside window", "severity": "major"},
    {"study_index": 0, "subject_index": 6, "category": "visit_window", "description": "Visit 2 occurred 3 days late", "severity": "minor"},
    {"study_index": 0, "subject_index": 1, "category": "ip_dosing", "description": "Dose administered 2 hours late", "severity": "minor"},
    {"study_index": 1, "subject_index": 22, "category": "eligibility", "description": "ECG performed out of window", "severity": "minor"},
    {"study_index": 1, "subject_index": 23, "category": "missed_visit", "description": "Week 4 follow-up missed", "severity": "major"},
]

PRODUCTS: list[dict[str, Any]] = [
    {"sku": "ONCO-IP-001", "name": "Kinase inhibitor capsules 50mg", "lot": "LOT-A001", "site_study": 0, "site_code": "ONC-01", "qty": 200},
    {"sku": "ONCO-IP-002", "name": "Kinase inhibitor capsules 50mg", "lot": "LOT-A002", "site_study": 0, "site_code": "ONC-02", "qty": 150},
    {"sku": "CARD-IP-001", "name": "Cardioprotective tablets 10mg", "lot": "LOT-B001", "site_study": 1, "site_code": "CAR-01", "qty": 300},
]

REGULATORY_DOCUMENTS: list[dict[str, Any]] = [
    {"study_index": 0, "type": "protocol", "reference": "ONCO-PROTO-v1.0.pdf", "version": "v1.0", "expiry": None},
    {"study_index": 0, "type": "ethics_approval", "reference": "ONCO-ETHICS-001.pdf", "version": "1", "expiry": dt.date(2026, 12, 31)},
    {"study_index": 0, "type": "insurance", "reference": "ONCO-INS-001.pdf", "version": "1", "expiry": dt.date(2027, 1, 1)},
    {"study_index": 1, "type": "protocol", "reference": "CARD-PROTO-v1.0.pdf", "version": "v1.0", "expiry": None},
    {"study_index": 1, "type": "ethics_approval", "reference": "CARD-ETHICS-001.pdf", "version": "1", "expiry": dt.date(2026, 11, 30)},
    {"study_index": 1, "type": "insurance", "reference": "CARD-INS-001.pdf", "version": "1", "expiry": dt.date(2027, 2, 1)},
    {"study_index": 2, "type": "protocol", "reference": "VACC-PROTO-v1.0.pdf", "version": "v1.0", "expiry": None},
    {"study_index": 2, "type": "ethics_approval", "reference": "VACC-ETHICS-001.pdf", "version": "1", "expiry": dt.date(2026, 10, 15)},
]

QUERIES: list[dict[str, Any]] = [
    {"study_index": 0, "subject_index": 0, "raised_by": "cra_1", "assigned": "crc_1", "status": "open", "due": dt.date(2026, 5, 1)},
    {"study_index": 0, "subject_index": 1, "raised_by": "cra_1", "assigned": "crc_2", "status": "resolved", "due": dt.date(2026, 4, 20)},
    {"study_index": 1, "subject_index": 20, "raised_by": "cra_2", "assigned": "crc_3", "status": "open", "due": dt.date(2026, 6, 1)},
    {"study_index": 1, "subject_index": 22, "raised_by": "cra_2", "assigned": "crc_4", "status": "in_progress", "due": dt.date(2026, 5, 25)},
    {"study_index": 0, "subject_index": 2, "raised_by": "cra_1", "assigned": "crc_1", "status": "open", "due": dt.date(2026, 4, 15)},
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
    {"principal": "agent://triage-chest-pain/v1", "persona": "triage_chest_pain", "contract": "contract-001", "model": "v1.2.0", "owner": "ai_team_1", "autonomy": "shadow", "safety": "low", "source": "global_agent_registry"},
    {"principal": "agent://med-rec/v1", "persona": "medication_reconciliation", "contract": "contract-002", "model": "v2.0.1", "owner": "ai_team_2", "autonomy": "advisory", "safety": "medium", "source": "nexus_a2a_protocol"},
    {"principal": "agent://discharge/v1", "persona": "discharge_planning", "contract": "contract-003", "model": "v1.5.0", "owner": "ai_team_3", "autonomy": "auto_with_threshold_hitl", "safety": "high", "source": "direct"},
    {"principal": "agent://triage-chest-pain/v2", "persona": "triage_chest_pain", "contract": "contract-004", "model": "v1.3.0", "owner": "ai_team_1", "autonomy": "advisory", "safety": "low", "source": "global_agent_registry"},
    {"principal": "agent://med-rec/v2", "persona": "medication_reconciliation", "contract": "contract-005", "model": "v2.1.0", "owner": "ai_team_2", "autonomy": "shadow", "safety": "medium", "source": "nexus_a2a_protocol"},
    {"principal": "agent://discharge/v2", "persona": "discharge_planning", "contract": "contract-006", "model": "v1.6.0", "owner": "ai_team_3", "autonomy": "advisory", "safety": "high", "source": "direct"},
    {"principal": "agent://differential/v1", "persona": "differential_review", "contract": "contract-007", "model": "v0.9.0", "owner": "ai_team_4", "autonomy": "shadow", "safety": "critical", "source": "global_agent_registry"},
    {"principal": "agent://treatment/v1", "persona": "treatment_plan", "contract": "contract-008", "model": "v1.0.0", "owner": "ai_team_5", "autonomy": "advisory", "safety": "high", "source": "nexus_a2a_protocol"},
    {"principal": "agent://safety-esc/v1", "persona": "safety_escalation", "contract": "contract-009", "model": "v1.1.0", "owner": "safety_team", "autonomy": "auto_with_threshold_hitl", "safety": "critical", "source": "direct"},
]

AGENT_COHORTS: list[dict[str, Any]] = [
    {"name": "Triage agents", "type": "single_agent", "profile": "chest_pain_triage", "family": "clinical_triage", "objective": "Evaluate safety of autonomous chest-pain triage"},
    {"name": "Medication reconciliation agents", "type": "single_agent", "profile": "med_rec", "family": "medication_safety", "objective": "Reduce discharge reconciliation errors"},
    {"name": "Mixed council", "type": "multi_agent", "profile": "clinical_council", "family": "multi_agent_council", "objective": "Deliberate on complex treatment plans"},
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
