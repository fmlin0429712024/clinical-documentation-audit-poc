---
name: clinical-record-normalization
description: Normalize a synthetic ICHD clinical-documentation gold set into a traceable audit-ready record. Use for mock data preparation, evidence inventory, and schema validation in this POC; never use for real patient data or clinical decisions.
---

# Clinical Record Normalization

1. Read the synthetic record and preserve source identifiers.
2. Create an evidence inventory: patient context, treatment context, notes, and audit context.
3. Mark absent fields as `not_present`; do not invent values.
4. Carry the synthetic-data notice into the normalized output.
5. Hand the evidence inventory to `documentation-evidence-review`.

## Output Contract

Return a normalized record, source references, absent-field list, and `human_review_required: true`.
