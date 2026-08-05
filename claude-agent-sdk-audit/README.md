# Part 2.5: Claude Agent SDK — Real Multi-Agent

Same ICHD documentation-audit content as the rest of this repo, this time
as a **real multi-agent system** using the Claude Agent SDK — not Claude
Code Skills (Phase 1.5) and not a single-agent direct-API script
(`claude-sdk-audit/`, Phase 2). See `../docs/prd-claude-agent-sdk-multi-agent.md`
for the full design and the exam-module → build-item mapping.

**Naming note:** `claude-sdk-audit/` (Phase 2) is single-agent, direct API
calls, no agentic loop. This folder is multi-agent, real subagents with
independent context, dispatched via the Task tool. One word apart in the
name, three agents apart in architecture.

## Setup

```bash
cd claude-agent-sdk-audit
uv sync
cp .env.example .env   # then paste your real ANTHROPIC_API_KEY into .env
```

`data/` and `tools/query_deterministic_rule.py` are referenced from the
repo root by path (imported, not copied or shelled out) — same convention
as `claude-sdk-audit/`. Uses the multi-domain gold set
(`data/synthetic-ichd-patient-goldset-multi-domain.json`) and **both**
SOP stores (`data/audit_rules.db` for treatment-domain rules,
`data/audit_rules-multi-domain.db` for the patient-domain one) — neither
is modified by anything in this folder.

## What's here

| File | Role |
| --- | --- |
| `mcp_server.py` | External MCP server (stdio transport, its own process) exposing `query_deterministic_rule`. Run standalone or spawned by `coordinator.py` via `command`/`args`. |
| `native_tools.py` | In-process (SDK MCP server) tools: `get_patient_context`, `get_treatment_context`, `submit_finding`. Deliberately the *other* half of the native-vs-external MCP comparison — same protocol, different transport. Named to avoid shadowing the repo-root `tools/` package that `mcp_server.py` imports from. |
| `subagents.py` | `AgentDefinition`s for `patient_domain_auditor` and `treatment_domain_auditor` — each with a domain-scoped `tools` allowlist and a prompt carrying its rules' judgment criteria plus one worked positive/negative example per non-deterministic rule (few-shot). |
| `hooks.py` | `PostToolUse` hook on `submit_finding` — deterministically blocks (forces resubmission) if `triggered=true` but `status != requires_human_review`, or vice versa. Not trusted to the tool description alone. |
| `coordinator.py` | `audit_coordinator` — dispatches both subagents via Task, aggregates their findings, runs a plain-Python evaluator (schema check, not a third LLM call), writes triggered findings to `review_queue.json`. |
| `resume_review.py` | Human resume step: `list` pending items, `decide <index> confirm\|reject\|clarify "note"`. Each queue record is self-contained (Chapter 9.3) — no conversation transcript needed to review it. |

## Run it

```bash
uv run python3 coordinator.py          # full audit, both domains, writes review_queue.json
uv run python3 resume_review.py list
uv run python3 resume_review.py decide 0 confirm "matches the worked example"
```

`mcp_server.py` can also be run/inspected standalone — it's a real, independent MCP server, not an SDK-internal helper:

```bash
uv run python3 mcp_server.py           # starts, waits on stdio (Ctrl+C to stop)
```

## Exam-module coverage

See `../docs/prd-claude-agent-sdk-multi-agent.md` Section 3 for the full
traceability table. Summary: agentic loop / tool definitions (Module 1),
Task-based hub-and-spoke with isolated subagent context (Module 2), MCP —
one external server + one in-process server, side by side (Module 3),
few-shot + deterministic/non-deterministic split (Module 4, partial —
dynamic decomposition explicitly out of scope), Hooks + plain-code
evaluator + pause/persist/resume (Module 5), `allowed_tools` as a real
per-subagent whitelist (Module 6, partial — Batch API explicitly out of
scope).
