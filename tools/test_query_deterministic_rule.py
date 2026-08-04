#!/usr/bin/env python3
"""TDD-style tests for tools/query_deterministic_rule.py — the Track A tool.

Runs the CLI exactly as the audit-rule-evaluation skill invokes it
(subprocess, JSON on stdin) so the test exercises the real tool contract,
not just its internal functions. Stdlib only — run with:

    python3 tools/test_query_deterministic_rule.py -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "query_deterministic_rule.py"
GOLD_SET = Path(__file__).resolve().parent.parent / "data" / "synthetic-ichd-patient-goldset.json"


def run_tool(rule_id: str, treatment: dict) -> dict:
    result = subprocess.run(
        [sys.executable, str(TOOL), rule_id, "-"],
        input=json.dumps(treatment),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def _treatment_by_date(date: str) -> dict:
    gold_set = json.loads(GOLD_SET.read_text())
    for treatment in gold_set["clinical_treatments"]:
        if treatment["treatment_date"] == date:
            return treatment
    raise AssertionError(f"no treatment dated {date} in the gold set")


class SynIchd01EarlyTermination(unittest.TestCase):
    def test_positive_gold_set_record_triggers(self):
        treatment = _treatment_by_date("2026-01-14")  # 205 of 240 min — 35 min short
        result = run_tool("SYN-ICHD-01", treatment)
        self.assertTrue(result["triggered"])
        self.assertEqual(result["status"], "requires_human_review")
        self.assertIsNotNone(result["draft_question"])

    def test_hypotension_records_do_not_trigger(self):
        # These two isolate the non-deterministic hypotension judgment as
        # the only variable — both are deterministic-clean on purpose.
        for date in ("2026-01-28", "2026-02-04"):
            with self.subTest(date=date):
                result = run_tool("SYN-ICHD-01", _treatment_by_date(date))
                self.assertFalse(result["triggered"])
                self.assertEqual(result["status"], "no_finding")
                self.assertIsNone(result["draft_question"])

    def test_treatment_refusal_records_also_trigger(self):
        # Refusing/discontinuing treatment naturally cuts it short, so
        # these two deliberately trigger SYN-ICHD-01 as well as the
        # non-deterministic SYN-ICHD-02 judgment -- proving combined
        # dispatch works on a second, independent pair of records.
        for date in ("2026-02-11", "2026-02-18"):
            with self.subTest(date=date):
                result = run_tool("SYN-ICHD-01", _treatment_by_date(date))
                self.assertTrue(result["triggered"])
                self.assertEqual(result["status"], "requires_human_review")

    def test_exactly_at_threshold_triggers(self):
        treatment = {"scheduled_minutes": 240, "completed_minutes": 225}  # 15 min short
        result = run_tool("SYN-ICHD-01", treatment)
        self.assertTrue(result["triggered"])

    def test_one_minute_under_threshold_does_not_trigger(self):
        treatment = {"scheduled_minutes": 240, "completed_minutes": 226}  # 14 min short
        result = run_tool("SYN-ICHD-01", treatment)
        self.assertFalse(result["triggered"])

    def test_completed_later_than_scheduled_does_not_trigger(self):
        treatment = {"scheduled_minutes": 240, "completed_minutes": 250}
        result = run_tool("SYN-ICHD-01", treatment)
        self.assertFalse(result["triggered"])


class SynIchd09MissedTreatment(unittest.TestCase):
    def test_positive_missed_status_triggers(self):
        result = run_tool("SYN-ICHD-09", {"status": "missed"})
        self.assertTrue(result["triggered"])
        self.assertEqual(result["status"], "requires_human_review")

    def test_negative_completed_status_does_not_trigger(self):
        result = run_tool("SYN-ICHD-09", {"status": "completed"})
        self.assertFalse(result["triggered"])
        self.assertEqual(result["status"], "no_finding")


class ToolErrorHandling(unittest.TestCase):
    def test_unknown_rule_id_exits_nonzero(self):
        result = subprocess.run(
            [sys.executable, str(TOOL), "SYN-ICHD-NOPE", "-"],
            input="{}",
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_list_includes_both_seeded_rules(self):
        result = subprocess.run(
            [sys.executable, str(TOOL), "--list"],
            capture_output=True,
            text=True,
            check=True,
        )
        rule_ids = {rule["rule_id"] for rule in json.loads(result.stdout)}
        self.assertEqual(rule_ids, {"SYN-ICHD-01", "SYN-ICHD-09"})


if __name__ == "__main__":
    unittest.main()
