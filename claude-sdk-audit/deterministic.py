#!/usr/bin/env python3
"""Part 2, deterministic path: zero Anthropic API calls, by design.

Imports the existing Track A tool directly (data/, tools/ stay the single
source of truth — see the repo's root README for why they're referenced,
not copied) instead of shelling out to it: there's no agent in the loop
here, so there's no Bash boundary to cross anymore.

No `import anthropic` appears anywhere in this file. That's the point:
in Part 1, Claude Code's own agent loop was still LLM-driven even when the
verdict wasn't. Here, we write the loop ourselves, so "zero LLM" is a
literal, inspectable fact about this file, not a documented intent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.query_deterministic_rule import evaluate, list_rules  # noqa: E402

GOLD_SET_PATH = REPO_ROOT / "data" / "synthetic-ichd-patient-goldset.json"


def audit_deterministic(gold_set_path: Path = GOLD_SET_PATH) -> list[dict]:
    """Evaluate every deterministic rule against every treatment. This is
    the same loop Part 1's deterministic-rule-audit skill described in
    prose for an agent to perform -- here it's just a for loop."""
    record = json.loads(gold_set_path.read_text())
    rules = list_rules()
    results: list[dict] = []
    for treatment in record.get("clinical_treatments", []):
        for rule in rules:
            try:
                result = evaluate(rule, treatment)
            except KeyError as exc:
                result = {
                    "rule_id": rule["rule_id"],
                    "method": "deterministic",
                    "triggered": None,
                    "status": "not_applicable",
                    "trigger_description": rule["description"],
                    "draft_question": None,
                    "prohibited_inference": rule["prohibited_inference"],
                    "note": f"required field missing on this treatment: {exc}",
                }
            results.append({"treatment_date": treatment.get("treatment_date"), **result})
    return results


if __name__ == "__main__":
    print(json.dumps(audit_deterministic(), indent=2))
