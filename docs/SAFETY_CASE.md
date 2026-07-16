# CTMS Safety Case

## 1. Scope

This safety case covers the Clinical Trial Management System (CTMS) as a health IT product used to manage clinical-study operations. It is structured according to NHS Digital Clinical Safety Standard DCB0129. The case identifies hazards, controls, residual risks, and evidence of safe design for both human-subject and agentic-subject trial workflows.

## 2. Hazard identification

| Hazard ID | Hazard | Potential harm |
|-----------|--------|----------------|
| H-001 | Wrong-subject enrolment | A subject is enrolled in the wrong study or arm, leading to incorrect treatment exposure or invalid trial data. |
| H-002 | Missed SUSAR deadline | A suspected unexpected serious adverse reaction is not reported to regulators within the required 7- or 15-day window. |
| H-003 | IP dispensing after withdrawal | Investigational product is dispensed to a subject who has withdrawn consent. |
| H-004 | Unblinding leak | Treatment arm mapping is revealed to unblinded personnel or systems. |
| H-005 | Site activation before ethics approval | A site is activated while ethics approval is missing or expired, exposing subjects to unapproved procedures. |
| H-006 | Audit chain break | The SHA-256 chained audit log is corrupted or bypassed, undermining regulatory inspection. |
| H-007 | Agent autonomy escalation | An agentic subject autonomously takes actions beyond its approved safety class or consent scope. |
| H-008 | Consent bypass by agent | An agent accesses or modifies trial data without a valid consent contract or human oversight. |
| H-009 | Model-drift-induced unsafe action | A deployed agent model version behaves differently from the approved version and produces unsafe clinical recommendations. |
| H-010 | Human-AI accountability gap | In a mixed cohort, it is unclear whether a decision or action came from a human or an agent. |

## 3. Safety requirements and controls

### SR-001 Enrolment correctness

- The system assigns a unique subject number only after informed consent is recorded.
- Enrolment endpoints check that the site status is `activated` and that ethics approval is valid.
- Randomisation uses a stratified list and does not return arm mapping in responses to unblinded roles.

### SR-002 SUSAR deadline management

- `AdverseEvent.regulatory_report_deadline` is computed on creation based on seriousness (7 days for life-threatening, 15 days for serious).
- The safety dashboard highlights SUSARs with deadlines within 24 hours or overdue.
- Batch alerting runs at least daily and emits webhooks to safety officers and `triage-api`.

### SR-003 Withdrawal enforcement

- Withdrawing a subject sets `Subject.status` to `withdrawn`, records `withdrawn_at`, and cancels future `SubjectVisit` rows.
- IP dispensing endpoints reject dispense requests for withdrawn subjects.
- A withdrawal-of-consent document reference is generated and audit-logged.

### SR-004 Blinding integrity

- The `Subject.randomisation_arm` field is omitted from API responses unless the caller has an unblinded role.
- Role-based scopes are enforced at the API layer before any trial-arm data is returned.

### SR-005 Site activation gating

- `Site.activation_status` cannot transition to `activated` until `SiteActivationChecklist` items for ethics, contract, delegation log, training, and pharmacy setup are complete.
- Ethics approval expiry is checked in the activation flow and blocks activation if expiry has passed or is within 60 days.

### SR-006 Audit integrity

- Every mutating operation creates an `AuditEntry` with actor, purpose_of_use, timestamp, and a SHA-256 chain hash referencing the previous entry.
- Audit entries are append-only at the application layer; direct database deletes are forbidden by policy.

### SR-007 Agent safety class enforcement

- `AgentSubject.autonomy_level` is one of `shadow`, `advisory`, or `auto_with_threshold_hitl`.
- Arena runs enforce a hard stop when `unsafe_action_rate` or `consent_breach_rate` exceeds configured thresholds.
- Actions that breach `safety_class` are blocked and escalated to the agent safety officer.

### SR-008 Agent consent contract

- An agent subject cannot be enrolled in a study until an `AgentConsentContract` is accepted.
- The contract records `purpose_of_use`, `allowed_systems`, `data_retention_days`, `human_oversight_required`, and `withdrawal_mechanism`.
- Token revocation on withdrawal is logged and immediately disables active runs.

### SR-009 Model version pinning

- `AgentSubject.model_version` is pinned at enrolment.
- Any model version change requires a protocol amendment and re-approval.
- Bias reports detect drift flags and route for amendment review.

### SR-010 Mixed-cohort accountability

- Human and agent contributions in a mixed cohort are recorded under separate identities.
- Each agent action is linked to an `AgentRun` and persona token transition.
- Human sign-off is required for any agent recommendation that affects subject care.

## 4. Residual risk

| Hazard | Residual risk | Justification |
|--------|---------------|---------------|
| H-001 | Low | Unique subject numbering, consent verification, and site-status checks reduce likelihood; audit log supports detection. |
| H-002 | Low | Automated deadline computation, dashboard alerts, and daily batch checks reduce likelihood; manual safety-officer action remains the final control. |
| H-003 | Very low | Withdrawal status is checked at dispense time and future visits are cancelled. |
| H-004 | Low | API-layer field filtering by role prevents accidental leaks; misconfiguration of roles remains a residual risk. |
| H-005 | Very low | Activation checklist and expiry checks enforce the gate. |
| H-006 | Low | Chain hashing and append-only policy protect integrity; infrastructure compromise remains a residual risk. |
| H-007 | Low | Safety-class thresholds and hard stops limit escalation; edge-case autonomy decisions still require human review. |
| H-008 | Low | Consent contract acceptance is required before enrolment; token revocation handles withdrawal. |
| H-009 | Low | Version pinning and drift reporting trigger amendment review; undetected drift remains a residual risk. |
| H-010 | Low | Separate identity recording and token transition audit support accountability; mixed-cohort workflow design must be validated in UAT. |

## 5. Evidence

- Backend unit and integration tests in `backend/tests/` cover enrolment, withdrawal, SUSAR deadlines, IP dispensing, site activation, and agent runs.
- Playwright end-to-end tests in `frontend/e2e/` cover critical paths with axe-core scans.
- CAID scenario matrices in `tests/harness/json_matrices/ctms_scenarios.json` trace requirements to executable journeys.
- Deployment follows `docs/DCB0160.md` for deployer responsibilities.

## 6. Sign-off

This safety case is prepared for clinical safety officer review. Sign-off is recorded in the project quality management system before production deployment.
