# National Capability Disposition Ledger — clinical-trial-system

**Wave:** 4 (Symphonix national-capability programme)
**Audit under implementation:** `docs/national-capability-audit.md` (intake copy of
`symphonix-assurance/reports/national-capability/pack/audits/clinical-trial-system-national-capability-audit.md`)
**Implemented:** 2026-08-05
**Provisional intake prefix:** `REQ-CTS-NAT-00N` — **aliases only**. They appear in this
ledger and nowhere else in the repository, so no gate can scrape them into a phantom
requirement obligation.

---

## 1. Native ID scheme and alias mapping

The repository's true requirements source is `docs/REQUIREMENTS.md`, rendered into
`tests/harness/requirements_superset.json` and
`tests/harness/requirements_matrix.json`. Its native scheme is `FR-C-<section><n>`
(numeric families `11..14`, `21..24`, … `101..106`, plus the agentic `A11..A45`
families) with `NFR-C-<XX>-00N` for non-functional requirements.

Maximum numeric family before this wave: **`FR-C-106`** (§2.14 BulletTrain onboarding).
New requirements therefore continue at **`FR-C-111`**, not at the provisional
`REQ-CTS-NAT-*` alias. De-duplicated against `docs/REQUIREMENTS.md`,
`requirements_superset.json`, `requirements_matrix.json`, `derived_nfrs.json` and
`matrix_config.toml` before allocation — no collision.

| Provisional alias | Native IDs landed | Doc section |
|---|---|---|
| `REQ-CTS-NAT-001` Study/site registry | `FR-C-111`, `FR-C-112`, `FR-C-113`, `FR-C-114` | §2.15 |
| `REQ-CTS-NAT-002` Ethics/regulatory pack | `FR-C-121`, `FR-C-122`, `FR-C-123`, `FR-C-124` | §2.16 |
| `REQ-CTS-NAT-003` Eligibility service | `FR-C-131`, `FR-C-132`, `FR-C-133` | §2.17 |
| `REQ-CTS-NAT-004` Consent lifecycle | `FR-C-141`, `FR-C-142`, `FR-C-143`, `FR-C-144`, `FR-C-145` | §2.18 |
| `REQ-CTS-NAT-005` Randomisation/blinding | `FR-C-151`, `FR-C-152`, `FR-C-153`, `FR-C-154` | §2.19 |
| `REQ-CTS-NAT-006` Safety reporting | `FR-C-161`, `FR-C-162`, `FR-C-163`, `FR-C-164` | §2.20 |
| `REQ-CTS-NAT-007` Investigational product | `FR-C-171`, `FR-C-172` | §2.21 |
| `REQ-CTS-NAT-008` Participant portal | `FR-C-181`, `FR-C-182`, `FR-C-183` | §2.22 |
| (cross-cutting, added by this session) Country packs | `FR-C-191`, `FR-C-192` | §2.23 |

31 new functional requirements; catalogue 37 → 68.

---

## 2. Per-family dispositions (verified against live code, not the audit's claims)

Every disposition below was graded by reading the code at `HEAD` before any change.
The audit's own dispositions were **wrong or incomplete for 6 of 8 families**.

### REQ-CTS-NAT-001 — Study/site registry · audit said `RETAIN-AS-OWNER` · **verdict: `partial` → EXTENDED**

**Already present.** `Study` (`backend/app/models.py:102`), `ProtocolVersion`
(`models.py:127`), `Site` (`models.py:141`), `SiteActivationChecklist`
(`models.py:160`), routes in `backend/app/api/v1/endpoints/studies.py` and
`sites.py`, activation checklist generated on site creation
(`backend/app/crud.py:153`).

**Absent.** No national/public registry identity of any kind — no registry code,
no registry identifier, no submission state, no acknowledgement; no sponsor legal
entity; no investigator delegation log (the checklist has a `delegation_log`
*task name* at `crud.py:153` but no delegation records behind it); no GCP
credential expiry.

**Built.** `TrialRegistration` + `InvestigatorDelegation` (`models.py`, national
tables block), `national.submit_trial_registration` /
`record_registration_receipt` / `create_investigator_delegation` /
`list_investigator_delegations` / `site_readiness` (`backend/app/national.py`),
routes in `backend/app/api/v1/endpoints/national.py`. Registration reaches
`registered` **only** on an acknowledgement whose identifier matches the
jurisdiction pack's pattern.

