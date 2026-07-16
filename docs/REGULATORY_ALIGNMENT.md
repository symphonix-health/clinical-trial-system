# CTMS Regulatory Alignment

## 1. ICH-GCP E6(R2)

CTMS implements the following ICH-GCP requirements:

- **Protocol control**: `Study`, `ProtocolVersion`, and status transitions enforce protocol approval before site activation and enrolment.
- **Informed consent**: `InformedConsent` records version, date, withdrawal, and reason; withdrawal blocks further IP dispensing and visits.
- **Investigator oversight**: Site activation requires ethics, contract, training, and pharmacy checklist completion.
- **Safety reporting**: `AdverseEvent` captures onset, severity, seriousness, causality, and computes SUSAR deadlines.
- **Source data verification**: Visit monitoring status and query linkage support CRA verification workflows.
- **Audit trail**: `AuditEntry` provides a SHA-256 chained, append-only log of all mutations with actor and purpose.

## 2. FDA 21 CFR Part 11

CTMS supports an electronic records and signatures posture:

- **Validation**: The system is validated through automated tests, scenario matrices, and documented deployment procedures.
- **Audit trail**: Each record modification creates an `AuditEntry` with timestamp, actor, and prior value reference.
- **Record retention**: Records are retained in the database with backups; retention periods follow sponsor and regulatory policy.
- **Access control**: OAuth 2.0 scopes and roles restrict access to authorised personnel.
- **Electronic signatures**: Signature events are recorded as `AuditEntry` rows with a signature reference. Full Part 11 compliance requires integration with a qualified e-signature provider; CTMS provides the audit hooks and role enforcement.

## 3. EU CTR Regulation (EU) No 536/2014

CTMS supports EU clinical trial workflows:

- Ethics approval tracking with expiry alerts.
- Protocol version management and amendment distribution.
- Subject information and consent records.
- Serious adverse event reporting deadlines.
- eTMF folder structure for regulatory documents.

## 4. NHS / HRA UK workflows

CTMS maps to UK clinical trial toolkit practices:

- Site activation checklist aligned with HRA approval and NHS R&D requirements.
- Subject eligibility and consent recording.
- Safety reporting and SUSAR tracking.
- DCB0129 safety case in `docs/SAFETY_CASE.md`.

## 5. CDISC and FHIR R4

CTMS uses FHIR R4 as its cross-system wire format:

- `ResearchStudy` for protocol metadata.
- `ResearchSubject` for enrolment.
- `Encounter` for visits.
- `AdverseEvent` for safety events.
- `Observation` for assessments.
- `MedicationDispense` for IP dispensing.
- `DocumentReference` for regulatory documents and narratives.
- `Task` for queries and acknowledgements.
- `Schedule` and `Appointment` for visit scheduling.

CDISC FHIR mapping guidance is used when translating CTMS data to SDTM-compatible datasets for regulatory submission.

## 6. Electronic signature posture

CTMS records signature intent through authenticated API calls and audit entries. The system is designed to integrate with a Part 11-compliant electronic signature service. Until that integration is active, signature events are captured as immutable audit records with actor identity and timestamp.
