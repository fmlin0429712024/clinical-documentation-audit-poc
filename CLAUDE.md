# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A **synthetic demonstration** reconstructing, on fully fictional data, the architecture behind a governed AI clinical-documentation-audit workflow for in-center hemodialysis (ICHD). It is an architectural communication artifact (portfolio/POC), not a clinical decision system and not production code. There is no application code, build, lint, or test tooling in this repo — it is data + rules + agent-skill definitions + docs.

> **Every patient, encounter, treatment, note, audit rule, evidence item, and finding here is fictional.** No client data, proprietary logic, or production code.

## Non-negotiable guardrails

These apply to any work in this repo, including extending skills or rules:

- Never introduce real patient, provider, or client data — mock/synthetic only.
- An AI agent may draft a traceable finding/question; it must never render a clinical, coding, coverage, billing, or payment decision. All findings are `requires_human_review`.
- Synthetic audit rules (`rules/synthetic-audit-rules.md`) are illustrative, not policy — don't treat them as real coding/compliance guidance.
- Preserve evidence traceability: every claim in a finding must cite a source field from the gold set.
- When evidence is absent, contradictory, or out of scope, label the record `insufficient_evidence` rather than inferring.

## Architecture: the workflow

The core idea is a pipeline of narrow, single-purpose agent skills feeding a human review gate, plus a feedback loop:

```
synthetic gold set → normalize → evidence review → rule evaluation → draft finding → HUMAN REVIEW → outcome
                                                                                          ↓ (reject/clarify)
                                                                                   reviewer feedback → loop back to evidence review
```

This is implemented as four agent skills, each with a single responsibility and an explicit output contract (see below). No skill is allowed to make the final call — that's the entire point of the design.

## Agent skills

Skills live in two parallel locations that must be kept in sync when edited:

- `.agents/skills/<name>/SKILL.md` + `.agents/skills/<name>/agents/openai.yaml` — Codex/OpenAI-facing registration.
- `.claude/skills/<name>/SKILL.md` — Claude Code-facing copy (same `SKILL.md` content, no `openai.yaml` sidecar — Claude Code doesn't use it).

If you edit a skill's instructions, update `SKILL.md` in **both** locations identically.

The four skills and their call order (see `clinical-audit-orchestrator/SKILL.md`):

1. **`clinical-record-normalization`** — turns the raw synthetic gold set into a traceable, normalized evidence inventory (patient/treatment/notes/audit context). Absent fields are marked `not_present`, never invented. Output always carries `human_review_required: true`.
2. **`documentation-evidence-review`** — given the normalized inventory and a candidate audit question, extracts only explicit statements relevant to that question, cited by note type/source field. Missing support is labeled `insufficient_evidence`. Drafts questions, not conclusions.
3. **`audit-rule-evaluation`** — applies `rules/synthetic-audit-rules.md` to the cited evidence and drafts a finding (status `requires_human_review`) including trigger, evidence, evidence gaps, and explicitly prohibited inferences.
4. **`clinical-audit-orchestrator`** — sequences the above three, routes the result to a human reviewer, and records reviewer feedback as an evaluation signal (confirm/reject/clarify) without auto-changing any rule or policy.

## Key files

| File | Role |
| --- | --- |
| `data/synthetic-ichd-patient-goldset.json` | The one synthetic input record (`patient` + `clinical_treatments[]`) all skills operate on. |
| `rules/synthetic-audit-rules.md` | The 3 illustrative rules (`SYN-ICHD-01/02/03`) — trigger, required evidence, agent output, human decision — plus guardrails. |
| `outputs/sample-audit-finding.md` | Example shape of a drafted finding, including the reviewer-outcome and evaluation-signal fields. |
| `docs/safety-and-governance.md` | Public-safety design notes and the list of real-world prerequisites (access controls, privacy review, governance, audit logging, etc.) before this pattern could ever touch real data. |

## Working in this repo

- There's no code to build/lint/test. "Verifying a change" means: does the edited skill/rule/data still satisfy the output contracts and guardrails above, and are the `.agents/` and `.claude/` skill copies still identical?
- Keep the synthetic-data notice/disclaimers intact in any new data or output files — don't strip them for brevity.
- New audit rules should follow the existing table shape in `rules/synthetic-audit-rules.md` (Rule ID, synthetic trigger, required evidence, agent output, human decision) and stay clearly fictional.
