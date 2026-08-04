"""TDD for the Part 2 deterministic path. Same fixtures/expectations as
tools/test_query_deterministic_rule.py in Part 1 -- this is deliberately
a parallel test suite, not a shared one, since it's asserting on a
different code path (direct import + our own loop, not the CLI tool)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from deterministic import GOLD_SET_PATH, audit_deterministic  # noqa: E402


def test_audits_every_rule_against_every_treatment():
    results = audit_deterministic()
    # 2 seeded rules x however many treatments are in the real gold set
    import json

    record = json.loads(GOLD_SET_PATH.read_text())
    expected_pairs = len(record["clinical_treatments"]) * 2
    assert len(results) == expected_pairs


def test_expected_triggers_in_the_real_gold_set():
    results = audit_deterministic()
    triggered = {
        (r["treatment_date"], r["rule_id"])
        for r in results
        if r["triggered"] is True
    }
    # 2026-01-14: early-termination example. 2026-02-11/18: treatment
    # refused/discontinued, which naturally cuts the treatment short too --
    # deliberately triggers SYN-ICHD-01 alongside the non-deterministic
    # SYN-ICHD-02 judgment on the same records.
    assert triggered == {
        ("2026-01-14", "SYN-ICHD-01"),
        ("2026-02-11", "SYN-ICHD-01"),
        ("2026-02-18", "SYN-ICHD-01"),
    }


def test_no_anthropic_import_in_this_module():
    """Zero LLM in the deterministic path should be a literal, inspectable
    fact, not just documented intent -- assert it directly against the
    actual import statements, not prose that merely discusses this."""
    import ast

    source = Path(__file__).resolve().parent.joinpath("deterministic.py").read_text()
    tree = ast.parse(source)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    assert "anthropic" not in modules
