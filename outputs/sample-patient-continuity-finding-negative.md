# Sample Synthetic Patient Continuity Finding — Negative Case (Flagged)

> **Mock output only.** It demonstrates traceability, not a real audit conclusion. Produced by the `patient-continuity-review` skill (non-deterministic, patient domain — LLM judgment against a narrative use-case description, not a formula). Source: `patient.nursing_notes` entry dated `2026-03-16`, cross-referenced against the treatment dated `2026-03-18`, both in `data/synthetic-ichd-patient-goldset-multi-domain.json` (**not** the original `data/synthetic-ichd-patient-goldset.json`, which has no `nursing_notes`). Compare against the [positive case](sample-patient-continuity-finding-positive.md).

| Field | Example |
| --- | --- |
| Finding ID | `SYN-FIND-0007` |
| Rule | `SYN-ICHD-05` |
| Status | `requires_human_review` |
| Trigger | Synthetic nursing note documents a care-plan-relevant change (medication discontinuation) |
| Evidence | Synthetic nursing note (`2026-03-16`): "patient's oral iron supplement was discontinued effective today due to reported GI intolerance. Care team to monitor iron-related labs and confirm resolution of symptoms." |
| Next relevant treatment | `2026-03-18` (earliest `clinical_treatments[]` entry after the nursing note's date) |

## Judgment Points

| Point | Status | Citation / gap |
| --- | --- | --- |
| Change adequately described (what, when) | `documented` | "oral iron supplement was discontinued effective today due to reported GI intolerance" |
| Next relevant treatment reflects awareness | `evidence_gap` | `treatment_note` (2026-03-18): "treatment completed without incident; standard intradialytic monitoring performed" — no reference to the iron-supplement change |
| Effect/outcome followed up | `evidence_gap` | Neither `treatment_note` nor `follow_up_note` mentions GI symptoms or iron-related labs |
| Physician notified / escalation if warranted | `evidence_gap` | No mention of physician notification regarding this change in either note |

| Field | Example |
| --- | --- |
| Draft question | Only the initial change is documented in the nursing note — the next treatment's documentation does not reflect awareness of the iron-supplement discontinuation, and no follow-up or physician notification is documented. Were these performed and simply not recorded, or does the record need to be completed? |
| Prohibited inference | No diagnosis, code, clinical severity, or payment implication is inferred; whether the medication change itself was clinically appropriate is not assessed. |
| Reviewer outcome | Pending — must be completed by a qualified human reviewer |

## Evaluation Signal

The evaluation loop records whether the reviewer confirmed these gaps,
rejected them (e.g. continuity was in fact documented elsewhere), or
requested clarification, and why. That feedback may improve the skill's
use-case description or evidence retrieval; it must not silently change
clinical policy.
