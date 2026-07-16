# CTMS Research Foundation

## 1. Standards and guidelines

CTMS is designed against the following standards and regulatory sources:

- ICH E6(R2) Good Clinical Practice: https://database.ich.org/sites/default/files/E6_R2_Addendum.pdf
- FDA 21 CFR Part 11: https://www.ecfr.gov/current/title-21/part-11
- EU CTR Regulation (EU) No 536/2014: https://eur-lex.europa.eu/eli/reg/2014/536
- NHS/HRA UK clinical trial toolkit: https://www.hra.nhs.uk/planning-and-improving-research/research-planning/clinical-trials-toolkit/
- CDISC FHIR mapping guidance for ResearchStudy / ResearchSubject: https://www.cdisc.org/fhir
- EU AI Act (Regulation (EU) 2024/1689) high-risk AI system requirements: https://eur-lex.europa.eu/eli/reg/2024/1689
- MHRA guidance on software and AI as a medical device: https://www.gov.uk/government/collections/software-and-ai-as-a-medical-device
- IEEE 2857-2023 Privacy Engineering for Entity Disambiguation: https://standards.ieee.org/standard/2857-2023.html
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework

## 2. Clinical trial lifecycle model

CTMS models the lifecycle as a state machine:

```
draft → approved → recruiting → active → suspended → completed → closed
```

Each transition is guarded by checklist completion, approval records, and audit entries. Site activation follows a similar state machine:

```
pending → activated → suspended → closed
```

Subject enrolment follows:

```
screening → enrolled → completed / early_terminated / withdrawn
```

## 3. FHIR R4 mapping

| CTMS entity | FHIR R4 resource |
|-------------|------------------|
| Study | ResearchStudy |
| Subject | ResearchSubject |
| SubjectVisit | Encounter + Appointment |
| AdverseEvent | AdverseEvent |
| InvestigationalProduct | Medication |
| IpDispense | MedicationDispense |
| RegulatoryDocument | DocumentReference |
| Query | Task |
| AuditEntry | Provenance |
| AgentSubject | ResearchSubject (with extension) |

## 4. Agentic research methodology

CTMS supports structured evaluation of clinical AI agents through:

- Deterministic synthetic environments with reproducibility hashes.
- Arena runs that capture traces and compute seven canonical metrics.
- Release gates that promote cohorts only when all metrics pass thresholds.
- Council deliberation trials with seat-based ballots and Cynefin routing.
- Bias and fairness reports across demographic strata.

This methodology aligns with the NIST AI RMF approach of measuring, managing, and communicating AI risks.

## 5. Safety and privacy engineering

- DCB0129 clinical safety case in `docs/SAFETY_CASE.md`.
- DCB0160 deployer responsibilities in `docs/DCB0160.md`.
- Privacy mapping in `docs/PRIVACY.md`.
- AI governance mapping in `docs/AI_GOVERNANCE.md`.

## 6. References

References are listed as URLs without tracking parameters. All links were valid at the time of writing; verify before formal submission.
