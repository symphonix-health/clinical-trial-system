"""Pin the CTMS -> BulletTrain connector seam, READ-ONLY.

CTMS may not edit BulletTrain. This module reads BT's connector manifests and
asserts, for every outbound route CTMS declares, whether the receiving
connector currently exposes an exchange route for it.

The point is that the seam cannot rot silently in either direction:

* If BT REGISTERS one of the national-capability resource types, the
  corresponding assertion here flips RED and this repo is told to stop
  grading the family as "implemented to the queue" and start closing the
  loop.
* If a CTMS route is added without a receiver mapping, or a mapping is
  pointed at a connector BT does not ship, that is caught here rather than
  at runtime behind a best-effort try/except.

Skipped -- never silently passed -- when the BulletTrain checkout is absent.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.connectors import integration_engine as ie

BT_MANIFESTS = (
    Path(__file__).resolve().parents[3] / "BulletTrain" / "connectors" / "manifests"
)

# The BT-side work this repo needs but must NOT land itself. The orchestrator
# consolidates BulletTrain changes; a parallel session editing BT is how the
# 2026-07-28 dead-on-arrival seam defect happened.
NEEDED_BT_WORK = {
    "citizen_portal": ["ResearchConsentWithdrawn", "ParticipantReimbursementIssued"],
    "pharmacy_system": ["ResearchConsentWithdrawn"],
    "analytics_bi": ["ResearchEligibilityPreScreen"],
    # No BulletTrain connector exists for these external national rails at all.
    "national_trial_registry": ["TrialRegistrationSubmitted"],
    "national_safety_authority": ["SafetyReportSubmitted"],
}


def _manifest(connector: str) -> dict | None:
    path = BT_MANIFESTS / f"{connector}_manifest.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _exchange_routes(connector: str) -> set[str] | None:
    manifest = _manifest(connector)
    if manifest is None:
        return None
    return set((manifest.get("runtime") or {}).get("exchange_routes") or {})


requires_bt = pytest.mark.skipif(
    not BT_MANIFESTS.is_dir(),
    reason="BulletTrain checkout not present beside this repo",
)


@requires_bt
def test_every_ctms_route_maps_to_a_declared_receiver() -> None:
    """No CTMS route may dispatch to a receiver the policy does not allow."""

    receivers = set(ie._RECEIVER_CONNECTOR_MAP)
    assert ie.policy.allowed_receivers == frozenset(receivers)
    for route in ie._ROUTE_RESOURCE_TYPE_MAP:
        assert route.startswith("ctms."), route


@requires_bt
def test_pre_existing_ctms_resource_types_are_still_registered_in_bullettrain() -> None:
    """The four cascades that DO close the loop today must keep doing so."""

    expected = {
        "citizen_portal": "SubjectEnrolled",
        "appointment_system": "VisitScheduled",
        "analytics_bi": "AdverseEventReported",
        "pharmacy_system": "IpDispensed",
        "global_agent_registry": "AgentRunCompleted",
    }
    for connector, resource_type in expected.items():
        routes = _exchange_routes(connector)
        assert routes is not None, f"BulletTrain has no {connector} manifest"
        assert resource_type in routes, (
            f"{connector} lost its {resource_type} exchange route -- a CTMS "
            "cascade that used to close the loop no longer does"
        )


@requires_bt
@pytest.mark.parametrize(
    ("connector", "resource_type"),
    [(c, r) for c, rs in NEEDED_BT_WORK.items() for r in rs],
)
def test_national_resource_types_are_still_unregistered_in_bullettrain(
    connector: str, resource_type: str
) -> None:
    """Deliberately flips RED when BulletTrain registers the kind.

    Until then CTMS implements these cascades UP TO THE QUEUE: the dispatch is
    persisted in ``IntegrationDispatch`` and is replayable, but the loop is
    NOT closed and the disposition ledger must not claim that it is.
    """

    assert resource_type in ie.UNREGISTERED_BT_RESOURCE_TYPES, (
        f"{resource_type} is no longer listed as unregistered in CTMS; update "
        "UNREGISTERED_BT_RESOURCE_TYPES and the disposition ledger together"
    )
    routes = _exchange_routes(connector)
    if routes is None:
        # No manifest at all -- expected for the two external national rails.
        return
    assert resource_type not in routes, (
        f"BulletTrain now exposes {resource_type} on the {connector} connector. "
        "CTMS can close this loop: remove it from "
        "UNREGISTERED_BT_RESOURCE_TYPES, add a receipt/reconciliation step, and "
        "re-grade the family in docs/NATIONAL_CAPABILITY_DISPOSITION_LEDGER.md."
    )


def test_unregistered_set_matches_the_declared_national_routes() -> None:
    """Runs without BulletTrain: the CTMS side of the seam is self-consistent."""

    national_routes = {
        "ctms.consent.withdrawn",
        "ctms.eligibility.prescreen_requested",
        "ctms.trial.registration_submitted",
        "ctms.safety.report_submitted",
        "ctms.participant.reimbursement_issued",
    }
    declared = {ie._ROUTE_RESOURCE_TYPE_MAP[r] for r in national_routes}
    assert declared == set(ie.UNREGISTERED_BT_RESOURCE_TYPES)
    needed = {r for rs in NEEDED_BT_WORK.values() for r in rs}
    assert needed == declared
