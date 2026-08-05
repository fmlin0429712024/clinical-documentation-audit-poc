#!/usr/bin/env python3
"""Human resume step — the other half of coordinator.py's pause/persist.

Chapter 9.3's structured handoff protocol, applied here: "the human operator
does not have access to the full conversation transcript—they only see this
summary. Therefore it must be complete and self-contained." Each queue
record already carries the full submit_finding payload (rule, evidence,
judgment points, draft question) — nothing here assumes you saw the run.

Usage:
    uv run python3 resume_review.py list
    uv run python3 resume_review.py decide <index> confirm|reject|clarify "note"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

QUEUE_PATH = Path(__file__).resolve().parent / "review_queue.json"
VALID_DECISIONS = {"confirm", "reject", "clarify"}


def _load() -> list[dict]:
    if not QUEUE_PATH.exists():
        return []
    return json.loads(QUEUE_PATH.read_text())


def _save(queue: list[dict]) -> None:
    QUEUE_PATH.write_text(json.dumps(queue, indent=2))


def list_pending() -> None:
    queue = _load()
    pending = [(i, r) for i, r in enumerate(queue) if r["reviewer_decision"] is None]
    if not pending:
        print("No pending items.")
        return
    for i, record in pending:
        f = record["finding"]
        print(f"[{i}] {f['rule_id']} ({f['domain']}/{f['method']}) — queued {record['queued_at']}")
        print(f"    evidence: {f['evidence_summary']}")
        if f.get("judgment_points"):
            for p in f["judgment_points"]:
                print(f"      - {p['point']}: {p['point_status']} ({p['citation']})")
        if f.get("draft_question"):
            print(f"    draft question: {f['draft_question']}")
        print()


def decide(index: int, decision: str, note: str) -> None:
    if decision not in VALID_DECISIONS:
        raise SystemExit(f"decision must be one of {VALID_DECISIONS}, got {decision!r}")
    queue = _load()
    if index < 0 or index >= len(queue):
        raise SystemExit(f"No queue item at index {index} (queue has {len(queue)} items).")
    queue[index]["reviewer_decision"] = {"decision": decision, "note": note}
    _save(queue)
    print(f"Recorded '{decision}' for item [{index}] ({queue[index]['finding']['rule_id']}).")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("list", "decide"):
        raise SystemExit(__doc__)
    if sys.argv[1] == "list":
        list_pending()
    else:
        if len(sys.argv) < 5:
            raise SystemExit("usage: resume_review.py decide <index> confirm|reject|clarify \"note\"")
        decide(int(sys.argv[2]), sys.argv[3], sys.argv[4])