### REQ-CTS-NAT-002 — Ethics/regulatory pack · audit said `BUILD-NEW` · **verdict: `partial` → EXTENDED**

**Already present.** `RegulatoryDocument` (`models.py:311` pre-change),
create/list CRUD (`crud.py`), eTMF completeness report (`crud.etmf_report`),
expiry data seeded (`backend/app/seeding/data.py` `REGULATORY_DOCUMENTS`).

**Absent.** Documents, not *submissions*: no submission type, no decision, no
decider, no conditions, no renewal or annual-report clock. Nothing to build
"BUILD-NEW" over — the document half already existed, so building as specified
would have duplicated it.

**Built.** `RegulatoryApproval` model, `national.create_regulatory_approval` /
`record_approval_decision` / `approvals_due`. `decided_by` is mandatory,
`approved_with_conditions` requires at least one condition, and a terminal
decision cannot be overwritten (409).

### REQ-CTS-NAT-003 — Eligibility service · audit said `HUB-CONSUME` · **verdict: `missing` → BUILT**

**Evidence of absence.** `rg -i "eligib|inclusion|exclusion|prescreen"` over
`backend/app` returned only two report counters (`crud.py` `screen_failed`) and
two seed deviation categories. `crud.create_subject` (`crud.py:202`) stores
demographics and nothing else.

**This also falsifies an existing requirement.** `FR-C-31` states the system
"checks inclusion/exclusion criteria and produces `eligible`, `ineligible`, or
`pending_review`". No such code existed and `Subject` had no field to hold the
verdict — a fully traceable requirement with zero implementing code.

**Built.** `EligibilityScreening` model, `national.request_eligibility_screening`
(hub dispatch, criteria + pseudonymous reference only) and
`record_eligibility_outcome` (outcome **derived** from the verdicts, never
accepted from the caller; a partial evaluation is refused).

### REQ-CTS-NAT-004 — Consent lifecycle · audit said `BUILD-NEW` · **verdict: `partial` → EXTENDED + DEFECT FIXED**

**Already present.** `InformedConsent` (`models.py:191` pre-change) with
`withdrawn_at`/`withdrawal_reason`; `crud.record_consent`;
`crud.withdraw_subject`, which already cancelled scheduled visits.

**Absent, and load-bearing.** `crud.create_ip_dispense` (pre-change, `crud.py`)
looked up the product and decremented stock — it never loaded the subject and
never consulted consent. A subject who had withdrawn consent could still be
dispensed investigational product through `POST /api/v1/ip/dispenses`. **This is
a real defect, not a documentation gap**: `FR-C-33` already required that
subjects not re-consented are "suspended from further IP dispensing", and
`FR-C-34` already required withdrawal handling. Also absent: consent type,
protocol version, assent/proxy, witness, future-use scope, and any propagation
of the withdrawal to a sibling.

**Built/fixed.** `Subject.consent_state` + `consent_withdrawn_at`; extended
`InformedConsent`; `crud.flag_reconsent_required`; `crud.withdraw_subject` now
sets the state and fans the withdrawal out through the hub to **both**
citizen-portal and pharmacy-system
(`integration_engine.notify_consent_withdrawn`); `crud.create_ip_dispense`
refuses `withdrawn` and `re_consent_required` with 422; `national.participant_summary`
stops offering upcoming visits for a withdrawn participant.
Regression tests: `backend/tests/test_national_capability.py::test_withdrawal_reaches_dispensing_visits_and_the_participant_surface`,
matrix rows `ctms_NAT_NEG_0009`, `ctms_NAT_NEG_0010`, `ctms_NAT_POS_0021/0022`.

### REQ-CTS-NAT-005 — Randomisation/blinding · audit said `BUILD-NEW` · **verdict: `code-only shell` → REPLACED**

**What existed.** A route that did the randomisation itself:

```python
# backend/app/api/v1/endpoints/subjects.py (pre-change)
import random
arm = random.choice(["arm_a", "arm_b"])
```

and `crud.randomise_subject`, which assigned whatever arm it was handed. No
allocation list, no stratification (the factors were stored but never used), no
blinding, no audit entry, no unblinding path at all.

**This falsifies two more existing requirements.** `FR-C-35` claims the system
"can randomise a subject in a two-arm **double-blind** study to a **stratified**
arm without revealing treatment mapping"; `FR-C-A14` claims the same for agent
subjects. Neither stratification nor blinding existed.

