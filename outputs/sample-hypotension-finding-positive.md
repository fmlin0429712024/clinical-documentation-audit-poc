# Sample Synthetic Hypotension Documentation Finding — Positive Case (Clean)

> **Mock output only.** It demonstrates traceability, not a real audit conclusion. Produced by the `intradialytic-hypotension-review` skill (non-deterministic — LLM judgment against a narrative use-case description, not a formula). Source treatment: `2026-01-28` in `data/synthetic-ichd-patient-goldset.json`. Compare against the [negative case](sample-hypotension-finding-negative.md).

| Field | Example |
| --- | --- |
| Finding ID | `SYN-FIND-0003` |
| Rule | `SYN-ICHD-04` |
| Status | `requires_human_review` |
| Trigger | Synthetic treatment note documents a symptomatic blood-pressure drop (dizziness, low BP) |
| Evidence | Synthetic treatment note: "patient reported dizziness and blood pressure was recorded as low. Ultrafiltration rate was reduced and the patient was repositioned. A saline bolus was given per standing order. Blood pressure was reassessed 15 minutes later and had returned to baseline; symptoms resolved." |

## Judgment Points

| Point | Status | Citation / gap |
| --- | --- | --- |
| Drop/symptoms recognized and recorded | `documented` | "patient reported dizziness and blood pressure was recorded as low" |
| Corrective action taken | `documented` | "Ultrafiltration rate was reduced and the patient was repositioned. A saline bolus was given per standing order." |
| Reassessment after action | `documented` | "Blood pressure was reassessed 15 minutes later and had returned to baseline; symptoms resolved" |
| Physician notified if unresolved | `documented` | `follow_up_note`: "physician was notified of the event and the reassessment findings" |

| Field | Example |
| --- | --- |
| Draft question | All four judgment points are documented for this hypotension event — does the reviewer confirm the documentation is adequate for the intended review purpose? |
| Prohibited inference | No diagnosis, code, clinical severity, or payment implication is inferred; whether the clinical response was medically correct is not assessed — only that it was documented. |
| Reviewer outcome | Pending — must be completed by a qualified human reviewer |

## Evaluation Signal

Even with all four points documented, this skill never confirms adequacy on
its own — the finding still routes to a human reviewer. The evaluation loop
records whether the reviewer confirmed, rejected, or requested clarification,
and why. This is the intended contrast with the
[negative case](sample-hypotension-finding-negative.md): same skill, same
four judgment points, different evidence in the note — proving the judgment
tracks the text rather than a fixed verdict.
