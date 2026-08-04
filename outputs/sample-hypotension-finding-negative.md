# Sample Synthetic Hypotension Documentation Finding — Negative Case (Flagged)

> **Mock output only.** It demonstrates traceability, not a real audit conclusion. Produced by the `intradialytic-hypotension-review` skill (non-deterministic — LLM judgment against a narrative use-case description, not a formula). Source treatment: `2026-02-04` in `data/synthetic-ichd-patient-goldset.json`. Compare against the [positive case](sample-hypotension-finding-positive.md).

| Field | Example |
| --- | --- |
| Finding ID | `SYN-FIND-0002` |
| Rule | `SYN-ICHD-04` |
| Status | `requires_human_review` |
| Trigger | Synthetic treatment note documents a symptomatic blood-pressure drop (dizziness, low BP) |
| Evidence | Synthetic treatment note: "patient reported dizziness and blood pressure was recorded as low. Ultrafiltration rate was reduced." |

## Judgment Points

| Point | Status | Citation / gap |
| --- | --- | --- |
| Drop/symptoms recognized and recorded | `documented` | "patient reported dizziness and blood pressure was recorded as low" |
| Corrective action taken | `documented` | "Ultrafiltration rate was reduced" |
| Reassessment after action | `evidence_gap` | Note does not state a follow-up BP value or reassessment |
| Physician notified if unresolved | `evidence_gap` | `follow_up_note` only states "patient monitored for the remainder of treatment" — no notification documented |

| Field | Example |
| --- | --- |
| Draft question | Reassessment and physician notification are not documented for this hypotension event — were they performed and simply not recorded, or does the record need to be completed? |
| Prohibited inference | No diagnosis, code, clinical severity, or payment implication is inferred; whether the clinical response was medically correct is not assessed. |
| Reviewer outcome | Pending — must be completed by a qualified human reviewer |

## Evaluation Signal

The evaluation loop records whether the reviewer confirmed the gap, rejected it (e.g. reassessment was in fact documented elsewhere), or requested clarification, and why. That feedback may improve the skill's use-case description or evidence retrieval; it must not silently change clinical policy.
