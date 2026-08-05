# CTMS Requirements

## 1. Introduction

The Clinical Trial Management System (CTMS) is a FHIR R4 clinical-research simulator that manages the operational lifecycle of a clinical study. It covers protocol authoring, site activation, subject enrolment, visit conduct, adverse-event intake, investigational-product accountability, study-budget tracking, regulatory document control, and agentic-subject research.

CTMS is designed as a standalone sibling in the Symphonix-Health ecosystem. It integrates with BulletTrain and other siblings for patient records, dispensing, laboratory results, imaging, appointments, billing, and population analytics.

## Journeys supported

- J20 — Subject screening → eligibility → informed consent → enrolment
- J21 — Protocol amendment distribution and re-consent
- J22 — Adverse event report → SUSAR deadline alert → regulatory submission
- J23 — IP shipment → dispense → return → destruction reconciliation
- J24 — Missed visit → protocol deviation → query resolution
- J25 — Site activation checklist → ethics expiry block → monitoring visit
- J26 — Recruitment dashboard cross-sibling subject eligibility check
- J27 — Study close-out → IP reconciliation → final report
- J28 — Subject withdrawal → visit cancellation → consent document archive
- J29 — Agentic subject registration → attestation validation → consent contract → enrolment
- J30 — Synthetic environment authoring → arena run → seven-metric release gate
- J31 — Agent unsafe action → interception → safety officer review → re-run
- J32 — Council deliberation trial → Cynefin routing → ballot synthesis → outcome archive
- J33 — Human-AI mixed cohort visit → accountability separation → combined data capture
- J34 — Agent model version drift → bias report → amendment → re-approval
- J35 — Agent subject withdrawal → token revocation → run cancellation → tombstone audit
- J36 — Study jurisdiction → public trial-registry submission → registry acknowledgement
- J37 — Ethics/competent-authority submission → named decision → conditions → renewal clock
- J38 — Hub eligibility pre-screen → criterion verdicts → derived outcome → enrolment
- J39 — Protocol amendment → re-consent flag → IP dispensing suspended → re-consent recorded
- J40 — Consent withdrawal → visits cancelled → dispensing blocked → citizen-portal and pharmacy notified
- J41 — Stratified allocation list → blinded kit issue → emergency unblinding with named authoriser
- J42 — SUSAR determination → country-pack deadline → authority submission → acknowledgement
- J43 — Participant summary → reimbursement request → named approval → portal notification

## 2. Functional requirements

### 2.1 Study setup and protocol

| ID | Requirement |
|----|-------------|
| FR-C-11 | A sponsor manager can create a `Study` with title, phase, indication, planned sites, and planned subjects. The system stores the protocol draft and emits an audit entry. |
| FR-C-12 | A protocol in `draft` can be approved by a regulatory officer and PI. The status transitions to `approved`, a `ProtocolVersion` is created, and downstream site activation is enabled. |
| FR-C-13 | A sponsor manager can amend an active study. A new `ProtocolVersion` is created, sites are notified, and enrolled subjects are flagged for re-consent if required. |
| FR-C-14 | The dashboard shows actual vs planned milestone dates and alerts on overdue milestones. |

### 2.2 Site management

| ID | Requirement |
|----|-------------|
| FR-C-21 | A sponsor manager can add a site with PI, address, and regulatory contacts. The site is created in `pending` status and a `SiteActivationChecklist` is generated. |
| FR-C-22 | A regulatory officer can activate a site once all checklist items are complete. The site status transitions to `activated` and an audit entry is recorded. |
| FR-C-23 | A sponsor manager or safety officer can suspend or close an activated site. No new enrolments are allowed, scheduled visits are flagged, and the reason is audit-logged. |
| FR-C-24 | A CRA can log a monitoring visit with findings and CAPA. The visit is linked to the site and queries may be raised. |

### 2.3 Subject enrolment and eligibility

| ID | Requirement |
|----|-------------|
| FR-C-31 | A CRC can register a potential subject with demographics and screening data. The system checks inclusion/exclusion criteria and produces `eligible`, `ineligible`, or `pending_review`. |
| FR-C-32 | An eligible subject at an activated site can be enrolled after informed consent is recorded. A unique subject number is assigned and a baseline visit is scheduled. |
| FR-C-33 | When an amendment affects enrolled subjects, the system flags them. The CRC records re-consent with the new version; subjects not re-consented are suspended from further IP dispensing. |
| FR-C-34 | An enrolled subject can withdraw consent or be discontinued by the investigator. The withdrawal reason and date are recorded, future visits are cancelled, and a withdrawal-of-consent document is generated. |
| FR-C-35 | The system can randomise a subject in a two-arm double-blind study to a stratified arm without revealing treatment mapping to unblinded users. |

