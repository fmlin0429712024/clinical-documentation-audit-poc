# Sample Synthetic Patient Continuity Finding — Positive Case (Clean)

> **Mock output only.** It demonstrates traceability, not a real audit conclusion. Produced by the `patient-continuity-review` skill (non-deterministic, patient domain — LLM judgment against a narrative use-case description, not a formula). Source: `patient.nursing_notes` entry dated `2026-03-02`, cross-referenced against the treatment dated `2026-03-04`, both in `data/synthetic-ichd-patient-goldset-multi-domain.json` (**not** the original `data/synthetic-ichd-patient-goldset.json`, which has no `nursing_notes`). Compare against the [negative case](sample-patient-continuity-finding-negative.md).

| Field | Example |
| --- | --- |
| Finding ID | `SYN-FIND-0006` |
| Rule | `SYN-ICHD-05` |
| Status | `requires_human_review` |
| Trigger | Synthetic nursing note documents a care-plan-relevant change (medication dose adjustment) |
| Evidence | Synthetic nursing note (`2026-03-02`): "physician adjusted the patient's antihypertensive medication (dose reduced) effective today, to reduce intradialytic hypotension risk. Care team to confirm tolerance of the new dose at the next treatment." |
| Next relevant treatment | `2026-03-04` (earliest `clinical_treatments[]` entry after the nursing note's date) |

## Judgment Points

| Point | Status | Citation / gap |
| --- | --- | --- |
| Change adequately described (what, when) | `documented` | "antihypertensive medication (dose reduced) effective today" |
| Next relevant treatment reflects awareness | `documented` | `treatment_note` (2026-03-04): "staff noted the patient's antihypertensive dose was reduced per the 2026-03-02 medication change" |
| Effect/outcome followed up | `documented` | `treatment_note`: "Blood pressure was monitored closely throughout the session; no hypotensive symptoms occurred and the patient tolerated the reduced dose well" |
| Physician notified / escalation if warranted | `documented` | `follow_up_note`: "physician was informed that the patient tolerated the reduced antihypertensive dose well during treatment" |

| Field | Example |
| --- | --- |
| Draft question | All four judgment points are documented for this care-plan change — does the reviewer confirm the documentation is adequate for the intended review purpose? |
| Prohibited inference | No diagnosis, code, clinical severity, or payment implication is inferred; whether the medication change itself was clinically appropriate is not assessed — only that it was documented and carried through. |
| Reviewer outcome | Pending — must be completed by a qualified human reviewer |

## Evaluation Signal

Even with all four points documented, this skill never confirms adequacy on
its own — the finding still routes to a human reviewer. This is the
intended contrast with the
[negative case](sample-patient-continuity-finding-negative.md): same skill,
same four judgment points, same mechanism (a patient-level note
cross-referenced against the next relevant treatment record), different
evidence in the notes.
