---
name: audit-rule-evaluation
description: Apply a synthetic ICHD audit rule to cited evidence and draft a traceable finding — dispatching to deterministic-rule-audit (SQLite-backed) for deterministic rules and to the matching use-case skill (e.g. intradialytic-hypotension-review) for non-deterministic ones. Use as the third pipeline step, after documentation-evidence-review. Never treat outputs as clinical, coding, billing, or compliance decisions.
allowed-tools: Read(rules/**) Read(data/**) Skill Bash(python3 tools/query_deterministic_rule.py *)
---

# Audit Rule Evaluation

## Purpose

Resolve a rule's trigger by the mechanism its Method demands — a tool query
for deterministic rules, judgment for non-deterministic ones — and draft a
traceable finding from the result.

## Workflow

1. Read `rules/synthetic-audit-rules.md` and the cited evidence from
   `documentation-evidence-review`.
2. Check the rule's Method column:
   - **deterministic** — do not judge the trigger yourself.
     - Auditing a whole patient (all treatments, all deterministic rules)?
       Run the `deterministic-rule-audit` skill — it owns the loop.
     - Checking a single rule against a single treatment? Extract that
       treatment as JSON and run
       `python3 tools/query_deterministic_rule.py <rule_id> -` (piping the
       treatment JSON on stdin) directly.
     Either way the result comes from `data/audit_rules.db` via the tool —
     report it verbatim.
   - **non-deterministic** — apply judgment against the cited evidence and
     the rule's narrative use-case description. For `SYN-ICHD-04`, run the
     `intradialytic-hypotension-review` skill instead of judging inline.
3. Draft a finding only when the evidence (or tool result) supports its
   question.
4. Include trigger, evidence, evidence gaps, and prohibited inferences.
5. Set status to `requires_human_review`.

## Output Contract

Return a traceable draft finding. Do not assign a diagnosis, code, clinical
severity, or payment result.

## Guardrails

- Deterministic rules: never reason about the threshold yourself — the
  tool's result is final.
- Non-deterministic rules: never treat the narrative use-case description
  as a checklist to pattern-match against.
- Cite only source fields present in the synthetic gold set.