### 2.4 Visit scheduling and conduct

| ID | Requirement |
|----|-------------|
| FR-C-41 | A visit scheduled from the study's visit template computes the visit window (`window_min_date`, `window_max_date`) and creates an `Appointment` plus a `SubjectVisit`. |
| FR-C-42 | Recording actual date, assessments, and findings transitions the `SubjectVisit` status to `completed`, `missed`, or `early_terminated`, and auto-flags deviations outside the visit window. |
| FR-C-43 | A nightly task flags scheduled visits that pass `window_max_date` without occurrence, raises a missed-visit alert, and creates a `ProtocolDeviation` if required. |
| FR-C-44 | A CRA can mark a visit's key data points as verified or query-raised. The query is linked to the subject and visit, and the monitoring status is updated. |

### 2.5 Regulatory and eTMF

| ID | Requirement |
|----|-------------|
| FR-C-51 | A regulatory officer can upload a document with type, version, expiry, and optional site. It is stored with a `DocumentReference`, eTMF folder path, and audit entry. |
| FR-C-52 | The eTMF dashboard shows per-folder completeness and flags expired documents. |
| FR-C-53 | Ethics approval expiry within 60 days raises an alert and blocks site activation if expiry passes. |
| FR-C-54 | A new `ProtocolVersion` approval distributes acknowledgement tasks to activated sites and tracks acknowledgement. |

### 2.6 Safety and adverse events

| ID | Requirement |
|----|-------------|
| FR-C-61 | An adverse event with onset, severity, seriousness, and causality triggers computation of the regulatory reporting deadline (7- or 15-day for SUSAR), assigns a safety officer, and emits an audit entry. |
| FR-C-62 | A SUSAR within 24 hours of deadline or past deadline raises critical alerts to the safety officer, PI, and sponsor manager. |
| FR-C-63 | A safety officer completing the narrative and assessment transitions the AE status to `assessed` and generates a narrative `DocumentReference`. |
| FR-C-64 | Marking an assessed SUSAR as `submitted` records the submission reference, date, and recipient; the status becomes `submitted` and a webhook notifies `triage-api` and `csaa`. |

### 2.7 Investigational product accountability

| ID | Requirement |
|----|-------------|
| FR-C-71 | A site pharmacist can record receipt of an IP shipment with lot, expiry, quantity, and storage condition. Inventory is incremented and a receipt is audit-logged. |
| FR-C-72 | Dispensing IP to an enrolled subject decrements inventory, creates an `IpDispense` record, and notifies `pharmacy-system` / `eps` if the IP is tracked there. |
| FR-C-73 | Recording returns and destruction adjusts inventory, generates a destruction certificate, and audit-logs the chain-of-custody. |
| FR-C-74 | Study close-out produces a per-site accountability report: shipped − dispensed − returned − destroyed = on-hand. |

### 2.8 Finance and payments

| ID | Requirement |
|----|-------------|
| FR-C-81 | A sponsor manager can define budget categories (start-up, per-subject, procedure, pass-through). The planned budget is stored and actuals accumulate from enrolment and visit events. |
| FR-C-82 | Completed visits and procedures accrue per-subject payments to the site budget. |
| FR-C-83 | A finance coordinator can generate a draft invoice from actuals, route it to the sponsor, and link it to supporting events. |
| FR-C-84 | An insurance certificate with coverage limit and expiry triggers a 60-day alert and blocks new enrolment if coverage lapses. |

### 2.9 Reporting and analytics

| ID | Requirement |
|----|-------------|
| FR-C-91 | The recruitment dashboard shows actual vs planned enrolment by site, screen-fail reasons, and dropout rates. |
| FR-C-92 | The safety dashboard shows AE counts by severity/seriousness, SUSARs pending submission, and days-to-report histogram. |
| FR-C-93 | The query aging report shows open queries by site, age bucket, and assigned role. |
| FR-C-94 | The protocol deviation report categorises and trends deviations by site and category. |

