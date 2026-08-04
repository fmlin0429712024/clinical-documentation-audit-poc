# Part 2: Claude SDK Audit

Same ICHD documentation-audit workflow as the repo root (Part 1, Claude Code + Skills), reimplemented as direct Python + Claude API calls — no Claude Code agent in the loop. See `../docs/prd-claude-sdk-migration.md` for the design rationale.

## Setup

```bash
cd claude-sdk-audit
uv sync
cp .env.example .env   # then paste your real ANTHROPIC_API_KEY into .env
```

`data/` and `tools/query_deterministic_rule.py` are referenced from the repo root (single source of truth, not copied). `skills/` is a copy of the repo root's `.claude/skills/` — decoupled on purpose, since this folder consumes the skill markdown differently (as prompt text, not via the Claude Code skill mechanism).

## What's here

| File | Track | What it does |
| --- | --- | --- |
| `deterministic.py` | deterministic | Pure Python. Imports `tools/query_deterministic_rule.py` directly and loops every treatment × every rule. **No `anthropic` import anywhere in this file** — enforced by `test_deterministic.py`. |
| `schemas.py` | non-deterministic | The `input_schema` for a forced tool call (`submit_hypotension_finding`) — this is what makes the output format an API-enforced guarantee instead of prose Claude Code hopes the model follows. |
| `nondeterministic.py` | non-deterministic | One Claude API call per treatment needing judgment. Loads `skills/intradialytic-hypotension-review/SKILL.md`'s body at runtime as the prompt (frontmatter stripped — `allowed-tools`/`disallowed-tools` don't mean anything to a raw API call). |
| `run_audit.py` | both | Orchestrator. Method dispatch (deterministic vs. non-deterministic) is a plain Python fact here, not something an LLM re-derives from a rules table. |

## Run it

```bash
uv run pytest -v                    # 3 deterministic tests always run; 2 live API tests
                                     # skip automatically if ANTHROPIC_API_KEY isn't set
uv run python3 deterministic.py     # deterministic checks only, no API calls
uv run python3 nondeterministic.py 2026-02-04   # one live judgment call
uv run python3 run_audit.py         # full audit, both tracks, all treatments
```

`outputs/` has captured example runs, including the raw schema-valid JSON from live calls.
