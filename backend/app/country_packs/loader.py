"""Load, validate and query the versioned country packs.

Packs are read once and cached. Every pack must declare the same top-level
contract (``REQUIRED_SECTIONS``) so that a domain caller can rely on a
section being present for ANY jurisdiction -- a pack that silently omits
``safety_reporting`` would make a statutory deadline disappear rather than
fail, which is the failure mode this validation exists to prevent.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

PACK_DIR = Path(__file__).resolve().parent / "packs"
SCHEMA_VERSION = "CTMS_COUNTRY_PACK_V1"
DEFAULT_JURISDICTION = "IE"

REQUIRED_SECTIONS = (
    "competent_authority",
    "ethics_authority",
    "trial_registry",
    "safety_reporting",
    "consent",
    "site_credentialing",
    "participant_reimbursement",
)

REQUIRED_SAFETY_KEYS = (
    "susar_fatal_or_life_threatening_days",
    "susar_other_days",
    "non_susar_serious_days",
)

# Seriousness grades that attract the shorter statutory clock. Kept here (not
# in the pack) because the ICH E2A grading vocabulary is the DOMAIN model; the
# number of days attached to it is the country POLICY and lives in the pack.
EXPEDITED_SERIOUSNESS = frozenset({"life_threatening", "fatal"})
SERIOUS_SERIOUSNESS = frozenset({"serious"}) | EXPEDITED_SERIOUSNESS


class CountryPackError(RuntimeError):
    """Raised when a jurisdiction is unknown or its pack is malformed."""


def _validate(code: str, payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise CountryPackError(f"country pack {code}: schema_version must be {SCHEMA_VERSION}")
    for field in ("code", "name", "pack_version", "effective_from", "sources"):
        if not payload.get(field):
            raise CountryPackError(f"country pack {code}: missing {field}")
    if payload["code"] != code:
        raise CountryPackError(f"country pack {code}: declares code {payload['code']!r}")
    dt.date.fromisoformat(payload["effective_from"])
    for section in REQUIRED_SECTIONS:
        if not isinstance(payload.get(section), dict):
            raise CountryPackError(f"country pack {code}: missing section {section}")
    for key in REQUIRED_SAFETY_KEYS:
        if not isinstance(payload["safety_reporting"].get(key), int):
            raise CountryPackError(f"country pack {code}: safety_reporting.{key} must be an integer")
    for source in payload["sources"]:
        for field in ("title", "publisher", "url", "accessed"):
            if not source.get(field):
                raise CountryPackError(f"country pack {code}: source missing {field}")
    return payload


@lru_cache(maxsize=1)
def _load_all() -> dict[str, dict[str, Any]]:
    packs: dict[str, dict[str, Any]] = {}
    for path in sorted(PACK_DIR.glob("*.json")):
        code = path.stem.upper()
        packs[code] = _validate(code, json.loads(path.read_text(encoding="utf-8")))
    if not packs:  # pragma: no cover - defensive; packs ship with the package
        raise CountryPackError("no country packs found")
    return packs


def list_packs() -> list[dict[str, Any]]:
    """Every pack, ordered by code."""

    return [_load_all()[code] for code in sorted(_load_all())]


def get_pack(code: str | None = None) -> dict[str, Any]:
    """Return one pack. ``None`` resolves to the default jurisdiction."""

    resolved = (code or DEFAULT_JURISDICTION).upper()
    packs = _load_all()
    if resolved not in packs:
        raise CountryPackError(f"unknown jurisdiction {resolved!r}; known: {sorted(packs)}")
    return packs[resolved]


def susar_deadline_days(
    seriousness: str, expectedness: str, causality: str, jurisdiction: str | None = None
) -> int | None:
    """Statutory reporting clock in days, or ``None`` when none applies.

    ICH E2A / EU CTR 536/2014 Art. 42 / 21 CFR 312.32(c) all agree on the
    grading: a SUSAR (serious + unexpected + at least possibly related) that is
    fatal or life-threatening is reportable within the pack's expedited window,
    any other SUSAR within the standard window, and a serious-but-expected or
    unrelated event within the pack's non-SUSAR window. The DAY COUNTS come
    from the pack, never from this function.
    """

    if seriousness not in SERIOUS_SERIOUSNESS:
        return None
    policy = get_pack(jurisdiction)["safety_reporting"]
    if is_susar(seriousness, expectedness, causality):
        if seriousness in EXPEDITED_SERIOUSNESS:
            return int(policy["susar_fatal_or_life_threatening_days"])
        return int(policy["susar_other_days"])
    return int(policy["non_susar_serious_days"])


def is_susar(seriousness: str, expectedness: str, causality: str) -> bool:
    """Suspected Unexpected Serious Adverse Reaction, per ICH E2A.

    All three limbs are required: SERIOUS, UNEXPECTED, and a suspected causal
    relationship to the investigational product.
    """

    return (
        seriousness in SERIOUS_SERIOUSNESS
        and expectedness == "unexpected"
        and causality in {"related", "probably_related", "possibly_related"}
    )


def validate_registry_identifier(identifier: str, jurisdiction: str | None = None) -> bool:
    """True when ``identifier`` matches the jurisdiction's registry format."""

    registry = get_pack(jurisdiction)["trial_registry"]
    pattern = registry.get("identifier_pattern")
    if not pattern:  # pragma: no cover - every shipped pack declares one
        return True
    return re.fullmatch(pattern, identifier) is not None