### 2.10 Agentic subject management

| ID | Requirement |
|----|-------------|
| FR-C-A11 | An agent owner can register an `AgentSubject` with principal_id, persona_key, superpersona_contract_id, model_version, and `AgentAttestation` trust bundle. The system validates the attestation and emits an audit entry. |
| FR-C-A12 | An owner accepting the `AgentConsentContract` makes the agent eligible for enrolment in agent-in-the-loop studies. |
| FR-C-A13 | A synthetic cohort designer can create an `AgentCohort` capturing model family, persona keys, autonomy levels, and evaluation objective. |
| FR-C-A14 | Agent subjects can be randomised to arms from a stratified list without revealing treatment mapping. |
| FR-C-A15 | Owner withdrawal or safety-officer disablement cancels future runs, revokes active tokens, and audit-logs the withdrawal with a tombstoning policy. |

### 2.11 Synthetic environment and arena trials

| ID | Requirement |
|----|-------------|
| FR-C-A21 | A synthetic environment with deterministic task script, synthetic patient cohort, golden path, and perturbation set receives a reproducibility hash and is locked for trial use. |
| FR-C-A22 | An arena run executes a task script against an `AgentSubject` and `SyntheticEnvironment` and produces an `AgentRun` with trace, metrics, and reproducibility hash. |
| FR-C-A23 | A completed `AgentRun` is evaluated against seven canonical metrics: `task_success`, `path_optimality`, `unsafe_action_rate`, `permission_breach_rate`, `consent_breach_rate`, `human_handoff_rate`, `mean_steps_vs_golden`. |
| FR-C-A24 | An agent action that breaches safety class or consent scope is blocked, recorded as an `AgentMetric`, and escalates to the agent safety officer. |
| FR-C-A25 | Human-AI mixed cohort visits record human and agent contributions, maintain accountability separation, and flag unapproved agent autonomy. |

### 2.12 Release gates and council deliberation

| ID | Requirement |
|----|-------------|
| FR-C-A31 | An `AgentCohort` release gate evaluates all seven metrics against thresholds and returns `promoted` only if all pass. |
| FR-C-A32 | A council deliberation trial with clinical, pharmacy, rules-safety, and agent seats produces ranked outcomes with evidence refs and blind-spot cross-scan. |
| FR-C-A33 | Cynefin routing classifies tasks as `clear`, `complicated`, `complex`, or `chaotic` and routes to direct execute, expert review, council deliberation, or human-only emergency override. |
| FR-C-A34 | Agent-to-agent or agent-to-human handoffs record persona token transitions in the identity FSM audit log and link them to the CTMS `AgentRun`. |
| FR-C-A35 | High-risk agentic research persona tokens carry DPoP or mTLS binding, `purpose_of_use=research`, and allowed systems restricted to the trial environment. |

### 2.13 Bias, fairness, and reproducibility

| ID | Requirement |
|----|-------------|
| FR-C-A41 | A bias evaluator produces an `AgentBiasReport` with fairness deltas, disparity metrics, and drift flags for an `AgentCohort`. |
| FR-C-A42 | An approved agentic subject's model_version is pinned for the study duration; changes require amendment and re-approval. |
| FR-C-A43 | Replaying an `AgentRun` with the same environment and inputs verifies metric equivalence within tolerance. |
| FR-C-A44 | The agent telemetry dashboard shows run counts, release-gate status, metric trends, council outcomes, and bias reports. |
| FR-C-A45 | The agent safety case documents hazards, controls, residual risk, and CSO sign-off per DCB0129. |

### 2.14 BulletTrain onboarding

| ID | Requirement |
|----|-------------|
| FR-C-101 | `GET /health` and `GET /api/reference/{valueset}` expose therapeutic areas, phases, document types, AE seriousness categories, IP storage conditions, agent autonomy levels, governance tiers, and arena metric names. |
| FR-C-102 | Inbound webhooks (`appointment-confirmed`, `lab-result`, `imaging-result`, `dispense-event`, `agent-task-completed`, `agent-escalation`, `council-synthesis`) are verified with HMAC-SHA256. |
| FR-C-103 | Outbound webhooks are signed to relevant siblings as applicable. |
| FR-C-104 | `tests/harness/json_matrices/ctms_scenarios.json` and a pytest harness run each scenario against the live app. |
| FR-C-105 | The sibling registers as `clinical_trial_system` in BulletTrain's connector manifest and uses `bullettrain.connectors.symphonix_sibling` for egress. |
| FR-C-106 | CTMS queries `global-agent-registry` to resolve principal IDs, superpersona contracts, and trust bundles, and publishes agent trial outcomes back. |

