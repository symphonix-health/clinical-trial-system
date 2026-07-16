"""Bootstrap CTMS canonical matrices and requirements metadata.

This one-off script:
1. Copies the existing 14-column functional matrix to reduced_json_matrices/.
2. Adds per-scenario requirement_ids to the json_matrices functional matrix.
3. Adds FR-C-13 coverage and a set of derived NFRs to the superset.
4. Prepares files for caid.matrices.build_canonical_matrices.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARN = ROOT / "tests" / "harness"
JSON_DIR = HARN / "json_matrices"
REDUCED_DIR = HARN / "reduced_json_matrices"
SUPERSET_PATH = HARN / "requirements_superset.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


REQUIREMENT_MAP: dict[str, list[str]] = {
    "CTMS-UC-001": ["FR-C-11", "FR-C-12"],
    "CTMS-UC-002": ["FR-C-21", "FR-C-22"],
    "CTMS-UC-003": ["FR-C-31", "FR-C-32"],
    "CTMS-UC-004": ["FR-C-34"],
    "CTMS-UC-005": ["FR-C-35"],
    "CTMS-UC-006": ["FR-C-41", "FR-C-42", "FR-C-43"],
    "CTMS-UC-007": ["FR-C-51", "FR-C-52"],
    "CTMS-UC-008": ["FR-C-61", "FR-C-62"],
    "CTMS-UC-009": ["FR-C-71", "FR-C-72"],
    "CTMS-UC-010": ["FR-C-81", "FR-C-83"],
    "CTMS-UC-011": ["FR-C-91"],
    "CTMS-UC-012": ["FR-C-A11"],
    "CTMS-UC-013": ["FR-C-A12"],
    "CTMS-UC-014": ["FR-C-A21"],
    "CTMS-UC-015": ["FR-C-A22", "FR-C-A23"],
    "CTMS-UC-016": ["FR-C-A31"],
    "CTMS-UC-017": ["FR-C-A41"],
    "CTMS-UC-018": ["FR-C-11"],
    "CTMS-UC-019": ["FR-C-11"],
}


def main() -> None:
    REDUCED_DIR.mkdir(parents=True, exist_ok=True)

    original_path = JSON_DIR / "ctms_scenarios.json"
    functional = load_json(original_path)

    # Retain a pristine 14-column copy for local harness execution.
    reduced_path = REDUCED_DIR / "ctms_matrix.14col.json"
    save_json(reduced_path, functional)
    print(f"[OK] retained 14-column matrix at {reduced_path.relative_to(ROOT)}")

    # Augment the json_matrices functional matrix with requirement_ids.
    for case in functional["test_cases"]:
        case["requirement_ids"] = REQUIREMENT_MAP.get(case["use_case_id"], [])

    # Add explicit FR-C-13 amendment coverage.
    amendment_case = {
        "use_case_id": "CTMS-UC-020",
        "component": "clinical_trial_system",
        "scenario": "Amend an active study and create a new protocol version",
        "test_type": "positive",
        "priority": "high",
        "expected_outcomes": ["Study amended", "New ProtocolVersion created", "Sites notified"],
        "preconditions": {"study_status": "approved", "auth_role": "sponsor_manager"},
        "test_data": {"amendment_summary": "Updated inclusion criteria"},
        "validation_rules": ["response.status_code == 200"],
        "dependencies": ["app.api.v1.endpoints.studies", "app.crud.amend_study"],
        "tags": ["study", "amendment", "FR-C-13"],
        "estimated_duration": 2,
        "automation_status": "automated",
        "notes": "Covers FR-C-13",
        "requirement_ids": ["FR-C-13"],
    }
    functional["test_cases"].append(amendment_case)
    functional["metadata"]["requirement_ids"].append("FR-C-13")

    save_json(original_path, functional)
    print(f"[OK] augmented functional matrix at {original_path.relative_to(ROOT)}")

    # Add derived NFRs to the requirements superset.
    superset = load_json(SUPERSET_PATH)
    nfrs = [
        {
            "requirement_id": "NFR-C-PE-001",
            "family": "PERFORMANCE",
            "title": "Dashboard query response time",
            "statement": "The system shall return recruitment and milestone dashboard queries within 500 ms at the 95th percentile under normal load.",
            "category": "non-functional",
            "source": "docs/REQUIREMENTS.md",
            "iso_25010_characteristic": "Performance Efficiency",
            "iso_25010_subcharacteristic": "Time Behaviour",
        },
        {
            "requirement_id": "NFR-C-PE-002",
            "family": "PERFORMANCE",
            "title": "Concurrent enrolment throughput",
            "statement": "The system shall support at least 50 concurrent subject enrolments per minute without error or response-time degradation beyond 1 second.",
            "category": "non-functional",
            "source": "docs/REQUIREMENTS.md",
            "iso_25010_characteristic": "Performance Efficiency",
            "iso_25010_subcharacteristic": "Capacity",
        },
        {
            "requirement_id": "NFR-C-SE-001",
            "family": "SECURITY",
            "title": "OIDC JWT authentication",
            "statement": "The system shall authenticate every API request with a valid OIDC JWT and reject requests with missing, expired, or tampered tokens.",
            "category": "non-functional",
            "source": "docs/REQUIREMENTS.md",
            "iso_25010_characteristic": "Security",
            "iso_25010_subcharacteristic": "Authentication",
        },
        {
            "requirement_id": "NFR-C-SE-002",
            "family": "SECURITY",
            "title": "Role-based access control",
            "statement": "The system shall enforce role-based access control so that sponsor managers, regulatory officers, safety officers, and coordinators can only perform actions permitted by their roles.",
            "category": "non-functional",
            "source": "docs/REQUIREMENTS.md",
            "iso_25010_characteristic": "Security",
            "iso_25010_subcharacteristic": "Authorisation",
        },
        {
            "requirement_id": "NFR-C-RE-001",
            "family": "RELIABILITY",
            "title": "Audit log durability",
            "statement": "The system shall durably record every protocol status change, site activation, subject enrolment, and adverse-event report to an append-only audit log.",
            "category": "non-functional",
            "source": "docs/REQUIREMENTS.md",
            "iso_25010_characteristic": "Reliability",
            "iso_25010_subcharacteristic": "Availability",
        },
        {
            "requirement_id": "NFR-C-SA-001",
            "family": "SAFETY",
            "title": "SUSAR critical alert latency",
            "statement": "The system shall raise a critical SUSAR alert to the safety officer, PI, and sponsor manager within 60 seconds of adverse-event creation when the regulatory deadline is within 24 hours.",
            "category": "non-functional",
            "source": "docs/REQUIREMENTS.md",
            "iso_25010_characteristic": "Reliability",
            "iso_25010_subcharacteristic": "Maturity",
        },
        {
            "requirement_id": "NFR-C-CO-001",
            "family": "COMPATIBILITY",
            "title": "FHIR R4 export compatibility",
            "statement": "The system shall export study, site, subject, and adverse-event data as valid FHIR R4 resources for interoperability with external research platforms.",
            "category": "non-functional",
            "source": "docs/REQUIREMENTS.md",
            "iso_25010_characteristic": "Compatibility",
            "iso_25010_subcharacteristic": "Interoperability",
        },
        {
            "requirement_id": "NFR-C-MA-001",
            "family": "MAINTAINABILITY",
            "title": "Configurable workflow versioning",
            "statement": "The system shall support configurable study workflow and consent versioning without requiring a code deployment for routine protocol amendments.",
            "category": "non-functional",
            "source": "docs/REQUIREMENTS.md",
            "iso_25010_characteristic": "Maintainability",
            "iso_25010_subcharacteristic": "Modifiability",
        },
    ]
    superset["requirements"].extend(nfrs)
    superset["metadata"]["requirement_count"] = len(superset["requirements"])
    save_json(SUPERSET_PATH, superset)
    print(f"[OK] added {len(nfrs)} NFRs to superset")

    # Emit derived_nfrs.json for the CAID NFR canonical-matrix builder.
    derived_nfrs = {
        "schema_version": "BT_DERIVED_NFRS_V1",
        "derived_nfrs": [
            {
                "requirement_id": n["requirement_id"],
                "title": n["title"],
                "statement": n["statement"],
                "rationale": "Derived from clinical-trial-system quality attributes.",
                "category": n["category"],
                "priority": "HIGH",
                "iso_25010_characteristic": n["iso_25010_characteristic"],
                "iso_25010_subcharacteristic": n["iso_25010_subcharacteristic"],
                "regulatory_ref": "",
                "trace_links": ["FR-C-11"],
                "acceptance_criteria": [
                    {
                        "ac_id": f"{n['requirement_id']}-AC01",
                        "given": "the system is running in a validated test environment",
                        "when": "the documented quality-attribute condition is exercised",
                        "then": "the system satisfies the NFR statement",
                        "test_type": "Positive",
                    }
                ],
            }
            for n in nfrs
        ],
    }
    derived_path = HARN / "derived_nfrs.json"
    save_json(derived_path, derived_nfrs)
    print(f"[OK] wrote {derived_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