**Built.** `RandomisationAllocation` + `UnblindingEvent` models;
`crud.ensure_allocation_list` (deterministic permuted blocks seeded on
`protocol_number:stratum`), `crud.randomise_subject` (consumes the next free
slot, writes an audit entry, refuses an exhausted list with 409),
`crud.unblind_subject` (named authoriser, self-authorisation flagged),
`GET /subjects/{id}/allocation` (kit code only).

### REQ-CTS-NAT-006 — Safety reporting · audit said `BUILD-NEW` · **verdict: `partial` → EXTENDED + 2 DEFECTS FIXED**

**Already present.** `AdverseEvent` (`models.py:221` pre-change), deadline
computation, SUSAR flag, hub dispatch to analytics-bi
(`integration_engine.notify_adverse_event`), safety dashboard
(`crud.safety_report`).

**Defect 1 — the statutory clock was wrong.**

```python
# backend/app/crud.py (pre-change)
if seriousness in ("serious", "life_threatening", "fatal"):
    days = 7 if seriousness == "serious" else 1
```

`serious` → 7 days, `life_threatening`/`fatal` → **1 day**. `FR-C-61` itself says
"7- or 15-day", and ICH E2A / EU CTR 536/2014 Art. 42 / 21 CFR 312.32(c) all say
7 days for fatal or life-threatening SUSARs and 15 days for other SUSARs. Every
seeded and live deadline was wrong in both directions.

**Defect 2 — the SUSAR test was missing a limb and excluded the worst class.**

```python
computed_susar = obj_in.seriousness == "life_threatening" and obj_in.causality in {"related", "possibly_related"}
```

No `expectedness` (the "U" in SUSAR) existed anywhere in the model, and the
grade test matched `life_threatening` **only** — so a **fatal**, related,
unexpected reaction was never auto-flagged as a SUSAR.

**Fixed/built.** `AdverseEvent.expectedness` / `.jurisdiction` /
`.deadline_basis`; `country_packs.loader.is_susar` (all three ICH E2A limbs) and
`susar_deadline_days` (day counts from the pack); `SafetySubmission` model with
`national.submit_safety_report` / `record_safety_acknowledgement` /
`overdue_safety_submissions`. A report is `submitted` until an acknowledgement
arrives — dispatch is never treated as completion.
Regression tests: `test_national_capability.py::test_fatal_unexpected_related_is_a_seven_day_susar`
(all four jurisdictions), `::test_adverse_event_records_the_deadline_basis`,
`::test_overdue_safety_submission_is_reported`.

### REQ-CTS-NAT-007 — Investigational product · audit said `HUB-CONSUME` · **verdict: `partial` → EXTENDED + DEFECT FIXED**

**Already present.** `InvestigationalProduct`, `IpShipment`, `IpDispense`
(`models.py:254-293` pre-change), receipt/dispense/destroy CRUD, accountability
report (`crud.ip_accountability_report`), and a hub cascade
(`integration_engine.notify_ip_dispensed`).

**Defect 3 — the hub cascade was only wired on the INBOUND path.**
`notify_ip_dispensed` was called from
`backend/app/connectors/inbound_processors.py:145` (the pharmacy webhook) but
**not** from `crud.create_ip_dispense`. A dispense recorded in CTMS itself never
reached the hub, so `FR-C-72` ("notifies pharmacy-system / eps") held for the
echo path only.

**Defect 4 (pre-recorded as CTMS-IP-001, now fixed).** `create_ip_dispense`
subtracted without a sufficiency check, so a dispense of 100 000 against 200 on
hand drove `quantity_on_hand` to −100 000 and made the `FR-C-74` identity
(`shipped − dispensed − returned − destroyed = on-hand`) unsatisfiable.

**Fixed.** Sufficiency guard (422) and outbound notification added to
`crud.create_ip_dispense`. Matrix row `ctms_EDG_0003` moved off
`blocked_on_defect` and is now live coverage of the refusal.

### REQ-CTS-NAT-008 — Participant portal · audit said `MIGRATE-SURFACE` · **verdict: `missing (contract side)` → BUILT (backend contract only)**

**Already present.** One cascade to citizen-portal on enrolment
(`integration_engine.notify_subject_enrolled`, BT route `SubjectEnrolled`).

