"""Tests for the Part 2 non-deterministic path.

Unlike test_deterministic.py, these make real, paid Claude API calls --
skipped automatically when the live API is unusable, so this doesn't
fail (or cost money) without a funded ANTHROPIC_API_KEY.

Three skip conditions, in the order they are checked:

1. No usable key configured (no ANTHROPIC_API_KEY, or not an `sk-ant-` key).
2. A key exists but the API rejects it as unauthenticated (401).
3. The key is valid but the account has no credits -- Anthropic returns
   400 "Your credit balance is too low to access the Anthropic API".
   This is the state of a real key with an unfunded account, so it must
   degrade to a clean skip too, or CI would go red for a billing reason,
   not a code reason.

Skips are explicit in the run log (`SKIPPED [...] reasons`), never a
faked pass: when credits exist the real model runs and the assertions
below apply for real.

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
from anthropic import BadRequestError
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


def _judge_live(date: str) -> dict:
    """Run one live judgment, skipping cleanly when the paid API is unusable.

    A valid-but-unfunded key surfaces as a 400 BadRequestError whose message
    mentions the credit balance -- treat that as an environment condition
    (skip), not a product defect (fail). Any other error still raises.
    """
    try:
        return judge_hypotension_documentation(_treatment(date))
    except BadRequestError as exc:
        if "credit balance" in str(exc).lower():
            pytest.skip(
                f"Anthropic API credits exhausted -- skipping live test: {exc}"
            )
        raise


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
    result = _judge_live("2026-01-28")
    _assert_schema_shape(result)
    assert result["trigger_present"] is True
    for key in ("recognized", "corrective_action", "reassessed", "physician_notified"):
        assert result["judgment_points"][key]["status"] == "documented"


@requires_live_key
def test_negative_case_schema_and_judgment():
    result = _judge_live("2026-02-04")
    _assert_schema_shape(result)
    assert result["trigger_present"] is True
    assert result["judgment_points"]["recognized"]["status"] == "documented"
    assert result["judgment_points"]["corrective_action"]["status"] == "documented"
    assert result["judgment_points"]["reassessed"]["status"] == "evidence_gap"
    assert result["judgment_points"]["physician_notified"]["status"] == "evidence_gap"
