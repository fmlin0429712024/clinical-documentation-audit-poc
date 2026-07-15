# Sample Synthetic Audit Finding

> **Mock output only.** It demonstrates traceability, not a real audit conclusion.

| Field | Example |
| --- | --- |
| Finding ID | `SYN-FIND-0001` |
| Rule | `SYN-ICHD-01` |
| Status | `requires_human_review` |
| Trigger | Synthetic treatment duration: 205 of 240 scheduled minutes |
| Evidence | Synthetic treatment note says treatment ended early; synthetic note records a stable discharge |
| Draft question | Is the fictional reason for early termination and the disposition sufficiently documented for the intended review purpose? |
| Prohibited inference | No diagnosis, code, clinical conclusion, or payment implication is inferred. |
| Reviewer outcome | Pending — must be completed by a qualified human reviewer |

## Evaluation Signal

The evaluation loop records whether the reviewer confirmed, rejected, or clarified the draft question and why. That feedback may improve rule wording, evidence retrieval, and prompt behavior; it must not silently change clinical policy.
