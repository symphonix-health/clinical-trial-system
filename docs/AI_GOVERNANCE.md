# CTMS AI Governance

## 1. Scope

This document describes governance for AI agentic subjects participating in clinical research through CTMS. It maps to the EU AI Act, MHRA software-as-medical-device guidance, and the NIST AI Risk Management Framework.

## 2. EU AI Act mapping

Clinical agents in CTMS are treated as high-risk AI systems under the EU AI Act where they influence subject care or trial integrity. The following obligations are addressed:

| Obligation | CTMS implementation |
|------------|---------------------|
| Risk management | Hazards, controls, and residual risks are documented in `docs/SAFETY_CASE.md`. |
| Data governance | Training and evaluation data are versioned through `SyntheticEnvironment` and `AgentRun` reproducibility hashes. |
| Technical documentation | Model cards are stored as `AgentAttestation` records with issuer, signature, expiry, and claims. |
| Record keeping | `AgentRun`, `AgentMetric`, and audit entries retain a complete trace of agent decisions. |
| Transparency | Agent subjects disclose autonomy level, safety class, and consent contract to authorised users. |
| Human oversight | `auto_with_threshold_hitl` autonomy level requires human approval for threshold-breaching actions. |
| Accuracy, robustness, cybersecurity | Release gates evaluate metrics; bias reports flag drift; tokens use DPoP or mTLS binding. |

## 3. MHRA software and AI as a medical device

CTMS clinical agents that provide diagnostic or therapeutic recommendations are assessed against MHRA guidance:

- Intended purpose is defined per `AgentSubject` and consent contract.
- Clinical validation is captured in `AgentRun` metrics and `AgentBiasReport`.
- Post-market surveillance uses drift flags and periodic re-attestation.
- Human-in-the-loop escalation is enforced for `advisory` and `auto_with_threshold_hitl` autonomy levels.

## 4. Algorithmic impact assessment

Before an agentic subject is enrolled in a study:

1. The agent owner submits an `AgentAttestation` trust bundle.
2. CTMS validates the attestation against `global-agent-registry` / `nexus-a2a-protocol`.
3. A consent contract is accepted with `purpose_of_use=research`, allowed systems, and human oversight flag.
4. The agent safety class and autonomy level are reviewed by an agent safety officer.
5. Bias reports are required for cohorts with demographic strata.

## 5. Model-card registry

`AgentAttestation` records act as model cards. Each record includes:

- `attestation_type`: clinical-safety, model-card, bias-audit, or security-review.
- `issuer`: the organisation that issued the attestation.
- `signature`: cryptographic signature of the trust bundle.
- `expires_at`: attestation expiry date.
- `claims_json`: structured claims such as accuracy, fairness metrics, training data provenance, and known limitations.

## 6. Bias audit cadence

- A bias report is generated before cohort promotion.
- Drift flags trigger an out-of-cycle review.
- Major model version changes require a new bias audit and protocol amendment.

## 7. Human-in-the-loop escalation

| Autonomy level | Behaviour |
|----------------|-----------|
| shadow | Agent observes and logs only; no autonomous action. |
| advisory | Agent recommends actions; human must approve before execution. |
| auto_with_threshold_hitl | Agent may act within safe thresholds; actions breaching thresholds require human approval. |

Escalation events are recorded as `AgentMetric` rows with `human_handoff_rate` and linked to `AgentRun` traces.

## 8. Token binding and research scope

High-risk agentic subjects use persona tokens with:

- DPoP or mTLS binding.
- `purpose_of_use=research`.
- `allowed_systems` restricted to CTMS and approved trial environments.
- Token revocation on withdrawal or disablement.

## 9. Council deliberation governance

Council trials for complex clinical decisions include:

- Clinical, pharmacy, rules-safety, and agent seats.
- Cynefin routing to direct execute, expert review, council deliberation, or human-only emergency override.
- Ballot minting per seat and synthesis with evidence references and blind-spot cross-scan.
- Outcome archive linked to `AgentRun` and audit chain.
