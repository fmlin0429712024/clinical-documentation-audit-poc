"""Tests for the Part 2 non-deterministic path.

Unlike test_deterministic.py, these make real, paid Claude API calls --
skipped automatically if no usable key is configured, so this doesn't
fail (or cost money) in an environment without ANTHROPIC_API_KEY set.

Per the Part 2 PRD's "what testing means differently here": schema
validity is a hard guarantee worth asserting unconditionally. Whether the
judgment content matches the known-good worked examples is also asserted
here, but that's inherently a live-model assertion, not a pure schema
check -- if this ever flakes, that's a prompt/schema tuning signal, not
necessarily a code bug.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(dotenv_path=HERE / ".env")
sys.path.insert(0, str(HERE))

from nondeterministic import GOLD_SET_PATH, judge_hypotension_documentation  # noqa: E402

_key = os.environ.get("ANTHROPIC_API_KEY", "")
requires_live_key = pytest.mark.skipif(
    not _key or not _key.startswith("sk-ant-"),
    reason="ANTHROPIC_API_KEY not configured -- skipping live API test",
)


def _treatment(date: str) -> dict:
    import json

    record = json.loads(GOLD_SET_PATH.read_text())
    for treatment in record["clinical_treatments"]:
        if treatment["treatment_date"] == date:
            return treatment
    raise AssertionError(f"no treatment dated {date} in the gold set")


def _assert_schema_shape(result: dict) -> None:
    assert set(result.keys()) >= {
        "trigger_present",
        "judgment_points",
        "draft_question",
        "prohibited_inference",
    }
    points = result["judgment_points"]
    for key in ("recognized", "corrective_action", "reassessed", "physician_notified"):
        assert key in points
        assert points[key]["status"] in ("documented", "evidence_gap")
        assert isinstance(points[key]["citation"], str)


@requires_live_key
def test_positive_case_schema_and_judgment():
    result = judge_hypotension_documentation(_treatment("2026-01-28"))
    _assert_schema_shape(result)
    assert result["trigger_present"] is True
    for key in ("recognized", "corrective_action", "reassessed", "physician_notified"):
        assert result["judgment_points"][key]["status"] == "documented"


@requires_live_key
def test_negative_case_schema_and_judgment():
    result = judge_hypotension_documentation(_treatment("2026-02-04"))
    _assert_schema_shape(result)
    assert result["trigger_present"] is True
    assert result["judgment_points"]["recognized"]["status"] == "documented"
    assert result["judgment_points"]["corrective_action"]["status"] == "documented"
    assert result["judgment_points"]["reassessed"]["status"] == "evidence_gap"
    assert result["judgment_points"]["physician_notified"]["status"] == "evidence_gap"
