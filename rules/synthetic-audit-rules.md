# Synthetic ICHD Documentation Audit Rules

> These rules are fictional examples for workflow demonstration. They are not clinical, coding, billing, quality, or compliance guidance.

| Rule ID | Synthetic trigger | Required evidence to draft a finding | Agent output | Human decision |
| --- | --- | --- | --- | --- |
| SYN-ICHD-01 | Treatment completed materially earlier than scheduled | Treatment duration and a relevant documentation note | Ask whether the reason and disposition are documented | Confirm, reject, or request clarification |
| SYN-ICHD-02 | A fictional symptom/event is mentioned | Source note and an associated assessment or follow-up statement | Identify missing evidence, if any | Confirm clinical relevance |
| SYN-ICHD-03 | Follow-up is referenced | Follow-up plan, owner, and timing when documented | Flag an evidence gap only | Decide whether action is needed |

## Guardrails

- Cite only source fields available in the synthetic gold set.
- Never infer a diagnosis, code, causality, or reimbursement impact.
- State `insufficient evidence` when documentation does not support a conclusion.
- Route every finding to a qualified human reviewer.
