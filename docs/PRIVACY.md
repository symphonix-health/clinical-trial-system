# CTMS Privacy Statement

## 1. Scope

This document maps CTMS data handling to HIPAA, GDPR, and POPIA requirements. It covers personal data collected for human subjects, agent owners, and trial personnel; cross-system transfers; retention; and subject rights.

## 2. Data categories

| Category | Examples | Legal basis |
|----------|----------|-------------|
| Subject identifiers | screening_id, enrolment_id, date of birth, sex | Trial consent / legitimate interest in research |
| Contact data | address, phone, emergency contact | Trial consent |
| Health data | adverse events, visit assessments, IP dispensing | Trial consent / public interest in clinical research |
| Genetic or special-category data | biomarkers, stratification factors | Explicit consent where collected |
| Trial personnel data | PI, CRC, safety officer identities | Contract / employment necessity |
| Agent metadata | principal_id, persona_key, model_version, owner_id | Consent of agent owner / legitimate interest in evaluating agent behaviour |
| Audit data | actor, purpose_of_use, timestamps, chain hash | Legal obligation and legitimate interest in integrity |

## 3. Principles

### 3.1 Purpose limitation

CTMS collects and processes data only for the purpose of managing the clinical trial and evaluating agentic subjects in that trial. Every cross-system call carries a `purpose_of_use` value.

### 3.2 Data minimisation

Demographic and health data are limited to what the protocol requires. Pseudonymous identifiers (`screening_id`, `enrolment_id`) are used where possible.

### 3.3 Accuracy

Subjects and personnel can request correction of inaccurate personal data. Corrections are audit-logged with the previous and new values.

### 3.4 Storage limitation

Personal data is retained for the period required by the protocol, sponsor policy, and applicable law. After the retention period, data is pseudonymised or deleted according to the documented tombstoning policy.

### 3.5 Integrity and confidentiality

Data at rest is encrypted with AES-256. Data in transit uses TLS 1.2 or higher. Access is controlled by OAuth 2.0 scopes and row-level security.

## 4. Subject rights

| Right | CTMS mechanism |
|-------|----------------|
| Access | Subject-initiated data access report generated from the audit chain and subject record. |
| Rectification | `PATCH` endpoints on subject and personnel records with audit logging. |
| Erasure | Withdrawal triggers tombstoning; direct deletion is blocked for regulatory retention but pseudonymisation is applied. |
| Restriction | Site suspension and role changes restrict processing. |
| Data portability | FHIR R4 exports of `ResearchStudy`, `ResearchSubject`, `Encounter`, and `AdverseEvent` resources. |
| Objection | Withdrawal of consent stops further IP dispensing and future visits. |

## 5. Cross-system transfers

Transfers to BulletTrain siblings occur only under the following conditions:

- A valid OAuth 2.0 token or HMAC-signed webhook is present.
- The `purpose_of_use` field is populated.
- The recipient system is listed in the subject's consent or the agent's consent contract.
- Webhook payloads exclude unnecessary personal data.

Recipient siblings include `provider-portal`, `pharmacy-system`, `eps`, `appointment-system`, `analytics-bi`, `citizen-portal`, `csaa`, `triage-api`, `global-agent-registry`, `nexus-a2a-protocol`, `symphonix-bridge-sdk`, and `signalbox-mcp`.

## 6. Jurisdiction mapping

### HIPAA

CTMS implements access controls, audit logging, encryption, and minimum necessary access. Business associate agreements are required for any downstream recipient handling PHI.

### GDPR

CTMS supports consent withdrawal, data subject access requests, purpose limitation, and retention limits. A record of processing activity is maintained by the sponsor.

### POPIA

CTMS implements reasonable technical and organisational measures to secure personal information. Data subject requests are handled through the same access and rectification endpoints.

## 7. Tombstoning policy

On subject withdrawal:

1. Future visits are cancelled.
2. No further IP is dispensed.
3. Direct identifiers are masked in non-regulatory views.
4. Audit entries and trial-record data required by law are retained with a withdrawal flag.
5. After the regulatory retention period, data is deleted or fully anonymised.
