# Sample Synthetic Treatment Refusal Documentation Finding — Positive Case (Clean)

> **Mock output only.** It demonstrates traceability, not a real audit conclusion. Produced by the `treatment-refusal-review` skill (non-deterministic — LLM judgment against a narrative use-case description, not a formula). Source treatment: `2026-02-11` in `data/synthetic-ichd-patient-goldset.json`. Compare against the [negative case](sample-treatment-refusal-finding-negative.md). This treatment also triggers `SYN-ICHD-01` (deterministic) since the refusal cut the treatment short — see the deterministic tool output separately.

| Field | Example |
| --- | --- |
| Finding ID | `SYN-FIND-0004` |
| Rule | `SYN-ICHD-02` |
| Status | `requires_human_review` |
| Trigger | Synthetic treatment note documents a patient requesting to stop/refuse continued treatment |
| Evidence | Synthetic treatment note: "patient stated they wanted to stop treatment and requested removal from dialysis, citing discomfort." |

## Judgment Points

| Point | Status | Citation / gap |
| --- | --- | --- |
| Refusal recognized and recorded, with reason | `documented` | "patient stated they wanted to stop treatment and requested removal from dialysis, citing discomfort" |
| Concerns addressed / risks explained | `documented` | "Nurse discussed the risks of discontinuing treatment early with the patient, including potential complications, and offered to adjust comfort measures" |
| Physician notified | `documented` | "Physician was notified of the refusal by phone" |
| Follow-up / monitoring plan documented | `documented` | `follow_up_note`: "patient remained in the unit for observation for 30 minutes after discontinuation; vital signs reassessed and stable prior to discharge home with standard post-treatment instructions and follow-up scheduled for the next session" |

| Field | Example |
| --- | --- |
| Draft question | All four judgment points are documented for this treatment-refusal event — does the reviewer confirm the documentation is adequate for the intended review purpose? |
| Prohibited inference | No diagnosis, code, clinical severity, or payment implication is inferred; whether the clinical response was medically correct is not assessed — only that it was documented. |
| Reviewer outcome | Pending — must be completed by a qualified human reviewer |

## Evaluation Signal

Even with all four points documented, this skill never confirms adequacy on
its own — the finding still routes to a human reviewer. This is the
intended contrast with the
[negative case](sample-treatment-refusal-finding-negative.md): same skill,
same four judgment points, different evidence in the note.
