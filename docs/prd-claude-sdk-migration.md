# PRD: Claude SDK Migration (Part 2)

Status: **Draft v0.1 — under review, nothing built yet**
Owner: Forest Lin
Depends on: Part 1 (`docs/prd-agentic-audit-tracks.md`), concluded and not being re-litigated here.
Scope: reimplement Part 1's two audit tracks using the Claude/Anthropic Python SDK directly, outside Claude Code. **No GitHub/CI work here** — that's Part 3, and won't be designed until this exists to test against.

## 1. Purpose

Part 1 proved the two-track pattern (deterministic vs. non-deterministic audit rules) inside Claude Code, but two things were structurally impossible to guarantee there, both raised explicitly during Part 1 review:

1. **Output format** — Part 1's `Output Contract` sections are prose the model tries to follow; nothing validates or enforces the shape of the response.
2. **"Zero LLM" for deterministic rules** — Part 1 could only guarantee the *verdict* wasn't computed by the LLM. The surrounding orchestration (deciding to loop, deciding to call the tool) was still an LLM-driven agent loop we don't control, because Claude Code's own loop isn't our code.

Part 2 exists to close both gaps by writing the orchestration ourselves: a plain Python script that (a) never calls the Anthropic API at all for deterministic rules, and (b) forces the non-deterministic judgment through a schema (tool-use `input_schema`) so the response is validated, not just requested nicely.

## 2. Goals

1. Reproduce Part 1's behavior on the same gold set: same triggers, same judgment outcomes for the two hypotension cases (`2026-01-28` clean, `2026-02-04` two gaps).
2. Make the "zero LLM in the deterministic path" guarantee literal — provable by inspection (no `anthropic` import/call anywhere in that code path), not just documented intent.
3. Make the non-deterministic finding's output shape enforced by the API (tool-use schema), not prose-requested.
4. Practice the actual mechanics: defining a tool `input_schema`, forcing `tool_choice`, parsing a guaranteed-shape response — this is the concrete "exam" skill this phase is for.

## 3. Non-goals

- No GitHub Actions / CI / headless deployment (Part 3).
- No evaluation-loop persistence layer (Part 4) — a stub/TODO is fine if it comes up naturally, not a deliverable.
- No re-implementation of `SYN-ICHD-02`/`03` — Part 1 never fully realized these (no dedicated handling, no test data); Part 2 stays scoped to the three rules Part 1 actually finished: `SYN-ICHD-01`, `SYN-ICHD-09` (deterministic), `SYN-ICHD-04` (non-deterministic).
- No attempt to reproduce Claude Code's general-purpose agent loop (autonomous multi-turn tool selection). See Section 4 — this is a deliberate scope boundary, not an oversight.

## 4. Architecture decision: direct API calls, not an autonomous agent loop

**Open question needing your confirmation before anything is built:** "Claude SDK" can mean two different things, and they lead to different designs:

- **(a) Direct/manual**: use the plain `anthropic` Python SDK to make single, controlled `messages.create()` calls. *We* write the control flow (the `for` loop over treatments, the `if` deciding deterministic vs. non-deterministic). The model is only ever invoked for the one non-deterministic judgment call, with a forced tool schema. No autonomous multi-step tool use by the model.
- **(b) Agentic loop (Claude Agent SDK)**: use Anthropic's higher-level agent framework, where the model itself decides which tools to call and when — architecturally similar to what Claude Code is built on. This would let the model "decide" to loop over treatments and call tools, which reintroduces exactly the ambiguity Part 2 exists to eliminate for the deterministic path.

**This PRD assumes (a)** — direct, manually-orchestrated API calls — because it's the only design that delivers Goal 2 (a literal, inspectable "zero LLM" guarantee) and matches how you described it earlier in this project ("we write our own Python... using the LLM through the Python," "all the agent is under our control"). Flagging this explicitly because getting it wrong changes the whole architecture below — confirm before I build anything.

## 5. Deterministic path — pure Python, no SDK call

Reuse `tools/query_deterministic_rule.py` directly as an importable module (`load_rule`, `evaluate`, `list_rules`) rather than shelling out to it — Part 2's script can `import` it because we're not agent-mediated anymore; there's no Bash tool in the way. This is actually simpler than Part 1's version, not more complex: one Python process, one function call, no subprocess boundary.

```python
from tools.query_deterministic_rule import list_rules, evaluate, load_rule
# no `import anthropic` anywhere in this file
```

Loop: for each treatment in the gold set, for each rule from `list_rules()`, call `evaluate(rule, treatment)`. Identical logic to `deterministic-rule-audit`'s skill Workflow — just expressed as literal Python instead of agent instructions.

## 6. Non-deterministic path — schema-enforced API call

