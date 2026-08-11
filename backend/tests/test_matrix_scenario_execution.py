"""Execute canonical-matrix scenarios against the REAL seeded CTMS app.

Why this module exists
---------------------
Every other consumer of ``tests/harness/json_matrices/ctms_scenarios.json``
validates *shape*: that a row carries the canonical columns, that the file holds
100 rows, that the Positive/Negative/Edge split is 85/10/5. None of them
dispatched ``trigger.api`` or evaluated ``expected_outputs``.

That is how 100 rows sat green while every one of them was a synthesized filler
row pointed at ``POST /api/ctms`` -- a path that is not a route in this
application at all. A shape check cannot tell the difference between a scenario
and a well-formed lie about one.

This module closes that gap. It boots the real ASGI app against a freshly
seeded database, dispatches each row's declared HTTP request with path and body
tokens resolved from ids that exist in THIS seed run, and asserts the observed
status matches the status recorded in ``expected_outputs.http_status``.

The recorded statuses were obtained by execution, not asserted a priori. Ten
rows are tagged ``requirement-unmet`` and carry a ``defect_reference``: for
those the recorded status documents a proven defect rather than a satisfied
requirement, so a future fix is expected to BREAK this test -- that is the
point. See the matrix ``metadata.replacement.defects_recorded``.

A row opts in by carrying ``EXECUTION_MARKER`` in ``validation_rules``. Rows
without it are reported as unexecuted rather than skipped silently, so the count
of un-proven rows stays visible.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient

MATRIX_DIR = Path(__file__).resolve().parents[2] / "tests" / "harness" / "json_matrices"
EXECUTION_MARKER = "executed by backend/tests/test_matrix_scenario_execution.py"


def _load_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (executable_rows, unexecuted_rows) across every scenario matrix."""
    executable: list[dict[str, Any]] = []
    unexecuted: list[dict[str, Any]] = []
    for path in sorted(MATRIX_DIR.glob("*_scenarios.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("scenarios", []):
            if not isinstance(row, dict):
                continue
            entry = {"matrix": path.name, "row": row}
            rules = row.get("validation_rules") or []
            if any(EXECUTION_MARKER in str(r) for r in rules):
                executable.append(entry)
            else:
                unexecuted.append(entry)
    return executable, unexecuted


EXECUTABLE, UNEXECUTED = _load_rows()


class _Resolver:
    """Resolve ``{token}`` placeholders from ids that exist in THIS seed run.

    Path templates in the matrix are stable across seed runs; the ids are not.
    Resolving live -- rather than baking ids into the matrix -- is what keeps the
    rows executable after a reseed.
    """

    def __init__(self, client: AsyncClient) -> None:
        self.c = client
        self.cache: dict[str, Any] = {}

    async def _first(self, path: str, where=None, field: str = "id") -> Any:
        r = await self.c.get(path)
        assert r.status_code == 200, f"resolver: GET {path} -> {r.status_code}"
        rows = r.json()
        assert isinstance(rows, list), f"resolver: GET {path} did not return a list"
        if where:
            rows = [x for x in rows if where(x)]
        assert rows, f"resolver: GET {path} yielded no match"
        return rows[0][field]

    async def get(self, token: str) -> Any:
        if token in self.cache:
            return self.cache[token]
        if token in ("study", "draft_study", "audit_study", "fhir_study"):
            used = {self.cache.get(k) for k in ("draft_study", "audit_study")}
            if token == "study":
                value = await self._first("/api/v1/studies")
            elif token == "fhir_study":
                # Cannot filter on the FHIR field: schemas.StudyOut omits it
                # entirely (defect CTMS-FHIR-001 -- the payload is write-only), so
                # it never appears in a listing. Resolve by the protocol number the
                # NFR-C-CO-001 write row uses instead.
                value = await self._first(
                    "/api/v1/studies",
                    where=lambda s: s.get("protocol_number") == "SX-CTMS-FHIR-CO001",
                )
            else:
                value = await self._first(
                    "/api/v1/studies",
                    where=lambda s: s.get("status") == "draft" and s["id"] not in used,
                )
        elif token in ("site", "new_site"):
            value = await self._first(
                "/api/v1/sites",
                where=(
                    (lambda s: s.get("activation_status") == "activated")
                    if token == "site"
                    else None
                ),
            )
        elif token in ("subject", "new_subject", "withdraw_subject", "rand_subject"):
            used = {
                self.cache.get(k)
                for k in ("subject", "withdraw_subject", "rand_subject")
            }
            value = await self._first(
                "/api/v1/subjects",
                where=lambda s: s.get("enrolment_status") == "enrolled"
                and (token == "subject" or s["id"] not in used),
            )
        elif token in ("nat_subject", "nat_withdraw_subject"):
            # National-capability rows need enrolled subjects that no earlier
            # row has already put into a terminal state. Kept in a separate
            # branch (rather than widened into the one above) so the existing
            # rows keep resolving to exactly the ids they resolved to before.
            used = {
                self.cache.get(k)
                for k in (
                    "subject",
                    "new_subject",
                    "withdraw_subject",
                    "rand_subject",
                    "nat_subject",
                    "nat_withdraw_subject",
                )
            }
            study = await self.get("study")
            value = await self._first(
                f"/api/v1/subjects?study_id={study}",
                where=lambda s: s.get("enrolment_status") == "enrolled"
                and s["id"] not in used,
            )
        elif token == "unrandomised_subject":
            value = await self._first(
                "/api/v1/subjects",
                where=lambda s: s.get("randomisation_arm") is None
                and s.get("enrolment_status") == "screening",
            )
        elif token == "ie_study":
            value = await self._first(
                "/api/v1/studies", where=lambda s: s.get("jurisdiction") == "IE"
            )
        elif token == "ie_site":
            ie_study = await self.get("ie_study")
            value = await self._first(f"/api/v1/sites?study_id={ie_study}")
        elif token == "new_registration":
            study = await self.get("study")
            value = await self._latest(f"/api/v1/trial-registrations?study_id={study}")
        elif token == "new_approval":
            study = await self.get("study")
            value = await self._latest(f"/api/v1/regulatory-approvals?study_id={study}")
        elif token == "new_screening":
            study = await self.get("study")
            value = await self._latest(f"/api/v1/eligibility-screenings?study_id={study}")
        elif token == "nat_ae":
            value = await self._latest("/api/v1/adverse-events")
        elif token == "new_submission":
            ae = await self.get("nat_ae")
            value = await self._latest(f"/api/v1/adverse-events/{ae}/safety-submissions")
        elif token == "new_reimbursement":
            subject = await self.get("subject")
            r = await self.c.get(f"/api/v1/participants/{subject}/summary")
            assert r.status_code == 200, f"resolver: participant summary -> {r.status_code}"
            rows = r.json()["reimbursements"]
            assert rows, "resolver: subject has no reimbursement"
            value = max(x["id"] for x in rows)
        elif token in ("visit", "new_visit"):
            value = await self._first_visit()
        elif token == "query":
            value = await self._first("/api/v1/queries")
        elif token in ("agent", "new_agent"):
            # Highest id, not first: the seeded agents 1-3 already hold a consent
            # contract, and a duplicate POST raises an unhandled IntegrityError
            # (defect CTMS-AGT-001) that poisons the session. The agent registered
            # by the FR-C-A11 row -- which runs earlier in matrix order -- is the
            # one FR-C-A12 is written against.
            r = await self.c.get("/api/v1/agents/subjects")
            assert r.status_code == 200, f"resolver: agents -> {r.status_code}"
            agents = r.json()
            assert agents, "resolver: no agent subjects seeded"
            value = max(a["id"] for a in agents)
        elif token in ("new_ae",):
            value = await self._first("/api/v1/adverse-events")
        elif token in ("product", "new_shipment", "new_budget"):
            # Inventory, shipment and budget ids are created by earlier rows in
            # the same matrix; id 1 always exists from the seed for each.
            value = 1
        elif token == "task":
            site = await self.get("new_site")
            r = await self.c.get(f"/api/v1/sites/{site}/checklist")
            rows = r.json() if r.status_code == 200 else []
            assert rows, "resolver: site checklist is empty"
            value = rows[0].get("task_name") or rows[0].get("name")
        else:
            pytest.fail(f"resolver: no rule for token {token!r}")
        self.cache[token] = value
        return value

    async def _latest(self, path: str) -> Any:
        """Highest id in a collection -- the row an earlier scenario just made."""

        r = await self.c.get(path)
        assert r.status_code == 200, f"resolver: GET {path} -> {r.status_code}"
        rows = r.json()
        assert rows, f"resolver: GET {path} returned no rows"
        return max(x["id"] for x in rows)

    async def _first_visit(self) -> int:
        for probe in range(1, 80):
            r = await self.c.get(f"/api/v1/visits/{probe}")
            if r.status_code == 200:
                return probe
        pytest.fail("resolver: no visit found in the seeded range")
        raise AssertionError  # unreachable, keeps type checkers happy

    async def sub_str(self, text: str) -> str:
        out = text
        while "{" in out and "}" in out:
            start = out.index("{")
            end = out.index("}", start)
            out = out[:start] + str(await self.get(out[start + 1 : end])) + out[end + 1 :]
        return out

    async def sub(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: await self.sub(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [await self.sub(v) for v in obj]
        if isinstance(obj, str) and obj.startswith("{") and obj.endswith("}"):
            return await self.get(obj[1:-1])
        return obj


@pytest.mark.asyncio
async def test_matrix_rows_execute_against_the_real_app(
    seeded_client: AsyncClient,
) -> None:
    """Dispatch every opted-in row and compare observed status to the record."""
    if not EXECUTABLE:
        pytest.fail("no executable scenario rows present -- the matrix lost its marker")

    resolver = _Resolver(seeded_client)
    failures: list[str] = []
    fixed: list[str] = []
    executed = 0
    blocked = 0

    for entry in EXECUTABLE:
        row = entry["row"]
        uid = row.get("use_case_id")
        payload = row.get("input_payload") or {}
        method = (payload.get("method") or "GET").upper()
        expected = (row.get("expected_outputs") or {}).get("http_status")
        defect = row.get("blocked_on_defect")

        path = await resolver.sub_str(payload.get("path") or "")
        request: dict[str, Any] = {"params": await resolver.sub(payload.get("query") or {})}
        if method in {"POST", "PUT", "PATCH"}:
            request["json"] = await resolver.sub(payload.get("body") or {})

        try:
            response = await seeded_client.request(method, path, **request)
        except Exception as exc:  # noqa: BLE001 - report, never mask
            failures.append(f"{entry['matrix']}::{uid} {method} {path} raised {exc!r}")
            continue

        executed += 1
        matched = response.status_code == expected

        if defect:
            # This row's expectation is what the REQUIREMENT demands, not what the
            # code currently does: the scenario and the requirement agree and the
            # code is the outlier. It is asserted to STILL FAIL. When the defect is
            # fixed the row starts matching, and THAT is what we report -- so a fix
            # can never pass silently while the row still claims to be blocked.
            blocked += 1
            if matched:
                fixed.append(
                    f"{entry['matrix']}::{uid} {method} {path} now returns the "
                    f"required {expected}: defect {defect} appears FIXED -- remove "
                    f"blocked_on_defect from this row so it becomes live coverage"
                )
            continue

        if not matched:
            failures.append(
                f"{entry['matrix']}::{uid} {method} {path} "
                f"expected {expected}, observed {response.status_code} "
                f"({response.text[:120]!r})"
            )

    print(
        f"\nexecuted {executed} rows; {blocked} held at the requirement's expectation "
        f"pending a code fix (blocked_on_defect)."
    )
    assert executed == len(EXECUTABLE), f"only {executed}/{len(EXECUTABLE)} dispatched"
    assert not fixed, (
        f"{len(fixed)} blocked-on-defect row(s) now satisfy their requirement:\n"
        + "\n".join(fixed)
    )
    assert not failures, (
        f"{len(failures)}/{len(EXECUTABLE)} matrix rows did not match observed "
        "behaviour:\n" + "\n".join(failures[:40])
    )


def _registered_operations() -> set[tuple[str, str]]:
    """Every (METHOD, path-template) the app actually serves.

    Enumerated from the OpenAPI document, NOT from ``app.routes``. FastAPI
    0.139 changed ``include_router`` to append a lazy ``_IncludedRouter``
    wrapper instead of flattening the sub-router's routes into the parent's
    ``routes`` list, so ``app.routes`` now yields only the 6 top-level routes
    (``/``, ``/docs``, ``/redoc``, ``/openapi.json``, ...) and none of the 70+
    API operations. Walking ``app.routes`` therefore reported EVERY matrix row
    as targeting a non-existent route -- 100 false positives on a clean tree.
    The OpenAPI document is the public, version-stable projection of the same
    routing table.
    """

    spec = _app().openapi()
    return {
        (method.upper(), path)
        for path, operations in spec["paths"].items()
        for method in operations
    }


def _app() -> Any:
    from app.main import app

    return app


def test_route_enumeration_sees_the_real_routing_table() -> None:
    """Known-true control for :func:`_registered_operations`.

    Without this, a future framework change that empties the enumeration
    would turn every row into a false offender again (or, with the assertion
    inverted, would let a phantom path through unnoticed). Anchoring on
    operations that are unambiguously registered makes the instrument itself
    testable.
    """

    registered = _registered_operations()
    for anchor in (
        ("POST", "/api/v1/studies"),
        ("GET", "/api/v1/subjects/{subject_id}"),
        ("POST", "/api/v1/adverse-events"),
    ):
        assert anchor in registered, (
            f"route enumeration lost {anchor}; it reports only "
            f"{len(registered)} operation(s) -- the enumeration is broken, "
            "not the matrix"
        )
    assert len(registered) > 50, (
        f"route enumeration returned only {len(registered)} operations; "
        "this application serves far more"
    )


def test_no_row_targets_a_route_that_does_not_exist() -> None:
    """Every declared path must map to a registered route.

    This is the check whose absence let 100 rows point at ``POST /api/ctms``.
    """

    registered = _registered_operations()

    offenders: list[str] = []
    for entry in EXECUTABLE + UNEXECUTED:
        row = entry["row"]
        payload = row.get("input_payload") or {}
        method = (payload.get("method") or "GET").upper()
        template = payload.get("path") or ""
        # Compare against route templates with the matrix's token names mapped
        # onto FastAPI's own parameter names by position.
        matched = any(
            verb == method and _same_shape(template, route_path)
            for verb, route_path in registered
        )
        if not matched:
            offenders.append(f"{row.get('use_case_id')}: {method} {template}")

    assert not offenders, (
        f"{len(offenders)} matrix rows target a path with no registered route:\n"
        + "\n".join(offenders[:20])
    )


def _same_shape(matrix_path: str, route_path: str) -> bool:
    """True iff a matrix path is an instance of a route template.

    A route's ``{param}`` segment matches ANY single matrix segment -- the matrix
    legitimately carries both token placeholders (``{study}``, resolved at
    execution) and hardcoded literals (``999999``, the deliberate absent-id
    probes in the negative rows). Only non-parameter route segments must match
    literally.
    """
    m = matrix_path.strip("/").split("/")
    r = route_path.strip("/").split("/")
    if len(m) != len(r):
        return False
    return all(
        (seg_r.startswith("{") and seg_r.endswith("}")) or seg_r == seg_m
        for seg_m, seg_r in zip(m, r, strict=False)
    )


def test_no_synthesized_filler_rows_remain() -> None:
    """No row may exist purely to satisfy the 85/10/5 distribution."""
    offenders: list[str] = []
    for path in sorted(MATRIX_DIR.glob("*.json")):
        blob = path.read_text(encoding="utf-8")
        if "synthesized for 85/10/5" in blob or "synthesised for 85/10/5" in blob:
            offenders.append(path.name)
    assert not offenders, f"synthesized filler rows remain in: {offenders}"


def test_unexecuted_row_count_is_reported() -> None:
    """Surface how much of the corpus is still un-proven by execution."""
    total = len(EXECUTABLE) + len(UNEXECUTED)
    print(
        f"\nmatrix execution coverage: {len(EXECUTABLE)}/{total} rows dispatched "
        f"against the real app; {len(UNEXECUTED)} rows remain schema-only."
    )
    assert total > 0
