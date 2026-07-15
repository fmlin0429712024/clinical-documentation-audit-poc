---
name: audit-rule-evaluation
description: Apply the illustrative synthetic ICHD documentation audit rules to cited evidence and draft a traceable finding for human review. Use only with the repository's mock rules and mock data; never treat outputs as clinical, coding, billing, or compliance decisions.
---

# Audit Rule Evaluation

1. Read `rules/synthetic-audit-rules.md` and cited evidence.
2. Determine whether a synthetic trigger is present.
3. Draft a finding only when the evidence supports its question.
4. Include trigger, evidence, evidence gaps, and prohibited inferences.
5. Set status to `requires_human_review`.

## Output Contract

Return a traceable draft finding. Do not assign a diagnosis, code, clinical severity, or payment result.
