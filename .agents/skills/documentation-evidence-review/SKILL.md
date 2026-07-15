---
name: documentation-evidence-review
description: Review synthetic ICHD clinical documentation for explicit evidence relevant to an illustrative audit question. Use after record normalization in this POC; identify evidence gaps without inferring diagnoses, codes, causality, or payment impact.
---

# Documentation Evidence Review

1. Read the normalized evidence inventory.
2. Extract only explicit statements relevant to the requested synthetic rule.
3. Cite note type and source field for every statement.
4. Label missing support as `insufficient_evidence`.
5. Send evidence and gaps to `audit-rule-evaluation`.

## Guardrail

Draft questions, not clinical conclusions. A qualified human reviewer owns interpretation.