**Absent.** No participant-facing contract of any kind: no visit/consent/results
projection, and no reimbursement concept anywhere in the repo.

**Built.** `ParticipantReimbursement` model, `national.create_reimbursement` /
`approve_reimbursement` / `participant_summary`, `GET
/participants/{id}/summary`. Currency and per-visit guidance cap come from the
study's country pack; over-cap payments are flagged, not silently allowed or
silently blocked; approval requires a named human.

**Deliberately NOT built here:** the participant UI. `MIGRATE-SURFACE` places the
user-facing workflow in `citizen-portal`, and CTMS stays the canonical owner of
the state (benchmark rule 1). See REMAINING §6.

---

## 3. Country packs (versioned data, benchmark rule 4)

`backend/app/country_packs/packs/{ie,uk,ke,us}.json`, loaded and **validated** by
`backend/app/country_packs/loader.py`. Each pack declares `schema_version`,
`pack_version`, `effective_from`, `review_due` and official `sources` with access
dates. A pack that omits a statutory section fails to load rather than silently
removing a deadline (`test_missing_statutory_section_fails_loading`).

| Jurisdiction | Competent authority | Ethics | Registry (identifier) | SUSAR clock | Notable delta |
|---|---|---|---|---|---|
| **IE** (default) | HPRA (via CTIS) | NREC-CT | CTIS EU trial number | 7 / 15 d | EU CTR 536/2014; assent < 18 |
| UK | MHRA (via IRAS) | HRA-REC | ISRCTN | 7 / 15 d | age of majority 16; consultee roles |
| KE | PPB | NACOSTI-accredited ERC **+ NACOSTI licence** | PACTR | 7 / 15 d | Swahili translation; council registration |
| US | FDA (IND) | IRB | ClinicalTrials.gov NCT | 7 / 15 d | HIPAA authorisation; Form FDA 1572; results within 365 d |

Ireland is the operating jurisdiction: the seeded paediatric vaccine study runs at
Irish sites under the IE pack, and `DEFAULT_JURISDICTION = "IE"`.

---

## 4. Alignment surfaces registered (measured, not asserted)

Every surface was re-measured with a before/after set-diff after registration.
Counts are `git show HEAD:<path>` versus the working tree.

| Surface | Before | After | New IDs present |
|---|---|---|---|
| `docs/REQUIREMENTS.md` (FR rows) | 0 of the 31 | 31 of 31 | §2.15–§2.23 |
| `tests/harness/requirements_superset.json` | 37 requirements | 68 | 31 |
| `tests/harness/requirements_matrix.json` | 37 requirements | 68 | 31 |
| `tests/harness/matrix_config.toml` (`framework_to_requirements`) | 42 ids | 73 | 31 |
| `tests/harness/json_matrices/ctms_scenarios.json` | 100 rows | 149 | 49 rows citing all 31 |
| `tests/harness/reduced_json_matrices/ctms_matrix.14col.json` | 19 rows | 28 | 9 rows citing all 31 + AC ids |
| `requirements_superset.json` acceptance criteria | 0 for these ids | 31 `-AC01` entries | 31 |
| Seed traceability (`backend/app/seed.py` `CAID-SEED-REQ`) | 0 | 6 blocks citing national ids | `FR-C-111..114`, `121..123`, `131..132`, `141`, `161`, `171`, `182..183` |
| `backend/tests/` (executing coverage) | — | +47 tests | national + seam suites |

---

## 5. Defects discovered and fixed (all with a regression test)

