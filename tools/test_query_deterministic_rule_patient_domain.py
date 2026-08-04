#!/usr/bin/env python3
"""Phase 3.5 tests for the patient-domain deterministic rule (SYN-ICHD-06).

Separate file from test_query_deterministic_rule.py on purpose: that file
is Phase 1's frozen regression suite, pinned to the original two-rule
data/audit_rules.db (test_list_includes_both_seeded_rules asserts the set
is exactly {SYN-ICHD-01, SYN-ICHD-09}). SYN-ICHD-06 lives in a separate
store, data/audit_rules-multi-domain.db, queried via --db — this file
tests that store, not the shared one, so it can never break Phase 1/2.

Uses small hand-built {"nursing_notes_count": N} objects rather than real
patient data, matching the existing suite's convention (see
test_exactly_at_threshold_triggers in test_query_deterministic_rule.py) —
this rule's logic is a plain count-vs-threshold comparison, so a real
gold-set record isn't needed to exercise both branches.

    python3 tools/test_query_deterministic_rule_patient_domain.py -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "query_deterministic_rule.py"
MULTI_DOMAIN_DB = Path(__file__).resolve().parent.parent / "data" / "audit_rules-multi-domain.db"
ORIGINAL_DB = Path(__file__).resolve().parent.parent / "data" / "audit_rules.db"


def run_tool(rule_id: str, payload: dict, db_path: Path = MULTI_DOMAIN_DB) -> dict:
    result = subprocess.run(
        [sys.executable, str(TOOL), rule_id, "-", "--db", str(db_path)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


class SynIchd06SparseNursingNotes(unittest.TestCase):
    def test_two_notes_triggers(self):
        # Matches data/synthetic-ichd-patient-goldset-multi-domain.json's
        # actual patient.nursing_notes count (2) — the real worked example.
        result = run_tool("SYN-ICHD-06", {"nursing_notes_count": 2})
        self.assertTrue(result["triggered"])
        self.assertEqual(result["status"], "requires_human_review")
        self.assertIsNotNone(result["draft_question"])

    def test_zero_notes_triggers(self):
        result = run_tool("SYN-ICHD-06", {"nursing_notes_count": 0})
        self.assertTrue(result["triggered"])

    def test_three_notes_does_not_trigger(self):
        result = run_tool("SYN-ICHD-06", {"nursing_notes_count": 3})
        self.assertFalse(result["triggered"])
        self.assertEqual(result["status"], "no_finding")
        self.assertIsNone(result["draft_question"])

    def test_more_than_three_notes_does_not_trigger(self):
        result = run_tool("SYN-ICHD-06", {"nursing_notes_count": 5})
        self.assertFalse(result["triggered"])


class OriginalStoreUnaffected(unittest.TestCase):
    """Guardrail: this new rule must never leak into the shared, frozen store."""

    def test_syn_ichd_06_not_in_original_db(self):
        result = subprocess.run(
            [sys.executable, str(TOOL), "--list", "--db", str(ORIGINAL_DB)],
            capture_output=True,
            text=True,
            check=True,
        )
        rule_ids = {rule["rule_id"] for rule in json.loads(result.stdout)}
        self.assertEqual(rule_ids, {"SYN-ICHD-01", "SYN-ICHD-09"})
        self.assertNotIn("SYN-ICHD-06", rule_ids)


if __name__ == "__main__":
    unittest.main()
