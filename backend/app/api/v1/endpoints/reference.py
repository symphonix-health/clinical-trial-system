"""Reference valuesets."""

from fastapi import APIRouter

from app import schemas

router = APIRouter()

VALUESETS: dict[str, list[str]] = {
    "therapeutic_areas": ["oncology", "cardiology", "infectious disease", "neurology", "endocrinology"],
    "phases": ["I", "II", "III", "IV", "observational"],
    "document_types": ["protocol", "ibc", "ethics_approval", "dsmb", "insurance", "investigator_brochure"],
    "ae_seriousness": ["non_serious", "serious", "life_threatening", "fatal"],
    "ip_storage_conditions": ["2-8C", "15-25C", "frozen", "room temperature", "protected from light"],
    "agent_autonomy_levels": ["shadow", "advisory", "auto_with_threshold_hitl"],
    "governance_tiers": ["low", "medium", "high", "critical"],
    "arena_metric_names": [
        "task_success",
        "path_optimality",
        "unsafe_action_rate",
        "permission_breach_rate",
        "consent_breach_rate",
        "human_handoff_rate",
        "mean_steps_vs_golden",
    ],
}


@router.get("/reference/{valueset}", response_model=schemas.ValuesetOut)
async def get_valueset(valueset: str) -> schemas.ValuesetOut:
    return schemas.ValuesetOut(name=valueset, values=VALUESETS.get(valueset, []))
