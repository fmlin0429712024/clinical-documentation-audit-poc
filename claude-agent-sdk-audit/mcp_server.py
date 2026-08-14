#!/usr/bin/env python3
"""External MCP server (stdio transport) — exposes query_deterministic_rule.

Deliberately NOT an in-process SDK MCP server (create_sdk_mcp_server).
This is a standalone process, run via `command`/`args` in ClaudeAgentOptions'
mcp_servers config, connected over stdio — the same shape as a `.mcp.json`
entry. It's a real MCP server: any MCP client (Claude Code, Claude Desktop,
another SDK app) could launch and talk to this exact file, not just this
project's coordinator.

Wraps tools/query_deterministic_rule.py (imported, not shelled out) against
BOTH SOP stores — the caller passes db_path explicitly, same as the CLI's
--db flag. Errors are structured (Module 1 / Chapter 4.4 guidance: an agent
can't decide whether to retry, skip, or escalate from a bare "failed"
string), distinguishing unknown_rule_id / missing_field / store_not_found.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.query_deterministic_rule import DB_PATH, evaluate, load_rule  # noqa: E402

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="ichd-deterministic-rules")

DEFAULT_DB = str(DB_PATH)
MULTI_DOMAIN_DB = str(REPO_ROOT / "data" / "audit_rules-multi-domain.db")


@mcp.tool()
def query_deterministic_rule(
    rule_id: str,
    record: dict[str, Any],
    db: str = "default",
) -> dict[str, Any]:
    """Evaluate one deterministic ICHD audit rule against one record.

    Zero LLM judgment — this looks up the rule's threshold/operator from a
    SQLite SOP store and computes the verdict in code. The caller reports
    the result verbatim; it must never re-derive or second-guess it.

    Args:
        rule_id: e.g. "SYN-ICHD-01", "SYN-ICHD-09" (treatment domain,
            default store) or "SYN-ICHD-06" (patient domain, multi-domain
            store).
        record: the treatment dict (for treatment-domain rules) or a
            minimal derived object like {"nursing_notes_count": 2} (for
            SYN-ICHD-06). Field names must match the rule's field_a/field_b.
        db: "default" for data/audit_rules.db (treatment-domain rules,
            SYN-ICHD-01/09 — this is the store shared with Phase 1/2, never
            extended) or "multi-domain" for data/audit_rules-multi-domain.db
            (patient-domain rules, currently only SYN-ICHD-06).

    Returns a structured result. On failure, "isError" is true and "error"
    names one of: "unknown_rule_id", "missing_field", "store_not_found" —
    never a bare exception string, so the caller can decide whether to
    retry with a different db, skip, or escalate.
    """
    if db not in ("default", "multi-domain"):
        return {
            "isError": True,
            "error": "store_not_found",
            "message": f"db must be 'default' or 'multi-domain', got {db!r}",
        }
    db_path = Path(DEFAULT_DB if db == "default" else MULTI_DOMAIN_DB)
    if not db_path.exists():
        return {
            "isError": True,
            "error": "store_not_found",
            "message": f"SOP store not found at {db_path}",
        }

    try:
        rule = load_rule(rule_id, db_path)
    except SystemExit:
        return {
            "isError": True,
            "error": "unknown_rule_id",
            "message": f"{rule_id!r} is not defined in the {db} store ({db_path.name}).",
        }

    try:
        result = evaluate(rule, record)
    except KeyError as exc:
        return {
            "isError": True,
            "error": "missing_field",
            "message": f"Record is missing required field {exc}; rule {rule_id} needs it.",
        }

    return {"isError": False, **result}


if __name__ == "__main__":
    mcp.run(transport="stdio")
