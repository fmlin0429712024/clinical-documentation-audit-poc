---
name: clinical-audit-orchestrator
description: Orchestrate the full synthetic ICHD audit pipeline end to end — normalization, evidence review, Method-dispatched rule evaluation, human review, and evaluation feedback. Use as the top-level entry point to demonstrate the whole governed agentic workflow in this POC; never execute against real patient or client data.
allowed-tools: Read(data/**) Skill
---

# Clinical Audit Orchestrator

**Domain:** collaboration — sequences across all domains; owns no evidence
of its own. Treatment-domain rules (`SYN-ICHD-01/02/04/09`) and the
patient-domain rule (`SYN-ICHD-05`) both flow through the same four steps
below — this skill doesn't branch by domain itself, `audit-rule-evaluation`
does.

## Purpose

Sequence the full pipeline and enforce the human-review gate — this skill
never decides an outcome itself, only routes to the skill/tool that does.

## Workflow

1. Run `clinical-record-normalization` on the synthetic gold set. To
   exercise `SYN-ICHD-05` (patient domain), use
   `data/synthetic-ichd-patient-goldset-multi-domain.json` — the original
   `data/synthetic-ichd-patient-goldset.json` has no `patient.nursing_notes`
   and cannot trigger that rule.
2. Run `documentation-evidence-review` for the candidate audit question.
3. Run `audit-rule-evaluation`, which dispatches by Method **and Domain** —
   `deterministic-rule-audit` (SQLite-backed) for deterministic rules, the
   matching use-case skill for non-deterministic ones (treatment domain:
   `intradialytic-hypotension-review`, `treatment-refusal-review`; patient
   domain: `patient-continuity-review`).
4. Route the output to a qualified human reviewer.
5. Record reviewer feedback as an evaluation signal; never change a rule
   or policy automatically.

## Output Contract

Return the finding produced by `audit-rule-evaluation`, routed to a human
reviewer, plus a recorded evaluation signal once reviewed.

## Guardrails

- Do not access real patient or client data.
- Do not make clinical, coding, coverage, billing, or payment decisions.
- Do not treat synthetic rules as policy.
- Preserve evidence traceability and human accountability.
- Stop and label the record `insufficient_evidence` when source evidence
  is absent, contradictory, or outside the synthetic scope.