| # | Defect | Where | Regression test |
|---|---|---|---|
| D1 | **Repo's own route-existence gate was RED on clean `main`, reporting 100 false offenders.** FastAPI 0.139 changed `include_router` to append a lazy `_IncludedRouter` instead of flattening sub-router routes into `app.routes`, so the gate saw 6 top-level routes and none of the 70+ API operations. | `backend/tests/test_matrix_scenario_execution.py` | `test_route_enumeration_sees_the_real_routing_table` (known-true control; proven to fail when the enumeration is reverted to `app.routes`) |
| D2 | SUSAR statutory deadline: `life_threatening`/`fatal` → **1 day** instead of 7; contradicted `FR-C-61` and ICH E2A / EU CTR / 21 CFR 312.32(c). | `backend/app/crud.py::_compute_susar_deadline` | `test_fatal_unexpected_related_is_a_seven_day_susar` (× 4 jurisdictions) |
| D3 | SUSAR determination omitted **expectedness** and matched `life_threatening` only, so a **fatal** related unexpected reaction was never flagged. | `backend/app/crud.py::create_adverse_event` | `test_adverse_event_records_the_deadline_basis`, matrix `ctms_NAT_POS_0026` |
| D4 | **Consent withdrawal did not propagate**: `create_ip_dispense` never loaded the subject, so a withdrawn subject could still be dispensed IP. | `backend/app/crud.py::create_ip_dispense` | `test_withdrawal_reaches_dispensing_visits_and_the_participant_surface`, matrix `ctms_NAT_NEG_0010` |
| D5 | CTMS-initiated dispense never notified the hub — `notify_ip_dispensed` was called only from the inbound pharmacy webhook. | `backend/app/crud.py` vs `connectors/inbound_processors.py:145` | matrix `ctms_NAT_POS_0017` (declares the connector call) |
| D6 | **CTMS-IP-001** (already recorded, now fixed): dispensing more than on-hand drove inventory negative. | `backend/app/crud.py::create_ip_dispense` | matrix `ctms_EDG_0003`, now live coverage; `CTMS-UC-028` asserts the balance |
| D7 | Randomisation was `random.choice` in the route handler — unreproducible, unstratified, unaudited, despite `FR-C-35` declaring stratified double-blind. | `backend/app/api/v1/endpoints/subjects.py` | `test_allocation_list_is_deterministic_and_balanced`, `test_allocation_exhaustion_is_refused_not_reused` |
| D8 | **3 of 19 14-column rows had no runner** (`CTMS-UC-009/010/011`) and had therefore never executed. `_case_ids()` silently skips runner-less rows. `CTMS-UC-011` also carried an assertion — `'actual_enrolled' in response.json()` — that could never have passed, because `schemas.RecruitmentReport` has no such field. `CTMS-UC-009` named two non-existent callables in `dependencies`. | `backend/tests/test_matrix_harness.py`, `ctms_matrix.14col.json` | `test_every_14col_row_has_an_executing_runner` (new gate that found it), plus three real runners |
| D9 | A subject could be "unblinded" against an arm no allocation list ever assigned (seeded arms were written straight onto the row). | `backend/app/crud.py::unblind_subject` | matrix `ctms_NAT_EDG_0002`; seeder now binds historic arms to real allocation slots |

### Defects recorded but **NOT** fixed in this wave (unchanged, still `blocked_on_defect`)

`CTMS-SEC-001` (no authentication layer), `CTMS-SEC-002` (no RBAC),
`CTMS-VAL-001` / `CTMS-VAL-002` (enum values accepted verbatim),
`CTMS-FIN-001` / `CTMS-FIN-002` (negative money accepted),
`CTMS-RPT-001` (eTMF report for a non-existent study returns 200),
`CTMS-FHIR-001` (FHIR payload write-only), `CTMS-OBS-001`.
9 rows remain held at their requirement's expectation. **Because CTMS-SEC-001/002
are open, the blinding requirement is only partially enforceable**: there is no
role to blind against, so `SubjectOut.randomisation_arm` is still readable by any
caller. The blinded read (`GET /subjects/{id}/allocation`) and the audited
unblinding path exist; role-based suppression does not. Graded honestly as
partial, not closed.

---

## 6. REMAINING (explicitly not done)

1. **Participant UI.** No frontend file was touched. The participant workflow is
   `MIGRATE-SURFACE` to citizen-portal, which must consume
   `GET /api/v1/participants/{id}/summary` and the reimbursement endpoints. No
   headed-browser or SignalBox evidence was produced, because no frontend source
   changed and the L-340 pre-push gate is therefore not engaged.
2. **Closed loops that stop at the queue.** Five national cascades are
   implemented up to the `IntegrationDispatch` queue and are **not** closed
   loops — BulletTrain has no exchange route for them. See §7. Receipt handling
   exists on the CTMS side for registry and safety (both have explicit
   acknowledgement endpoints), so the loop closes as soon as BT registers the
   kinds.
3. **Blinding enforcement** — blocked on `CTMS-SEC-001`/`CTMS-SEC-002` (above).
4. **Agent-subject randomisation (`FR-C-A14`)** still uses the legacy path; the
   allocation-list model is not yet applied to `AgentTrialArm`.
