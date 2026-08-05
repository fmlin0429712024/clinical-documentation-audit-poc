"""Deterministic escalation enforcement — Module 5 / Chapter 3.5, Chapter 9.1:
"when failure has financial, legal, or safety consequences—use hooks, not
prompts." A triggered audit finding not routed to human review is exactly
that kind of consequence, so this is not left to submit_finding's prompt
description alone.

PostToolUse fires after the tool call completes but before Claude sees the
result — this hook inspects the arguments Claude just submitted and blocks
(forcing a resubmission) if triggered=true but status != requires_human_review.
"""
from __future__ import annotations

from typing import Any

from claude_agent_sdk import HookMatcher

SUBMIT_FINDING_TOOL_NAME = "mcp__audit-tools__submit_finding"


async def enforce_escalation(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: Any,
) -> dict[str, Any]:
    if input_data.get("tool_name") != SUBMIT_FINDING_TOOL_NAME:
        return {}

    finding = input_data.get("tool_input", {})
    triggered = finding.get("triggered")
    status = finding.get("status")

    if triggered is True and status != "requires_human_review":
        return {
            "decision": "block",
            "reason": (
                f"Rejected: rule {finding.get('rule_id', '?')} has "
                f"triggered=true but status={status!r}. Every triggered "
                "finding must carry status='requires_human_review' — this "
                "is enforced here, not just requested in the tool "
                "description. Resubmit with the correct status."
            ),
        }

    if triggered is False and status == "requires_human_review":
        return {
            "decision": "block",
            "reason": (
                f"Rejected: rule {finding.get('rule_id', '?')} has "
                "triggered=false but status='requires_human_review'. A "
                "non-triggered rule should carry status='no_finding'. "
                "Resubmit with the correct status."
            ),
        }

    return {}


ESCALATION_HOOKS = {
    "PostToolUse": [
        HookMatcher(matcher=SUBMIT_FINDING_TOOL_NAME, hooks=[enforce_escalation]),
    ],
}
