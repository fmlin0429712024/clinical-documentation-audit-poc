#!/usr/bin/env python3
"""Part 2, non-deterministic path: one schema-enforced Claude API call per
treatment needing judgment. Contrast with deterministic.py -- this file
DOES import anthropic, deliberately, because this is the one task that's
genuinely a judgment call, not a formula.

The narrative use-case description is loaded at runtime from the copied
skill markdown (skills/intradialytic-hypotension-review/SKILL.md) rather
than duplicated into a Python string -- one source of truth, not two to
keep in sync. Only the body transfers; the frontmatter (allowed-tools,
disallowed-tools) doesn't mean anything to a direct API call -- tool
access here is the `tools=[FINDING_TOOL]` list below, actual code, not a
YAML declaration.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(dotenv_path=HERE / ".env")

sys.path.insert(0, str(HERE))
from schemas import FINDING_TOOL  # noqa: E402

REPO_ROOT = HERE.parent
GOLD_SET_PATH = REPO_ROOT / "data" / "synthetic-ichd-patient-goldset.json"
SKILL_PATH = HERE / "skills" / "intradialytic-hypotension-review" / "SKILL.md"
MODEL = "claude-haiku-4-5-20251001"


def load_skill_body(skill_path: Path = SKILL_PATH) -> str:
    """Strip the YAML frontmatter, return the prose body."""
    text = skill_path.read_text()
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL).strip()


def judge_hypotension_documentation(
    treatment: dict, client: "anthropic.Anthropic | None" = None
) -> dict:
    client = client or anthropic.Anthropic()
    skill_body = load_skill_body()

    prompt = (
        f"{skill_body}\n\n"
        "---\n\n"
        "Apply the above to this synthetic treatment record. Call "
        "submit_hypotension_finding exactly once with your judgment.\n\n"
        f"treatment_note: {treatment.get('treatment_note', 'not_present')}\n"
        f"follow_up_note: {treatment.get('follow_up_note', 'not_present')}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[FINDING_TOOL],
        tool_choice={"type": "tool", "name": "submit_hypotension_finding"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_hypotension_finding":
            return block.input

    raise RuntimeError("Model did not call submit_hypotension_finding")


if __name__ == "__main__":
    record = json.loads(GOLD_SET_PATH.read_text())
    date_filter = sys.argv[1] if len(sys.argv) > 1 else None
    for treatment in record["clinical_treatments"]:
        if date_filter and treatment["treatment_date"] != date_filter:
            continue
        result = judge_hypotension_documentation(treatment)
        print(json.dumps({"treatment_date": treatment["treatment_date"], **result}, indent=2))