One `messages.create()` call per (treatment, rule) pair needing judgment (currently just `SYN-ICHD-04`), with a forced tool call:

```python
FINDING_TOOL = {
    "name": "submit_hypotension_finding",
    "description": "Submit the four-point hypotension documentation judgment.",
    "input_schema": {
        "type": "object",
        "properties": {
            "trigger_present": {"type": "boolean"},
            "judgment_points": {
                "type": "object",
                "properties": {
                    "recognized": {"$ref": "#/$defs/point"},
                    "corrective_action": {"$ref": "#/$defs/point"},
                    "reassessed": {"$ref": "#/$defs/point"},
                    "physician_notified": {"$ref": "#/$defs/point"}
                },
                "required": ["recognized", "corrective_action", "reassessed", "physician_notified"]
            },
            "draft_question": {"type": "string"},
        },
        "$defs": {
            "point": {
                "type": "object",
                "properties": {
                    "status": {"enum": ["documented", "evidence_gap"]},
                    "citation": {"type": "string"}
                },
                "required": ["status", "citation"]
            }
        },
        "required": ["trigger_present", "judgment_points", "draft_question"]
    }
}
```

The system/user prompt carries the same narrative use-case description already written in `intradialytic-hypotension-review/SKILL.md` — that text doesn't need to be rewritten, just relocated from a skill file into a Python string (or loaded from the skill file directly, to avoid duplicating it — worth deciding during implementation, not here). `tool_choice` forced to `submit_hypotension_finding`, so the response is guaranteed to parse as valid JSON matching the schema — no prose to parse, no "did it follow the format" uncertainty.

## 7. Method dispatch also becomes plain Python

In Part 1, "which rules are deterministic vs. non-deterministic" was read from `rules/synthetic-audit-rules.md`'s Method column by an LLM-driven agent. In Part 2, that's a fact we already know at code-writing time — no reason to make the model re-derive it. A small Python constant (or reading the existing SQLite table for the two deterministic rule IDs, treating anything else relevant as non-deterministic) replaces that step entirely. This reinforces the theme: **everything that can be a fact in code should be code; the model is invoked only for the one task that's genuinely a judgment call.**

## 8. Proposed repository layout

```
sdk/
  deterministic.py      # imports tools/query_deterministic_rule.py directly
  nondeterministic.py   # anthropic API call + FINDING_TOOL schema
  run_audit.py          # orchestration: loop treatments, dispatch, print findings
tests/
  test_sdk_deterministic.py   # same-shape tests as Part 1's, via direct import not subprocess
  test_sdk_nondeterministic.py # schema-validates a captured/fixture response; does NOT assert on judgment content, since that's model output — see Section 10
```

This is the first point in the project with a real external dependency (`anthropic`), so a minimal `pyproject.toml` + `uv sync` becomes justified — unlike the abandoned Part 1 attempt to packagize a plain stdlib script, which was correctly reverted as premature. Also needs: `ANTHROPIC_API_KEY` handling (environment variable, never committed — add `.env` to `.gitignore` if a `.env` file is used).

## 9. Success criteria

- `python3 sdk/run_audit.py` against the same gold set produces the same triggers as Part 1 for all three rules, across all existing treatments.
- Deterministic path: zero `anthropic` API calls, verifiable by code inspection (no import) — not just "the tests passed."
- Non-deterministic path: response is schema-valid on every call (no parse failures), tested against both the `2026-01-28` and `2026-02-04` treatments, matching Part 1's worked examples in `outputs/`.

## 10. What "testing" means differently here

Same caveat as Part 1's testing guide, worth restating because it applies even harder here: schema-validity is testable and should be asserted (did the API return well-formed JSON matching `FINDING_TOOL`'s schema — yes/no, deterministic to check). Whether the model's *judgment* is correct (did it call `2026-02-04` a 2-gap case) is not something a schema can guarantee — schema enforcement fixes the shape problem, not the accuracy problem. Don't conflate "the output is schema-valid" with "the output is correct" when reporting results.

## 11. Open questions for review

1. Confirm the direct-API-calls architecture (Section 4) is what you mean by "Claude SDK" here, not the autonomous Claude Agent SDK loop.
2. `uv` for dependency management — same tool already available in this environment — okay to use, or prefer plain `pip` + `requirements.txt`?
3. Where should the hypotension use-case narrative live — duplicated into a Python string, or loaded at runtime from `intradialytic-hypotension-review/SKILL.md` so Part 1 and Part 2 share one source of truth? (Leaning toward loading it — avoids drift — but that couples Part 2 to a Part 1 file path, worth deciding deliberately.)
4. Model choice for the API calls — pin a specific model, or leave configurable?