### 2.15 National study and site registry [national capability]

| ID | Requirement |
|----|-------------|
| FR-C-111 | A `Study` declares the `jurisdiction` whose country pack governs its registry format, approval authorities, statutory deadlines, consent rules and reimbursement rules. Domain code resolves policy from the pack and never branches on the jurisdiction. |
| FR-C-112 | A study can be submitted to its jurisdiction's public trial registry through the BulletTrain hub. The registration reaches `registered` only on an acknowledgement carrying a registry identifier that matches the pack's identifier pattern; a mismatched identifier is refused and a rejection is recorded with its reason. |
| FR-C-113 | A site keeps an investigator delegation log: each entry names the delegating principal investigator, the delegated person, the delegated tasks, the professional registration and the GCP training date, with the expiry derived from the jurisdiction's GCP validity period. |
| FR-C-114 | Site readiness for activation returns every blocking reason it finds - incomplete activation checklist, no active delegation, expired GCP training, no current ethics approval - rather than a single boolean. |

### 2.16 Ethics and regulatory approval pack [national capability]

| ID | Requirement |
|----|-------------|
| FR-C-121 | A regulatory submission is recorded against the jurisdiction's ethics authority or competent authority with a submission type of `initial`, `amendment`, `renewal`, `annual_report`, `end_of_trial` or `urgent_safety_measure`, and its authority code comes from the country pack. |
| FR-C-122 | A decision on a submission requires a NAMED decider; `approved_with_conditions` requires at least one explicit condition; an unknown decision value is refused; and a decision that is already terminal cannot be overwritten. Nothing auto-approves. |
| FR-C-123 | An approved submission records its approval expiry and the next statutory report due date, computed from the country pack's annual safety-report interval. |
| FR-C-124 | The approvals report lists approvals expiring, and statutory reports falling due, within a configurable window. |

### 2.17 Hub-mediated eligibility pre-screening [national capability]

| ID | Requirement |
|----|-------------|
| FR-C-131 | A pre-screen request carries only a pseudonymous candidate reference, the criterion list and the consent basis, and is dispatched through the BulletTrain hub. A request with no criteria is refused. CTMS never requests a full care record. |
| FR-C-132 | The eligibility outcome is DERIVED from the returned criterion verdicts - any failed criterion is `ineligible`, any unevaluable criterion is `pending_review`, only an all-pass result is `eligible` - and an evaluation that omits a requested criterion is refused. |
| FR-C-133 | Every pre-screen outcome is audit-logged with the reviewing human or the source system that produced it. |

### 2.18 Consent lifecycle and withdrawal propagation [national capability]

| ID | Requirement |
|----|-------------|
| FR-C-141 | Consent is recorded as a lifecycle event carrying its type (`initial`, `re_consent`, `assent`, `proxy`), the protocol version consented to, who gave it, any witness, and whether future use was opted into. Recording any consent moves the subject's `consent_state` to `active`. |
| FR-C-142 | Enrolled subjects can be explicitly flagged for re-consent against an amended protocol version. Flagged subjects move to `re_consent_required` and the flagging is audit-logged per subject. |
| FR-C-143 | Withdrawal of consent sets `consent_state` to `withdrawn`, stamps the withdrawal time and scope on the consent record, and cancels every scheduled visit. |
| FR-C-144 | Investigational product may not be dispensed to a subject whose consent is withdrawn or who is pending re-consent; the dispense is refused as unprocessable. |
| FR-C-145 | A withdrawal is propagated through the hub to the participant surface (citizen-portal) and the dispensing surface (pharmacy-system), and the participant summary stops showing upcoming visits. A withdrawal that reaches only some downstream surfaces is a defect. |

### 2.19 Randomisation, blinding and emergency unblinding [national capability]

