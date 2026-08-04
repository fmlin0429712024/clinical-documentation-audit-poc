# Sample Synthetic Patient-Domain Deterministic Finding

> **Mock output only.** It demonstrates traceability, not a real audit conclusion. Produced by the `deterministic-rule-audit` skill's patient-level check — resolved by `tools/query_deterministic_rule.py SYN-ICHD-06 - --db data/audit_rules-multi-domain.db`, **zero LLM judgment in the verdict**, same guarantee as `SYN-ICHD-01`/`09`. Source: `patient.nursing_notes` in `data/synthetic-ichd-patient-goldset-multi-domain.json` (count = 2). Unlike `SYN-ICHD-01`/`09`, this rule lives in a separate SOP store (`data/audit_rules-multi-domain.db`), never added to the shared `data/audit_rules.db` — see `docs/prd-multi-agent-domain-split.md`.

| Field | Example |
| --- | --- |
| Finding ID | `SYN-FIND-0008` |
| Rule | `SYN-ICHD-06` |
| Status | `requires_human_review` |
| Trigger | Synthetic patient record has 2 documented `nursing_notes` entries (`nursing_notes_count < 3`) |
| Evidence | `nursing_notes_count = 2` (computed from `patient.nursing_notes`, not judged) |
| Draft question | Is the sparse nursing-note documentation for this patient consistent with actual care-plan activity, or does the record need to be completed? |
| Prohibited inference | No diagnosis, code, clinical conclusion, or payment implication is inferred. |
| Reviewer outcome | Pending — must be completed by a qualified human reviewer |

## Both branches, tool-verified (not just this one worked example)

`tools/test_query_deterministic_rule_patient_domain.py` exercises both sides of the threshold directly against the tool (not through an LLM), since a real second patient record isn't needed to prove the comparison works:

| `nursing_notes_count` | `triggered` |
| --- | --- |
| `0` | `true` |
| `2` (this patient's actual count) | `true` |
| `3` | `false` |
| `5` | `false` |

## Evaluation Signal

The evaluation loop records whether the reviewer confirmed, rejected, or clarified the draft question and why. That feedback may improve rule wording (e.g. the illustrative threshold of 3) or evidence retrieval; it must not silently change clinical policy.
