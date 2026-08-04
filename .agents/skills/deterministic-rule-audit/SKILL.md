---
name: deterministic-rule-audit
description: Audit every clinical_treatments[] entry for a synthetic ICHD patient against every deterministic rule (SYN-ICHD-01, SYN-ICHD-09) in the SQLite SOP store, by calling tools/query_deterministic_rule.py once per (rule, treatment) pair. Use from audit-rule-evaluation, or directly, whenever a full deterministic pass over a patient is needed — not just one rule/treatment lookup. Never judges a threshold itself; the tool's result is always final.
allowed-tools: Read(data/**) Bash(python3 tools/query_deterministic_rule.py *)
---

# Deterministic Rule Audit

## Purpose

Give every deterministic rule a chance to fire against every treatment for
a patient — the agent does the looping, `tools/query_deterministic_rule.py`
does the (LLM-free) computing. This is the batch counterpart to a single
ad-hoc rule/treatment check.

## Workflow

1. Get the rule catalog: run `python3 tools/query_deterministic_rule.py --list`.
2. Get the patient's `clinical_treatments[]` (from `clinical-record-normalization`
   output, or the gold set directly for a standalone run).
3. For each treatment, for each rule from step 1: extract that treatment
   as JSON and run `python3 tools/query_deterministic_rule.py <rule_id> -`
   (piped on stdin). This is a real loop of tool calls — do not skip
   pairs, do not summarize without checking each one.
4. For every result with `"triggered": true`, draft a finding using that
   result's `trigger_description`, `draft_question`, and
   `prohibited_inference` verbatim, citing the treatment date and rule ID.
5. Set every drafted finding's status to `requires_human_review`.

## Output Contract

Return one draft finding per triggered (rule, treatment) pair, each citing
the treatment date and rule ID, plus a short tally of how many
(rule, treatment) pairs were checked and how many triggered. Do not assign
a diagnosis, code, clinical severity, or payment result.

## Guardrails

- Never compute or judge a threshold inline — every verdict must come
  verbatim from `tools/query_deterministic_rule.py`.
- Audit every treatment for the patient, not a hand-picked one — a clean
  audit means every pair was checked and none triggered, not that only
  the obvious ones were checked.
- If a rule's required field is missing from a treatment, the tool call
  will fail — record that pair as `not_present`/not applicable rather
  than guessing a value to force an answer.
