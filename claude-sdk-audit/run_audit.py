#!/usr/bin/env python3
"""Part 2 orchestrator: runs both tracks against the full gold set.

Method dispatch -- "which rules are deterministic vs non-deterministic"
-- is a plain Python fact here, not something re-derived by an LLM
reading rules/synthetic-audit-rules.md's Method column, unlike Part 1.
Adding a new non-deterministic rule/skill later means adding a line here
explicitly, not hoping an agent infers it correctly each run.

Every non-deterministic trigger routes to human review regardless of
gap/no-gap, matching intradialytic-hypotension-review/SKILL.md's own
Workflow: even a fully-documented event only gets a reviewer's
confirmation requested, never self-confirmed by the skill.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from deterministic import GOLD_SET_PATH, audit_deterministic  # noqa: E402
from nondeterministic import judge_hypotension_documentation  # noqa: E402


def run_full_audit(gold_set_path: Path = GOLD_SET_PATH) -> dict:
    record = json.loads(gold_set_path.read_text())

    deterministic_results = audit_deterministic(gold_set_path)

    nondeterministic_results = []
    for treatment in record["clinical_treatments"]:
        judgment = judge_hypotension_documentation(treatment)
        nondeterministic_results.append(
            {
                "treatment_date": treatment["treatment_date"],
                "rule_id": "SYN-ICHD-04",
                "method": "non-deterministic",
                **judgment,
            }
        )

    findings_requiring_human_review = [
        r for r in deterministic_results if r["triggered"]
    ] + [r for r in nondeterministic_results if r["trigger_present"]]

    return {
        "deterministic_checks": deterministic_results,
        "non_deterministic_checks": nondeterministic_results,
        "findings_requiring_human_review": findings_requiring_human_review,
    }


if __name__ == "__main__":
    print(json.dumps(run_full_audit(), indent=2))
