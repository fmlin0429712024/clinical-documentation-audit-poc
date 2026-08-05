"""audit_coordinator — the collaboration role, real multi-agent version.

Hub-and-spoke (Chapter 3.3): this coordinator dispatches to the two domain
subagents via the Task tool, waits for both, and aggregates. It does not
own any audit evidence itself — same principle as Phase 1.5's
clinical-audit-orchestrator skill, now backed by real subagent isolation
instead of a single Claude Code session.

The evaluator step (Module 5: compare structured outputs with plain code,
not another LLM call) runs after the coordinator's own turn completes,
against the JSON it reports — no second model call needed since both
subagents already emit the same submit_finding schema.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ichd-deterministic-rules (mcp_server.py) is an external subprocess — by
# default the SDK connects to MCP servers non-blockingly, so the first
# turn can start before it's ready and the subagent never discovers the
# tool exists. Force a bounded wait instead (observed empirically: without
# this, deterministic-rule findings were silently missing from a live run
# — not an error, just an empty gap, which is worse).
os.environ.setdefault("MCP_CONNECTION_NONBLOCKING", "0")
os.environ.setdefault("MCP_CONNECT_TIMEOUT_MS", "15000")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query  # noqa: E402

from hooks import ESCALATION_HOOKS  # noqa: E402
from subagents import AUDIT_TOOLS, RULE_TOOL, SUBAGENTS  # noqa: E402
from native_tools import audit_tools_server  # noqa: E402

REVIEW_QUEUE_PATH = HERE / "review_queue.json"

COORDINATOR_PROMPT = """\
You are the collaboration/orchestrator agent for a synthetic ICHD documentation-audit
system. You own no evidence yourself — you dispatch to two subagents and aggregate.

You have two subagents available via the Task tool: patient_domain_auditor and
treatment_domain_auditor. Dispatch to BOTH, in parallel (two Task calls in the same
turn), each with the specific dates/scope it needs to check — do not assume either
subagent knows anything beyond what you put in its Task prompt.

Once both subagents report back, compile every finding they returned (they each call
submit_finding once per rule) into ONE final JSON array, and output it as your only
response, inside a ```json fenced block, no other prose. Each array element must be
exactly one subagent's submit_finding arguments, verbatim — do not summarize,
paraphrase, or add commentary. If a subagent's Task result doesn't include a finding
you expected, still list what it did return; do not silently drop coverage."""


def _dispatch_prompt(gold_set_path: str) -> str:
    return f"""\
Audit the synthetic patient in {gold_set_path} across both domains:

- treatment_domain_auditor: check SYN-ICHD-01/02/04/09 for the treatments dated
  2026-01-14, 2026-01-28, 2026-02-04, 2026-02-11, 2026-02-18, 2026-03-04, 2026-03-18.
- patient_domain_auditor: check SYN-ICHD-06 (patient-level) and SYN-ICHD-05 for the
  nursing_notes entries dated 2026-03-02 and 2026-03-16.

Pass this exact scope into each Task prompt — don't let either subagent guess it."""


def _extract_json_array(text: str) -> list[dict[str, Any]]:
    match = re.search(r"```json\s*(\[.*?\])\s*```", text, re.DOTALL)
    raw = match.group(1) if match else text
    return json.loads(raw)


def _evaluate(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Plain-code evaluator: schema conformance + triggered/clean split.

    Not an LLM call (Module 5) — both subagents already share one schema
    (tools.SUBMIT_FINDING_SCHEMA), so this is a direct structural check.
    """
    required = {
        "rule_id",
        "domain",
        "method",
        "triggered",
        "status",
        "evidence_summary",
        "judgment_points",
        "prohibited_inference",
    }
    valid, invalid = [], []
    for f in findings:
        missing = required - f.keys()
        bad_status = f.get("triggered") is True and f.get("status") != "requires_human_review"
        if missing or bad_status:
            invalid.append({"finding": f, "missing_fields": sorted(missing), "bad_status": bad_status})
        else:
            valid.append(f)

    triggered = [f for f in valid if f["triggered"]]
    return {
        "total_findings": len(findings),
        "schema_valid": len(valid),
        "schema_invalid": invalid,
        "triggered_count": len(triggered),
        "clean_count": len(valid) - len(triggered),
    }


def _write_review_queue(triggered: list[dict[str, Any]]) -> None:
    """Pause/persist/resume (Chapter 11.6's state-persistence pattern,
    applied to human escalation instead of crash recovery): append
    self-contained records, don't block waiting for a human synchronously.
    """
    existing = json.loads(REVIEW_QUEUE_PATH.read_text()) if REVIEW_QUEUE_PATH.exists() else []
    now = datetime.now(timezone.utc).isoformat()
    for finding in triggered:
        existing.append(
            {
                "queued_at": now,
                "reviewer_decision": None,
                "finding": finding,
            }
        )
    REVIEW_QUEUE_PATH.write_text(json.dumps(existing, indent=2))


async def run_audit(gold_set_path: str | None = None) -> dict[str, Any]:
    gold_set_path = gold_set_path or str(
        HERE.parent / "data" / "synthetic-ichd-patient-goldset-multi-domain.json"
    )

    options = ClaudeAgentOptions(
        system_prompt=COORDINATOR_PROMPT,
        agents=SUBAGENTS,
        mcp_servers={
            "audit-tools": audit_tools_server,
            "ichd-deterministic-rules": {
                "type": "stdio",
                "command": sys.executable,
                "args": [str(HERE / "mcp_server.py")],
            },
        },
        allowed_tools=["Task", *AUDIT_TOOLS, RULE_TOOL],
        hooks=ESCALATION_HOOKS,
    )

    result_text = None
    async for message in query(prompt=_dispatch_prompt(gold_set_path), options=options):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            result_text = message.result

    if result_text is None:
        raise RuntimeError("Coordinator run produced no ResultMessage — nothing to evaluate.")

    findings = _extract_json_array(result_text)
    evaluation = _evaluate(findings)
    triggered = [f for f in findings if f.get("triggered") is True]
    _write_review_queue(triggered)

    return {
        "findings": findings,
        "evaluation": evaluation,
        "queued_for_review": len(triggered),
    }


if __name__ == "__main__":
    outcome = asyncio.run(run_audit())
    print(json.dumps(outcome, indent=2))
