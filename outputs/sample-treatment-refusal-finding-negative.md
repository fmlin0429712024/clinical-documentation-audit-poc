# Sample Synthetic Treatment Refusal Documentation Finding — Negative Case (Flagged)

> **Mock output only.** It demonstrates traceability, not a real audit conclusion. Produced by the `treatment-refusal-review` skill (non-deterministic — LLM judgment against a narrative use-case description, not a formula). Source treatment: `2026-02-18` in `data/synthetic-ichd-patient-goldset.json`. Compare against the [positive case](sample-treatment-refusal-finding-positive.md). This treatment also triggers `SYN-ICHD-01` (deterministic) since the refusal cut the treatment short.

| Field | Example |
| --- | --- |
| Finding ID | `SYN-FIND-0005` |
| Rule | `SYN-ICHD-02` |
| Status | `requires_human_review` |
| Trigger | Synthetic treatment note documents a patient requesting to stop/refuse continued treatment |
| Evidence | Synthetic treatment note: "patient stated they wanted to stop treatment, citing anxiety. Patient continued to decline further treatment despite staff presence." |

## Judgment Points

| Point | Status | Citation / gap |
| --- | --- | --- |
| Refusal recognized and recorded, with reason | `documented` | "patient stated they wanted to stop treatment, citing anxiety" |
| Concerns addressed / risks explained | `evidence_gap` | Note does not describe any discussion of risks or attempt to address the patient's concerns |
| Physician notified | `evidence_gap` | No mention of physician notification in either note |
| Follow-up / monitoring plan documented | `evidence_gap` | `follow_up_note` only states "patient left the unit shortly after discontinuation" — no monitoring, reassessment, or discharge instructions recorded |

| Field | Example |
| --- | --- |
| Draft question | Only recognition of the refusal is documented for this event — risk discussion, physician notification, and a follow-up/monitoring plan are not documented. Were these performed and simply not recorded, or does the record need to be completed? |
| Prohibited inference | No diagnosis, code, clinical severity, or payment implication is inferred; whether the clinical response was medically correct is not assessed. |
| Reviewer outcome | Pending — must be completed by a qualified human reviewer |

## Evaluation Signal

The evaluation loop records whether the reviewer confirmed these gaps,
rejected them (e.g. the missing steps were in fact documented elsewhere),
or requested clarification, and why. That feedback may improve the
skill's use-case description or evidence retrieval; it must not silently
change clinical policy.
