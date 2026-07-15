---
name: clinical-audit-orchestrator
description: Orchestrate the synthetic ICHD clinical-documentation audit workflow across normalization, evidence review, illustrative rule evaluation, human review, and evaluation feedback. Use to demonstrate governed agentic workflow design in this POC; never execute against real patient or client data.
---

# Clinical Audit Orchestrator

## Workflow

1. Run `clinical-record-normalization` on the synthetic gold set.
2. Run `documentation-evidence-review` for the candidate audit question.
3. Run `audit-rule-evaluation` using only the synthetic rules.
4. Route the output to a qualified human reviewer.
5. Record reviewer feedback as an evaluation signal; do not change a rule or policy automatically.

## Stop Conditions

Stop and label the record `insufficient_evidence` when source evidence is absent, contradictory, or outside the synthetic scope.

## Non-Negotiable Guardrails

- Do not access real patient or client data.
- Do not make clinical, coding, coverage, billing, or payment decisions.
- Do not treat synthetic rules as policy.
- Preserve evidence traceability and human accountability.
