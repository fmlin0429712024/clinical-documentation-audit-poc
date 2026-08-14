"""Native (in-process) Agent SDK tools — the counterpart to mcp_server.py.

Built with @tool + create_sdk_mcp_server: an in-process MCP server that
runs inside this application, no subprocess. Deliberately the *other* half
of the native-vs-external comparison this PRD asked for (see
docs/prd-claude-agent-sdk-multi-agent.md Section 5) — query_deterministic_rule
is the external stdio server in mcp_server.py; these two are in-process.

get_patient_context / get_treatment_context: read-only, domain-scoped data
access. Neither subagent gets raw file access — only these tool calls.

submit_finding: the forced-structured-output tool both subagents call to
report a result. Its schema is the single source of truth hooks.py's
PostToolUse hook validates against (Module 5 / Chapter 3.5: escalation
enforced in code, not trusted to a prompt instruction).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from claude_agent_sdk import create_sdk_mcp_server, tool

GOLD_SET_PATH = REPO_ROOT / "data" / "synthetic-ichd-patient-goldset-multi-domain.json"


def _load_gold_set() -> dict[str, Any]:
    return json.loads(GOLD_SET_PATH.read_text())


@tool(
    "get_patient_context",
    "Read patient-level context for the synthetic ICHD patient: patient "
    "identifiers plus one nursing_notes entry (given its note_date), plus "
    "the next relevant treatment record after that date (the earliest "
    "clinical_treatments[] entry dated after note_date — a chronological "
    "fact, not a judgment). Patient-domain scope only: does not return "
    "other treatments. Returns isError + a structured error code "
    "('note_not_found') if note_date doesn't match any nursing_notes entry.",
    {"note_date": str},
)
async def get_patient_context(args: dict[str, Any]) -> dict[str, Any]:
    record = _load_gold_set()
    note_date = args["note_date"]
    note = next(
        (n for n in record["patient"]["nursing_notes"] if n["note_date"] == note_date),
        None,
    )
    if note is None:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "error": "note_not_found",
                            "message": f"No nursing_notes entry dated {note_date}.",
                        }
                    ),
                }
            ],
            "isError": True,
        }

    later = [
        t for t in record["clinical_treatments"] if t["treatment_date"] > note_date
    ]
    next_treatment = min(later, key=lambda t: t["treatment_date"]) if later else None

    payload = {
        "synthetic_patient_id": record["patient"]["synthetic_patient_id"],
        "nursing_note": note,
        "next_relevant_treatment": next_treatment,
    }
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]}


@tool(
    "get_treatment_context",
    "Read one clinical_treatments[] entry for the synthetic ICHD patient "
    "by treatment_date. Treatment-domain scope only: does not return "
    "patient-level fields like nursing_notes. Returns isError + a "
    "structured error code ('treatment_not_found') if the date doesn't "
    "match any treatment.",
    {"treatment_date": str},
)
async def get_treatment_context(args: dict[str, Any]) -> dict[str, Any]:
    record = _load_gold_set()
    treatment_date = args["treatment_date"]
    treatment = next(
        (
            t
            for t in record["clinical_treatments"]
            if t["treatment_date"] == treatment_date
        ),
        None,
    )
    if treatment is None:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "error": "treatment_not_found",
                            "message": f"No clinical_treatments[] entry dated {treatment_date}.",
                        }
                    ),
                }
            ],
            "isError": True,
        }
    return {"content": [{"type": "text", "text": json.dumps(treatment, indent=2)}]}


SUBMIT_FINDING_SCHEMA = {
    "type": "object",
    "properties": {
        "rule_id": {"type": "string"},
        "domain": {"type": "string", "enum": ["patient", "treatment"]},
        "method": {"type": "string", "enum": ["deterministic", "non-deterministic"]},
        "triggered": {"type": "boolean"},
        "status": {"type": "string", "enum": ["requires_human_review", "no_finding"]},
        "evidence_summary": {
            "type": "string",
            "description": "One or two sentences citing the exact source field(s).",
        },
        "judgment_points": {
            "type": "array",
            "description": "Empty for deterministic rules. For non-deterministic rules, one entry per judgment point.",
            "items": {
                "type": "object",
                "properties": {
                    "point": {"type": "string"},
                    "point_status": {
                        "type": "string",
                        "enum": ["documented", "evidence_gap", "not_applicable"],
                    },
                    "citation": {"type": "string"},
                },
                "required": ["point", "point_status", "citation"],
            },
        },
        "draft_question": {"type": ["string", "null"]},
        "prohibited_inference": {"type": "string"},
    },
    "required": [
        "rule_id",
        "domain",
        "method",
        "triggered",
        "status",
        "evidence_summary",
        "judgment_points",
        "prohibited_inference",
    ],
}


@tool(
    "submit_finding",
    "Submit one rule's audit finding in the shared structured schema. "
    "Call this exactly once per rule evaluated — it is the only way a "
    "finding reaches the coordinator. If 'triggered' is true, 'status' "
    "MUST be 'requires_human_review' (enforced by a hook, not just this "
    "description — an incorrect status will be rejected and you'll be "
    "asked to resubmit). Never assign a diagnosis, code, clinical "
    "severity, or payment result anywhere in this submission.",
    SUBMIT_FINDING_SCHEMA,
)
async def submit_finding(args: dict[str, Any]) -> dict[str, Any]:
    # The hook (hooks.py, PostToolUse on this tool) is what actually
    # enforces the triggered->status invariant. This handler just echoes
    # the finding back as confirmation; it does not judge or store it —
    # the coordinator reads the finding from the transcript, and hooks.py
    # enforces the rule the description promises.
    return {
        "content": [
            {
                "type": "text",
                "text": f"Finding recorded for {args.get('rule_id', '?')}.",
            }
        ],
        "structuredContent": args,
    }


audit_tools_server = create_sdk_mcp_server(
    name="audit-tools",
    version="1.0.0",
    tools=[get_patient_context, get_treatment_context, submit_finding],
)