5. **Eligibility ingestion from a real sibling.** The hub request is dispatched
   and the outcome endpoint is real, but no sibling currently answers
   `ResearchEligibilityPreScreen`; outcomes are recorded through the CTMS
   endpoint.
6. **Seeding Alignment Gate.** See §8 — resolution was repaired repo-side, but
   the gate's verdict is reported honestly rather than claimed as a pass.
7. **Allocation concurrency.** `crud.randomise_subject` selects the next free
   slot with a plain `SELECT ... LIMIT 1` and no row lock. Under genuinely
   concurrent randomisation two callers could contend for one slot. Adequate
   for the single-writer SQLite deployment this repo ships, NOT adequate for a
   multi-writer production database; a `SELECT ... FOR UPDATE SKIP LOCKED` (or
   an equivalent advisory lock) is required before that.
8. **Re-submission of an already-registered trial** overwrites the registry
   identifier on the next acknowledgement rather than treating it as an
   amendment with its own history. Acceptable for the amendment flow as
   modelled; a registry-side version history is not implemented.

---

## 7. BulletTrain-side work required (NOT landed here — read-only)

BulletTrain's connector manifests were read read-only. The following exchange
routes do not exist, so the corresponding CTMS dispatches queue locally and the
family is graded "implemented to the queue", never "closed loop":

| BT connector | Resource type needed | CTMS route |
|---|---|---|
| `citizen_portal` | `ResearchConsentWithdrawn` | `ctms.consent.withdrawn` |
| `citizen_portal` | `ParticipantReimbursementIssued` | `ctms.participant.reimbursement_issued` |
| `pharmacy_system` | `ResearchConsentWithdrawn` | `ctms.consent.withdrawn` |
| `analytics_bi` | `ResearchEligibilityPreScreen` | `ctms.eligibility.prescreen_requested` |
| *(no manifest at all)* `national_trial_registry` | `TrialRegistrationSubmitted` | `ctms.trial.registration_submitted` |
| *(no manifest at all)* `national_safety_authority` | `SafetyReportSubmitted` | `ctms.safety.report_submitted` |

`backend/tests/test_bt_connector_seam.py` pins this read-only and **flips RED**
the moment BulletTrain registers any of them, so the seam cannot rot silently.
It also pins the five cascades that DO close today (`SubjectEnrolled`,
`VisitScheduled`, `AdverseEventReported`, `IpDispensed`, `AgentRunCompleted`).

---

## 7b. Matrix-integrity cluster splits (advisory, acknowledged)

`caid matrix-integrity` reports **6 cluster splits** — rows whose single piece of
executable substance is bound to two requirement ids. Ten were reported on the
first draft; four were removed by narrowing the binding to the requirement each
row's assertions actually discriminate (`ctms_NAT_POS_0002`, `_0015`, `_0020`,
`_0021`, `_0022`, `ctms_NAT_NEG_0010`, and all nine 14-column rows). The six
that remain are single API calls that genuinely constitute the whole obligation
for both ids and were kept deliberately rather than split into near-duplicate
rows, which would have been padding:

* `ctms_NAT_POS_0012` — `FR-C-122` + `FR-C-123`: one decision call both requires
  the named decider and derives the expiry/next-report clocks.
* `ctms_NAT_POS_0023` — `FR-C-151` + `FR-C-152`: the first randomisation of a
  stratum both generates the list and consumes a slot from it.
* `ctms_NAT_POS_0026` — `FR-C-161` + `FR-C-162`: one POST both applies the
  three-limb SUSAR test and the pack's clock.
* `ctms_EDG_0003` — `FR-C-72` + `FR-C-171`: kept dual-bound so `FR-C-72` does
  not lose an atom (see the rekey in `matrix-integrity-ledger.json`).
* two further pairs of the same shape.

The gate reports these; it does not fail on them. Levers `padded` and
`undefined` are both **0**, and `unbound` fell from the baseline's 19 to 16
because three previously runner-less 14-column rows gained real bindings.

## 8. Seeding Alignment Gate — honest grading

On clean `HEAD` the gate returned **`decision=BLOCKED`, rationale "Required
artefact(s) missing: seed"** — for a repo with a 300-line working seeder. The
cause is not this repo's seed: caid-agent's `discover_seed()` has no candidate
matching `backend/app/seeding/loader.py`. Its ranked candidates include
`backend/app/seed.py` and `backend/app/seed`, but the package here is named
`seeding` and the callable lives in `loader.py`, so **nothing matched and the
gate failed closed**. Every seeding verdict this repo has ever recorded was
measured against no file at all.

