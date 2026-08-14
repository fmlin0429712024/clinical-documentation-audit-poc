# PRD: Multi-Agent Claude Agent SDK (Phase 2.5)

Status: **v0.1 — draft, nothing built yet**
Owner: Forest Lin
Depends on: Phase 1.5 (`docs/prd-multi-agent-domain-split.md`, concluded) — this PRD ports its validated 3-role design (collaboration / patient / treatment) from Claude Code Skills into a real multi-agent Claude Agent SDK implementation. Same relationship Phase 2 has to Phase 1.
Scope: a new, self-contained folder **`claude-agent-sdk-audit/`** (sibling to `claude-sdk-audit/`), own `pyproject.toml`/`uv.lock`/README, Python (matching Phase 2's language choice for the `claude-sdk-audit` ↔ `claude-agent-sdk-audit` naming pair).

## 1. Purpose

Practice the Claude Agent SDK's real mechanics — this is explicit exam-prep, not just an architecture exercise. The user supplied a 6-module exam knowledge summary (`claude-agent-sdk-exam-summary.md`, not committed to the repo — personal study material); this PRD's job is to map each module to a concrete, working piece of this project rather than a generic tutorial exercise. Section 3 is the traceability table between exam module and build item.

Phase 1.5 already validated *what* the three roles should do (patient-domain vs. treatment-domain vs. collaboration/orchestration) and *what* the six rules require. Phase 2.5 does not re-decide any of that — it only changes the *mechanism*: Skills (single session, prompt-driven) become real subagents (independent context, SDK-orchestrated).

## 2. Scope decisions (resolved with the user before drafting)

| Exam topic | Decision | Why |
| --- | --- | --- |
| MCP (Module 3) | **Partial — one tool only** (went in scope → out of scope → this compromise, in that order) | The three tools this build needs (Section 5) get built regardless of MCP; MCP only changes *how one of them* is registered. `query_deterministic_rule` is exposed via a small MCP server; `get_patient_context`/`get_treatment_context` are native Agent SDK tools. Lets both mechanisms be compared side by side without doubling the tool surface — closes the user's self-flagged MCP gap at low incremental cost. |
| Dynamic decomposition (Module 4) | **Out of scope** | User is studying this independently; including it would need a new data scenario purpose-built for it, which risks scope creep into a build that's already large. |
| Batch API (Module 6) | **Out of scope** | User has already studied it; our dataset (one patient) can't demonstrate its real value (throughput/cost at scale) anyway — a token demo wouldn't teach anything a real understanding hasn't already covered. |

Deterministic vs. non-deterministic (Module 4's other half) and tool-whitelisting (Module 6's other half) are already this project's foundation since Phase 1 — no new decision needed, just carried forward.

## 3. Exam module → build item traceability

| Module | Exam concept | Where it lands in this build |
| --- | --- | --- |
| 1. API Fundamentals | Agentic loop (`stop_reason`), tool `name`/`description`/`input_schema`, structured (not generic) tool errors | Every tool (both the MCP-exposed one and the two native ones, Section 5) returns typed error shapes (`unknown_rule_id`, `missing_field`, `store_not_found`) instead of a raised exception string. Tool descriptions written like onboarding docs, not code comments — same discipline Phase 1's skill descriptions already used. |
| 2. Multi-Agent Architecture | Hub-and-spoke, Task-tool orchestration vs. subagent `allowed_tools` as separate concerns, subagents are independent API calls with **no inherited context** | `audit_coordinator` (collaboration role) dispatches to `patient_domain_auditor` and `treatment_domain_auditor` as SDK subagents, running in parallel. Each subagent's prompt is built explicitly by the coordinator — the relevant rule text and scoped data reference are constructed and injected per call, never assumed inherited. This is the load-bearing design point of the whole PRD — see Section 4. |
| 3. Tool Selection & MCP | Tool descriptions are documentation the model reasons over; MCP decouples tool implementation from agent logic | `get_patient_context`/`get_treatment_context` are plain Python functions registered directly against the Agent SDK's native tool mechanism. `query_deterministic_rule` is exposed via a small in-process MCP server instead — same underlying function, different registration/transport mechanism, deliberately, so the two approaches sit side by side for comparison. See Section 5. |
| 4. Prompt Engineering (partial) | Deterministic vs. non-deterministic; few-shot; prompt chaining | Deterministic/non-deterministic split: carried forward unchanged from Phase 1/1.5 (SYN-ICHD-01/06/09 deterministic, SYN-ICHD-02/04/05 non-deterministic). Few-shot: `patient_domain_auditor`'s and `treatment_domain_auditor`'s system prompts embed one worked positive + one worked negative example (from `outputs/sample-*.md`) directly, not just a description of the judgment task. Prompt chaining: at least one non-deterministic judgment (patient-continuity-review's four-point walk) is split into two sequential calls — extract-evidence, then judge-against-evidence — instead of one combined call, to practice the mechanic once, deliberately. |
| 5. Escalation / HITL / Error Handling | Hooks enforce hard rules in code, not prompts; comparing two structured outputs via code, not another LLM call; "pause, persist, resume"; self-contained human package | The biggest new surface area — see Section 6. A Hook deterministically enforces that any triggered finding carries `status: requires_human_review` before the run is allowed to complete — this is not trusted to prompt instructions alone, closing the gap Phase 1/1.5 left open (their skills only *said* "always route to human review" in prose). An evaluator step re-derives/cross-checks each subagent's structured finding in plain Python (schema comparison, not a third LLM call). Triggered findings are written to a local review queue file, the run pauses; a separate resume step lets a human load the self-contained package and record confirm/reject/clarify. |
| 6. Configuration Engineering | `system_prompt` + `allowed_tools` as deterministic whitelist, not documentation | Each subagent's `allowed_tools` restricts it to only its domain's tools (native or MCP-exposed alike) — `patient_domain_auditor` cannot call the treatment-scoped tools and vice versa, enforced by the SDK, not by the prompt asking nicely. Mirrors the `allowed-tools` frontmatter discipline from every Phase 1 skill, now as a real access-control mechanism instead of a Claude Code convention. |

## 4. Architecture

```
audit_coordinator (collaboration role)
├── dispatches, in parallel, via SDK subagents:
│   ├── patient_domain_auditor   — allowed_tools: get_patient_context, query_deterministic_rule(--db multi-domain)
│   └── treatment_domain_auditor — allowed_tools: get_treatment_context, query_deterministic_rule(--db default)
├── waits for both, then (plain Python, not an LLM call):
│   ├── runs the evaluator/comparison step (Section 6)
│   ├── enforces the escalation Hook's outcome
│   └── writes triggered findings to the review queue
```

Each subagent call is a fully independent context (Module 2's core lesson). The coordinator's dispatch code is responsible for building each subagent's prompt with exactly the data and rule text it needs — nothing is inherited from the coordinator's own context, and nothing is available to a subagent beyond what its `allowed_tools` expose.

## 5. Tools — native SDK vs. MCP, side by side

| Tool | Scope | Registration | Notes |
| --- | --- | --- | --- |
| `get_patient_context` | patient domain | Native Agent SDK tool | Reads `patient.nursing_notes` + (given a nursing-note date) the next relevant treatment record, from `data/synthetic-ichd-patient-goldset-multi-domain.json`. |
| `get_treatment_context` | treatment domain | Native Agent SDK tool | Reads one `clinical_treatments[]` entry by date. |
| `query_deterministic_rule` | both, `--db`-scoped | **MCP** (external server process, stdio) | Standalone script (`mcp_server.py`) run as its own process, connected via a `command`/`args` config entry (same shape as `.mcp.json`) — not an in-process helper. Wraps the existing `tools/query_deterministic_rule.py`. Returns structured error types per Module 1, not a raised exception. |

`patient_domain_auditor`'s `allowed_tools` includes only `get_patient_context` + `query_deterministic_rule` scoped to `data/audit_rules-multi-domain.db`; `treatment_domain_auditor`'s includes only `get_treatment_context` + `query_deterministic_rule` scoped to `data/audit_rules.db`. Exact enforcement mechanism (can `allowed_tools` scope a *parameter* of a shared tool, or does this require two distinctly-named tool wrappers per store — one per domain, regardless of registration style?) is a real open question to resolve by checking the actual SDK docs during build, not guessed here.

## 6. Escalation, evaluation, and the human queue

- **Hook**: fires after each subagent produces its structured finding; deterministically rejects/blocks completion if a triggered rule's output is missing `status: requires_human_review`. Exact Hook event name/signature to be verified against the real Claude Agent SDK docs during build (not guessed in this PRD) — this repo's established convention (see Phase 1 PRD Section 14) is to flag SDK-mechanism claims as unverified until checked against source, not present docs-adjacent guesses as confirmed fact.
- **Evaluator step**: plain Python, not an LLM call. Both subagents already output the same finding schema (trigger, evidence, evidence_gap points, draft_question, status) — the evaluator asserts schema conformance and flags any subagent output that doesn't validate, per Module 5's explicit guidance to avoid a third LLM call for structured comparison.
- **Pause/persist/resume**: triggered findings append to a local `review_queue.json` (flat file — matches this POC's no-infra ethos, same spirit as the SQLite "SOP store" being a committed file, not a real server). The coordinator run ends after writing the queue — it does not block waiting synchronously for a human. A separate `resume_review.py` script lets a human list pending items, view the self-contained package (both domains' evidence, not requiring the original conversation), and record `confirm` / `reject` / `clarify`, writing the outcome back into the same record. This is the first concrete implementation of the evaluation-signal capture Phase 1/1.5's skills only described in prose (and that Phase 4 was always going to need).

## 7. Data reuse (same isolation principle as Phase 1.5)

Referenced by path, **not copied, not modified**:
- `data/synthetic-ichd-patient-goldset-multi-domain.json`
- `data/audit_rules.db` (treatment-domain rules)
- `data/audit_rules-multi-domain.db` (patient-domain rules)
- `tools/query_deterministic_rule.py` (imported as a module, same pattern Phase 2's `deterministic.py` already established)

Phase 2.5 only reads these — no new rule rows, no schema changes — so there's no repeat of the "shared state" risk Phase 1.5 had to design around for writes.

## 8. File structure (proposed)

```
claude-agent-sdk-audit/
  pyproject.toml / uv.lock          # own deps: claude-agent-sdk, mcp
  README.md                          # explicit single-agent vs multi-agent banner vs. claude-sdk-audit/
  tools.py                           # get_patient_context, get_treatment_context — native SDK tools
  mcp_server.py                      # query_deterministic_rule, MCP-exposed only (Section 5)
  subagents.py                       # AgentDefinitions for patient_domain_auditor, treatment_domain_auditor
  coordinator.py                     # audit_coordinator: dispatch, evaluator step, hook wiring
  hooks.py                           # Section 6's escalation hook
  resume_review.py                   # human resume step
  review_queue.json                  # runtime output, gitignored or committed as an example — TBD
  outputs/                           # worked examples, same convention as Phase 1/1.5
```

## 9. Non-goals

- Dynamic decomposition (Module 4) and Batch API (Module 6) — explicitly deferred to the user's independent study (Section 2).
- No changes to `claude-sdk-audit/` (Phase 2) or the Phase 1/1.5 skill layer — both stay frozen, referenced only as the source of the validated design and shared data.
- No real queue/database infrastructure for the human-review pause/resume — a flat JSON file is sufficient to demonstrate the pattern at this POC's scale.
- No production-hardening (retries, real notification delivery, auth) — same synthetic-demo boundary as the rest of the repo.

## 10. Open questions to resolve during build (not guessed here)

1. Exact Agent SDK API for defining subagents and wiring `allowed_tools` per-subagent vs. per-tool-parameter (Section 5's open question).
2. Exact Hook event/signature available for post-finding validation (Section 6) — `@hook("PreToolUse"/"PostToolUse")` per the user's course material; exact decorator/signature confirmed at build time.
3. ~~MCP transport~~ — resolved: external server process (stdio, `command`/`args`), not in-process. Matches the user's course material, which frames MCP entirely around external server processes configured via `.mcp.json`-shaped entries.

These will be verified against the actual installed SDK's docs/source before being written into code, matching this repo's existing practice of not presenting unverified SDK claims as fact (see Phase 1 PRD Section 14 on `allowed-tools`/`disallowed-tools`).