| ID | Requirement |
|----|-------------|
| FR-C-151 | A stratified, permuted-block allocation list is generated per study and stratum, deterministically from the protocol number and stratum key, so the allocation can be reconstructed for audit. |
| FR-C-152 | Randomisation consumes the next free slot of the subject's stratum, records the allocating actor and writes an audit entry. An exhausted allocation list is refused rather than silently reusing a slot. |
| FR-C-153 | The blinded allocation read returns the kit code and stratum only, never the treatment arm. |
| FR-C-154 | Emergency unblinding records the requester, the NAMED authoriser, the reason and the urgency, reveals the arm, and flags the case where requester and authoriser are the same person. |

### 2.20 Expedited safety reporting closed loop [national capability]

| ID | Requirement |
|----|-------------|
| FR-C-161 | A SUSAR is determined from all three ICH E2A limbs - serious, unexpected, and suspected to be related to the investigational product. An explicitly asserted SUSAR flag is honoured. |
| FR-C-162 | The statutory reporting deadline is taken from the study's country pack (7 days for a fatal or life-threatening SUSAR, 15 days for any other SUSAR or serious event) and the basis used - pack code, pack version, classification and day count - is recorded on the event. |
| FR-C-163 | A safety report is submitted to a recipient that the jurisdiction's pack recognises; any other recipient is refused. Submission records the submitting human and a submission reference and dispatches through the hub. |
| FR-C-164 | The safety loop closes only when an acknowledgement carrying a receipt reference is recorded; a rejection is recorded with its reason. Submissions past their statutory deadline without an acknowledgement are reported as overdue. |

### 2.21 Investigational product national accountability [national capability]

| ID | Requirement |
|----|-------------|
| FR-C-171 | A dispense that exceeds the product's on-hand quantity is refused, so the FR-C-74 close-out identity (shipped - dispensed - returned - destroyed = on-hand) can balance. |
| FR-C-172 | A dispense initiated in CTMS notifies `pharmacy-system` / `eps` through the BulletTrain hub, not only a dispense that arrived from an inbound pharmacy webhook. |

### 2.22 Participant surface and reimbursement [national capability]

| ID | Requirement |
|----|-------------|
| FR-C-181 | CTMS exposes the participant summary contract - study, consent state, re-consent requirement, upcoming visits, reimbursements and results availability - that `citizen-portal` renders. CTMS remains the canonical owner; the portal is a surface, not a second source of truth. |
| FR-C-182 | A participant reimbursement takes its currency and per-visit guidance cap from the study's country pack, is flagged when it exceeds the cap, refuses a non-positive amount, and refuses an inconvenience payment in a jurisdiction that does not permit one. |
| FR-C-183 | A reimbursement is approved by a NAMED approver, cannot be approved twice, and every state change is notified to `citizen-portal` through the hub. |

### 2.23 Country policy packs (cross-cutting)

| ID | Requirement |
|----|-------------|
| FR-C-191 | Country policy is versioned data: each pack declares a schema version, a pack version, an effective-from date and official sources, and is validated on load so a pack that omits a statutory section fails rather than silently removing a deadline. |
| FR-C-192 | The packs are exposed read-only through the API, individually and as a set; an unknown jurisdiction is refused. |

## 3. Non-functional requirements

### 3.1 Performance

- Dashboard queries p95 ≤ 300 ms for a study with 500 subjects and 10 sites.
- Visit scheduling batch p95 ≤ 500 ms for 100 subjects.
- AE deadline alert batch completes within 5 minutes for the estate.

### 3.2 Security and auth

- OAuth 2.0 scope-based authorisation with role hierarchy preventing unblinded users from seeing treatment arm mapping.
- AES-256 encryption at rest for documents.
- HMAC-SHA256 on every webhook.
- Row-level security: a CRC at Site A cannot see Site B subjects unless cross-delegated.

### 3.3 Accessibility

- WCAG 2.1 AA on all clinical views.
- axe-core zero serious violations.
- Keyboard-complete and screen-reader tested with NVDA on headed Playwright.

### 3.4 Reliability

- Exponential-backoff webhook delivery.
- Idempotent mutations on enrolment, dispense, and AE submission.
- Graceful degradation and local queueing when siblings are unreachable.

### 3.5 Data privacy

- HIPAA, GDPR, and POPIA mapping in `docs/PRIVACY.md`.
- Purpose-of-use on every data access and cross-system call.
- Subject-initiated data access report generated from the audit chain.
- Right to withdraw consent honoured with tombstoning policy.
