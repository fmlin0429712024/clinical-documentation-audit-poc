# Synthetic ICHD Documentation Audit Rules

> These rules are fictional examples for workflow demonstration. They are not clinical, coding, billing, quality, or compliance guidance.

| Rule ID | Method | Synthetic trigger | Required evidence to draft a finding | Agent output | Human decision |
| --- | --- | --- | --- | --- | --- |
| SYN-ICHD-01 | deterministic | A `clinical_treatments[]` item completed materially earlier than scheduled (`scheduled_minutes − completed_minutes ≥ 15`) | Treatment duration | Run via `deterministic-rule-audit` skill (batch) or `tools/query_deterministic_rule.py` directly (single check); either way, report the SQLite-backed result verbatim | Confirm, reject, or request clarification |
| SYN-ICHD-02 | non-deterministic | A fictional symptom/event is mentioned in `treatment_note` | `treatment_note` and `follow_up_note` | Identify missing evidence, if any | Confirm clinical relevance |
| SYN-ICHD-03 | non-deterministic | `follow_up_note` is present | Follow-up statement when documented | Flag an evidence gap only | Decide whether action is needed |
| SYN-ICHD-04 | non-deterministic | `treatment_note` documents a symptomatic blood-pressure drop (hypotension event) | `treatment_note`, `follow_up_note`, and the narrative use-case description in the `intradialytic-hypotension-review` skill | Apply the skill's use-case description; cite which of the four judgment points are documented vs. an evidence gap | Confirm adequate, request clarification, or flag the gap |
| SYN-ICHD-09 | deterministic | A `clinical_treatments[]` item has `status == "missed"` | `status` | Run via `deterministic-rule-audit` skill (batch) or `tools/query_deterministic_rule.py` directly (single check); either way, report the SQLite-backed result verbatim | Confirm, reject, or request clarification |

**Method** distinguishes how the trigger is decided: `deterministic` rules are resolved by `tools/query_deterministic_rule.py` against the SQLite SOP store in `data/audit_rules.db` — the agent invokes the tool and reports its result, it does not judge the threshold itself. `non-deterministic` rules require reading free-text notes and applying judgment against a described scenario; there is no formula, only a narrative use-case description (in the relevant skill) that the LLM reasons against.

## Guardrails

- Cite only source fields available in the synthetic gold set.
- Never infer a diagnosis, code, causality, or reimbursement impact.
- State `insufficient evidence` when documentation does not support a conclusion.
- Route every finding to a qualified human reviewer.