**Repaired repo-side, without creating a duplicate.** The implementation moved to
`backend/app/seed.py` (`seed_all`, `seed_database`), and
`backend/app/seeding/loader.py` is now an explicit re-export shim holding no copy
of the data. `backend/app/main.py` and `backend/tests/conftest.py` import paths
are unchanged. This deliberately avoids the estate's stale-duplicate defect
class, where a `backend/seed.py` copy exists only to satisfy the gate and then
rots away from the file the application runs.

Seed annotations (`# CAID-SEED-REQ:`) sit **immediately above** the constructor
they describe, which is the only position the gate's annotation walker sees.
A second parser constraint had to be met as well: caid's `CTOR_RE` /
`EMBEDDED_CTOR_RE` match a **bare** `ClassName(` only, so
`db.add(models.InformedConsent(...))` parsed as zero seed records even once the
file was found. The ORM classes are therefore imported by name and constructed
bare, and the two private helpers were renamed `seed_national_records` /
`seed_agentic_records` so their constructors fall inside a span
`_seed_function_spans` actually walks (it enters only top-level `seed_*` /
`main` functions).

### Measured verdicts (same caid build, `92cd008`, both runs)

| Tree | Decision | Rows | Blocking | missing_seed | partial_seeding |
|---|---|---|---|---|---|
| clean `HEAD` (`git archive` export) | **BLOCKED** — "Required artefact(s) missing: seed" | 134 | 77 | 34 | 43 |
| first draft of this change | FAIL | 195 | 93 | **42** | 51 |
| this change (aliases removed) | **FAIL** — real alignment findings | 187 | 85 | **34** | 51 |

The middle row is kept deliberately. The first draft put the provisional
`REQ-CTS-NAT-00N` alias in the `docs/REQUIREMENTS.md` section headings, and the
gate — which scrapes that file for requirement ids with a regex that matches
`REQ-`-prefixed ids — turned all eight into **phantom requirement obligations**
with no spec, no use case and no seed. That is the exact alias-leakage failure
the wave lessons warn about, and it was caught by *measuring* the gate's own
matrix rather than by asserting the aliases were confined. Removing them from
`REQUIREMENTS.md` and from `backend/app/seed.py` took the row count 195 → 187
and `missing_seed` 42 → **34, identical to clean `HEAD`** — i.e. the 31 real new
requirements added no net missing-seed rows.

**This is an improvement, not a regression, and it is NOT a pass.** At `HEAD`
the gate could not see a seeder at all, so its 134 rows were graded against
nothing; it now parses 7 seed records, every one of them carrying declared
requirement ids. The remaining `missing_seed` rows are a genuine, largely
pre-existing backlog: most CTMS requirements — including 17 of the 31 landed
here — are *behavioural* (a refusal, a propagation, a receipt) and have no
seed-shaped row to bind to. 14 of the 31 national requirements do have seed
records and are bound (7 parsed seed records, every one carrying declared
requirement ids). Closing the rest is out of this wave's scope and is recorded
in REMAINING rather than claimed.

---

## 9. Verification summary

* `backend/tests/` — full suite green (see the commit message for counts),
  including 37 new national-capability tests, 9 connector-seam tests and 2 new
  matrix meta-gates.
* All **149** canonical scenario rows dispatch against the real seeded ASGI app;
  all **28** 14-column rows now have an executing runner.
* Negative control performed for D1 (reverted the fix, watched the new control
  test fail, restored).
* `caid matrix-integrity` — REPORT / exit 0 (`padded=0 undefined=0`, atom
  carried forward by rekey, 0 last-atom losses).
* `caid coverage-shrink` — PASS, "No requirement lost scenario coverage"
  (100 → 167 scenarios compared across both matrix files).
* `ruff` — the repo's lint step was **already failing on clean `HEAD`** with the
  installed ruff (267 findings, dominated by `B008` `Depends()`-in-defaults,
  which is the repo's universal FastAPI idiom, plus `UP042`/`E501`). This change
  takes it to 295; every added finding is in a category already present at
  `HEAD`, and all five newly added modules were separately checked. No
  repo-wide style churn was attempted.
* Gate results, and the gates that were NOT run, are recorded in the session
  report accompanying this landing.
