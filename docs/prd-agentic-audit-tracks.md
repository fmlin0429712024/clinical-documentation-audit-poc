# PRD: Deterministic + Non-Deterministic Audit Tracks (Claude Code Skills Practice)

Status: **v0.7 — Part 1 concluded; see Section 17**
Owner: Forest Lin
Scope: Claude Code (skills + tools) only. **No Claude Agent SDK work in this PRD** — that is an explicit future phase and is out of scope here.

## Roadmap (whole project, not just this PRD)

This repo is a multi-phase exam/certification-prep practice project. Each phase gets its own PRD once it starts; this document is Part 1 only.

| Phase | Scope | Status |
| --- | --- | --- |
| Part 1 | Claude Code + Skills implementation of the two audit tracks (this doc) | **Done** — concluded 2026-08-03, see Section 17 |
| Part 2 | Reimplement the same workflow with the Claude SDK — schema-enforced output, code-level determinism guarantee | Next — see `docs/prd-claude-sdk-migration.md` |
| Part 3 | Push to GitHub; PR automation using Claude Code headless mode on a self-hosted VM | Not started — PRD to follow once Part 2 exists (CI needs real Part 2 code/tests to run against) |
| Part 4 | Evaluation loop (reviewer-feedback capture and rule improvement — currently only described in prose in the orchestrator skill and the README workflow diagram) | Not started — deferred, gradual |

## 1. Purpose

This repo is a practice ground for building agentic solutions with Claude Code. The goal of this phase is to design and stand up **two parallel audit tracks** on top of the existing synthetic ICHD documentation-audit workflow, so we can practice two different skill-design patterns side by side on the same project:

- **Track A — Deterministic**: the audit verdict is computed by a tool/formula. The LLM's job is to call the tool and report the result — it never judges the outcome itself.
- **Track B — Non-deterministic**: the audit verdict requires reading free-text clinical notes and reasoning about them against a described scenario. The LLM's job *is* the judgment.

Both tracks reuse the existing repo conventions (synthetic-only data, `requires_human_review` findings, evidence citation, no clinical/coding/payment conclusions — see `docs/safety-and-governance.md`).

## 2. Goals

1. Practice designing a Claude Code skill that delegates a deterministic check to an external **tool** (a SQLite-backed lookup) instead of letting the model eyeball a threshold.
2. Practice designing a Claude Code skill that carries a **narrative use-case description** and relies on the LLM to extract and judge evidence against it — without collapsing into a disguised checklist/deterministic check.
3. Build a small, coherent story with **positive and negative sample data** for both tracks, so each skill can be run end-to-end and demonstrably discriminate compliant vs. deficient documentation.
4. Keep the two tracks visibly distinguished in the repo (which rule is which, which mechanism decides it) so the contrast is legible to someone reading the repo later.

## 3. Non-goals

- No Claude Agent SDK, no Python agent runtime, no migration work of any kind. That is a separate future PRD.
- No real patient/clinical/compliance data or guidance — everything stays fictional, per the existing safety boundary.
- No production concerns: no auth, access control, deployment, logging infrastructure, or real evaluation pipeline.
- No change to the existing `SYN-ICHD-01/02/03` *behavior* — Track A refines how `SYN-ICHD-01` is evaluated and stored, it doesn't change what it detects.

## 4. Terminology (locking this down so we stop re-litigating it)

| Term | Meaning in this PRD |
| --- | --- |
| **Deterministic** | The verdict is produced by an exact computation (formula/threshold over structured fields), executed by a tool. Zero LLM involvement in *deciding* the outcome. |
| **Non-deterministic** | The verdict requires interpreting unstructured text against a described scenario. No formula could produce it reliably — it needs LLM judgment. |
| **SOP (this PRD)** | Applies to Track A only: a structured, queryable rule definition (id, fields, operator, threshold, description) stored in SQLite — not prose. |
| **Use-case description** | Applies to Track B only: prose guidance embedded in the skill describing the scenario and what adequate documentation generally looks like. Deliberately *not* an itemized checklist, to avoid it quietly becoming a deterministic check. |

## 5. Track A — Deterministic (`SYN-ICHD-01`, early termination)

### 5.1 Mechanism

- The rule (currently only informally described in `rules/synthetic-audit-rules.md`) becomes a row in a new **SQLite** database. This is the "tool" being practiced: the skill doesn't reason about the threshold, it queries the DB and applies the returned comparison.
- Proposed threshold (formalizing the current vague "materially earlier"): `scheduled_minutes − completed_minutes ≥ 15` minutes. Illustrative only, not a real clinical/coding standard.

### 5.2 Proposed SQLite schema (open for review)

```sql
CREATE TABLE deterministic_rules (
    rule_id TEXT PRIMARY KEY,       -- 'SYN-ICHD-01'
    description TEXT NOT NULL,      -- human-readable trigger description
    field_a TEXT NOT NULL,          -- 'scheduled_minutes'
    field_b TEXT NOT NULL,          -- 'completed_minutes'
    operator TEXT NOT NULL,         -- 'a_minus_b_gte'
    threshold INTEGER NOT NULL,     -- 15
    draft_question TEXT NOT NULL,   -- question routed to human reviewer
    prohibited_inference TEXT NOT NULL
);
```

**Open question:** does the DB hold *only* rule metadata (treatment data stays in the existing `data/*.json` gold set, tool reads both), or do we also move the synthetic treatments into a `treatments` table in the same DB? Leaning toward **rule metadata only** — keeps the gold set as the single source of truth for patient data and makes the DB purely "the SOP store," which matches your framing ("SOP is for deterministic"). Flagging for your call.

### 5.2b Deterministic rule catalog (proposed, ~10 rows — for review)

You asked for enough rows in `deterministic_rules` that the SQLite lookup is a real tool-use exercise, not a 1-row toy. Below is a draft catalog. **All thresholds are fictional and illustrative — none of these are real clinical, coding, or CMS quality standards; that must stay explicit wherever this table is shown.**

Supporting this requires adding new numeric fields to `clinical_treatments[]` beyond the current `scheduled_minutes`/`completed_minutes` — noted in the "New field(s) needed" column. This is a new ask on the data model and needs your sign-off before I touch the gold set.

| Rule ID | Description (synthetic) | Field(s) | Operator | Threshold | New field(s) needed |
| --- | --- | --- | --- | --- | --- |
| SYN-ICHD-01 | Treatment completed materially earlier than scheduled | `scheduled_minutes`, `completed_minutes` | `a_minus_b_gte` | 15 min | *(none — exists)* |
| SYN-ICHD-05 | Treatment started materially later than scheduled | `scheduled_start`, `actual_start` | `b_minus_a_gte` | 20 min | `scheduled_start`, `actual_start` |
| SYN-ICHD-06 | Excess interdialytic weight gain vs. target | `pre_treatment_weight_kg`, `target_weight_kg` | `pct_diff_gte` | 4% | `pre_treatment_weight_kg`, `target_weight_kg` |
| SYN-ICHD-07 | Ultrafiltration rate above illustrative ceiling | `uf_volume_l`, `completed_minutes`, `post_treatment_weight_kg` (derived rate) | `derived_rate_gte` | 13 mL/kg/hr | `uf_volume_l`, `post_treatment_weight_kg` |
| SYN-ICHD-08 | Blood flow rate below illustrative floor | `blood_flow_rate_ml_min` | `lt` | 300 mL/min | `blood_flow_rate_ml_min` |
| SYN-ICHD-09 | Treatment marked missed | `status` | `eq` | `"missed"` | *(none — `status` exists)* |
| SYN-ICHD-10 | Fewer than 3 treatments documented in the trailing 7 days | `treatments_last_7_days` (derived) | `lt` | 3 | *(derived from existing records, no new field)* |
| SYN-ICHD-11 | Post-treatment systolic BP drop beyond illustrative threshold | `pre_treatment_sbp`, `post_treatment_sbp` | `a_minus_b_gte` | 30 mmHg | `pre_treatment_sbp`, `post_treatment_sbp` |
| SYN-ICHD-12 | Pre-treatment potassium above illustrative lab ceiling | `pre_treatment_potassium_meq_l` | `gte` | 6.0 mEq/L | `pre_treatment_potassium_meq_l` |
| SYN-ICHD-13 | Vascular access cannulation attempts above illustrative ceiling | `cannulation_attempts` | `gt` | 2 | `cannulation_attempts` |

**Open sub-question:** do you want all 10 rules backed by real (synthetic) data in the gold set from day one, or should we ship the DB with all 10 rule *definitions* but only build out positive/negative treatment data for a smaller subset (e.g. 3–4) first, adding the rest incrementally? Leaning toward the latter — proves the tool works against a real catalog without a huge synthetic-data authoring pass up front.

### 5.3 Data (positive + negative)

| Case | Date | Scheduled | Completed | Shortfall | Expected verdict |
| --- | --- | --- | --- | --- | --- |
| Positive (existing) | 2026-01-14 | 240 | 205 | 35 min | **Triggers** |
| Negative (new) | 2026-01-21 | 240 | 233 | 7 min | **Does not trigger** |

### 5.4 Skill impact

`audit-rule-evaluation` SKILL.md gains an instruction: for rules flagged deterministic in the DB, query the SQLite tool and report its result verbatim — do not independently judge the threshold.

## 6. Track B — Non-deterministic (new: intradialytic hypotension response)

### 6.1 Mechanism

New skill, `intradialytic-hypotension-review`, carrying a narrative use-case description (not stored in SQLite — deliberately prose, living in the skill):

> During ICHD, a patient may develop symptomatic hypotension (BP drop with symptoms like dizziness, nausea, lightheadedness). There is no fixed checklist — presentations and responses vary. Read `treatment_note` and `follow_up_note` and judge whether the documentation shows: the drop/symptoms were recognized and recorded; some corrective action was taken; the patient was reassessed after that action; and the physician was notified if the condition didn't resolve. Cite the exact language behind each judgment. If a note is silent or ambiguous on a point, mark it an evidence gap — never assume it happened. Never judge whether the clinical response was medically *correct*, only whether the documentation gives a reviewer enough to judge that.

### 6.2 Data (positive + negative)

| Case | Date | treatment_note (summary) | follow_up_note (summary) | Expected verdict |
| --- | --- | --- | --- | --- |
| Negative / compliant | 2026-01-28 | BP drop + symptoms recognized; UFR paused; repositioned; saline bolus given; BP reassessed and improved | Stable at discharge | **No documentation gap** |
| Positive / deficient | 2026-02-04 | BP drop + symptoms recognized; UFR paused | "Patient monitored" (no reassessment value, no notification mentioned) | **Flags gap**: reassessment and physician notification not documented |

### 6.3 Rule table entry

Add `SYN-ICHD-04` to `rules/synthetic-audit-rules.md`, and add a **Method** column across the whole table (`deterministic` / `non-deterministic`) so the two tracks are visible at a glance in the existing artifact.

## 7. Repository changes this PRD authorizes once approved

- `data/audit_rules.db` (new) — SQLite store for Track A rule metadata.
- `data/synthetic-ichd-patient-goldset.json` — add 3 new `clinical_treatments[]` entries (1 deterministic-negative, 1 non-deterministic-positive, 1 non-deterministic-negative).
- `rules/synthetic-audit-rules.md` — add Method column, add `SYN-ICHD-04` row, point `SYN-ICHD-01` at the SQLite store as canonical.
- `.claude/skills/intradialytic-hypotension-review/SKILL.md` (new) + mirrored copy in `.agents/skills/` per the existing dual-location convention.
- `audit-rule-evaluation` SKILL.md (both copies) — add the "query the tool for deterministic rules" instruction.

**Nothing above is written yet.** This PRD is the artifact under review.

## 8. Success criteria

- Running the orchestrator skill against each of the 5 total scenarios (1 existing + 4 new) produces the expected verdict, with the deterministic ones visibly resolved via a DB query tool call rather than model arithmetic/judgment.
- A reader of the repo can tell, without asking, which rules are deterministic and which aren't, and why.

## 9. Open questions for this review pass

1. SQLite scope: rule metadata only, or also treatment data? (Section 5.2)
2. Is `intradialytic-hypotension-review` the right skill boundary, or should this fold into the existing `documentation-evidence-review` skill instead of a new one?
3. Is the 15-minute threshold and the specific hypotension narrative acceptable as fictional illustrative content, or do you want different numbers/scenario details?
4. DB file location/name (`data/audit_rules.db`) — fine, or prefer elsewhere (e.g. `rules/`)?
5. Rule catalog (Section 5.2b): do all 10 rules ship with real synthetic data immediately, or definitions-first with data added incrementally for a subset?
6. Are the ~10 rule definitions and their new required fields (Section 5.2b table) acceptable, or do you want to trim/change any of them?

## 10. Part 2 preview (placeholder only — not designed yet)

Once Part 1 is built and actually run in Claude Code, a Part 2 PRD will port the same two tracks to the Claude Agent SDK. Rough intended mapping, for directional alignment only — **not to be designed in detail until Part 1 is validated**:

- Track A's SQLite lookup → becomes an SDK **tool** (function/tool-calling) the agent invokes; same DB, same schema, just called from SDK code instead of a Claude Code skill.
- Track B's narrative use-case description → becomes the **system/skill prompt** for an SDK agent or subagent; same text, different runtime.
- The orchestrator skill → becomes the SDK **agent loop** that decides which track applies and dispatches accordingly.

No file structure, tool signatures, or SDK project setup is decided here — that's Part 2's job, after Part 1 ships.

## 11. Part 1 build decisions (v0.3 — resolves open questions above)

To keep the first build pass small, scope was narrowed from the full catalog in Section 5.2b:

- **Rule catalog scope (resolves Q5, Q6):** built only 2 deterministic rules — `SYN-ICHD-01` (existing) and `SYN-ICHD-09` (missed treatment) — both usable with fields already in the gold set, no new schema needed. This still proves the SQLite lookup is a real table query (two rows, two different operators: `a_minus_b_gte` and `eq`), not a hardcoded threshold. The remaining 8 rows from Section 5.2b are deferred; the schema and `tools/query_deterministic_rule.py` already generalize to more operators/rows if added later.
- **SQLite scope (resolves Q1):** rule metadata only, per the original lean toward this option. Treatment data stays in `data/synthetic-ichd-patient-goldset.json` as the single source of truth; the tool takes a treatment record as input and looks up the rule separately.
- **DB location (resolves Q4):** `data/audit_rules.db`, generated from a committed `data/audit_rules.sql` (schema + seed) via `sqlite3 data/audit_rules.db < data/audit_rules.sql`. Both the `.sql` source and the built `.db` are committed — no build step required to run the demo.
- **Skill boundary (resolves Q2):** new dedicated skill `intradialytic-hypotension-review`, not folded into `documentation-evidence-review` — keeps the non-deterministic use-case description isolated and independently reusable, mirrored into `.agents/skills/` with an `openai.yaml` sidecar for consistency with the other four skills.
- **Threshold/narrative content (resolves Q3):** 15-minute threshold and the hypotension narrative (Section 6.1) shipped as drafted.
- **Terminology fix:** Section 6.2's original "Negative/compliant" and "Positive/deficient" labels were backwards from how they're used elsewhere in this PRD. Corrected polarity used in the actual build: **positive = audit passes clean, negative = audit flags a gap.**
- **Test data (final):** two new treatment records added to the existing patient in the gold set, both deterministic-clean (well under the 15-minute threshold) so the only variable between them is the non-deterministic hypotension judgment:
  - `2026-01-28` — **positive**: hypotension event fully documented (recognized, corrective action, reassessed, physician notified) → expected `no evidence gap`.
  - `2026-02-04` — **negative**: hypotension event documented but missing reassessment and physician notification → expected `requires_human_review` with 2 evidence gaps.
- Added `outputs/sample-hypotension-finding-negative.md` and `outputs/sample-hypotension-finding-positive.md` as worked examples for both cases, mirroring the existing `sample-audit-finding.md` convention.

**Still open:** none blocking — this section will be updated if further review changes any of the above before Part 1 is considered done.

## 12. Skill cleanup pass (v0.4)

Requested by the user: standardize all 5 SKILL.md files (both `.claude/skills/` and `.agents/skills/` mirrors) into one consistent template — `Purpose → [optional skill-specific section] → Workflow → Output Contract → Guardrails` — and sharpen every frontmatter `description` to name its pipeline position and hard constraints. All 5 skills were reviewed and kept; none were dropped, since each still maps to a distinct pipeline stage or track (normalize, evidence-review, Method-dispatch, orchestrate, hypotension use case). Also added `tools/test_query_deterministic_rule.py` (stdlib `unittest`, 9 tests, subprocess-driven against the real CLI) as the TDD layer for Track A — Track B has no equivalent automated layer since it's LLM judgment; verification there is the worked positive/negative examples plus a self-test guide (`docs/testing-guide.md`) for the user to run interactively.

## 13. Deterministic track gap fix (v0.5)

Reviewing `docs/testing-guide.md`, the user flagged two real gaps in Track A:

1. The guide only demonstrated single (rule, treatment) lookups — there was no way to audit a whole patient (loop every treatment × every deterministic rule), even though "loop to audit the target (patient + treatments)" was the actual intended use.
2. The deterministic track had no dedicated skill of its own — it was just a paragraph inside `audit-rule-evaluation` — unlike Track B, which is independently invocable via `intradialytic-hypotension-review`. The user wanted deterministic auditing reachable the same way: through a skill's description/prompt, not only through a direct script call.

This also surfaced a design fork worth recording: should the loop over treatments live *inside* `tools/query_deterministic_rule.py` (one batch CLI call) or *inside a skill's Workflow* (the agent iterates, calling the tool once per pair)? The user chose **agent-side looping** — the tool stays exactly as already tested (one rule × one treatment, no internal iteration), and the new `deterministic-rule-audit` skill's Workflow instructs the agent to call it once per (rule, treatment) pair. Rationale volunteered by the user: this project is explicitly about practicing how an *agent* orchestrates tools — hiding the loop inside Python code would defeat that purpose, and Python must only ever run when a skill's instructions cause the agent to invoke it, never on its own.

Resolved by adding the `deterministic-rule-audit` skill (mirrored `.claude/`/`.agents/`, `openai.yaml` sidecar) and updating `audit-rule-evaluation`, `clinical-audit-orchestrator`, `rules/synthetic-audit-rules.md`, the README skills table, and `docs/testing-guide.md` to reference it as the batch-audit entry point, distinct from the tool's single-lookup mode.

## 14. Per-skill tool allowlisting (v0.6)

The user asked for two things to be clearly defined on every skill for study/certification purposes: (1) a sharp `description` aligned with how it should be triggered by a prompt — already done in Section 12 — and (2) an explicit tool allowlist in each skill's frontmatter, so a skill cannot use tools outside a declared set.

Verified via research agent against Claude Code's official skill docs (`https://code.claude.com/docs/en/skills.md`) before writing anything, since this was explicitly for exam-prep accuracy:

- **`allowed-tools`** is a real frontmatter field (space-separated, comma-separated, or YAML list; supports Bash subcommand scoping like `Bash(git add *)`). Confirmed **it pre-approves tools for the turn — it does not itself prevent Claude from calling other tools.** It's a friction-reduction/declared-intent mechanism, not a sandbox.
- **`disallowed-tools`** removes a tool from the available pool while the skill is active. The docs use the phrase "removed from Claude's available pool" but **do not explicitly confirm whether this is a hard block (call refused) or a softer restriction** — the research agent flagged this ambiguity directly and recommended not presenting it as a guaranteed hard enforcement without further confirmation (empirical test or official clarification via `/feedback`).

Given the ambiguity, added `allowed-tools` to all 6 skills (declaring each one's real tool footprint) and added `disallowed-tools: Bash` specifically to `intradialytic-hypotension-review`, with an explicit in-skill note ("Note on `disallowed-tools: Bash`") stating this is documented best-effort intent, not a verified sandbox guarantee — and that a verified hard guarantee requires Part 2 (controlling the tool list passed to the model directly via the SDK). This was a deliberate choice to model "don't present docs-adjacent language as a confirmed guarantee" as its own teaching point, alongside the mechanism itself.

Per-skill `allowed-tools` assigned:

| Skill | allowed-tools |
| --- | --- |
| `clinical-record-normalization` | `Read(data/**)` |
| `documentation-evidence-review` | `Read(data/**) Read(rules/**)` |
| `audit-rule-evaluation` | `Read(rules/**) Read(data/**) Skill Bash(python3 tools/query_deterministic_rule.py *)` |
| `deterministic-rule-audit` | `Read(data/**) Bash(python3 tools/query_deterministic_rule.py *)` |
| `intradialytic-hypotension-review` | `Read(data/**) Read(rules/**)` (+ `disallowed-tools: Bash`) |
| `clinical-audit-orchestrator` | `Read(data/**) Skill` |

(Path-scoped `Read(...)` was tightened from bare `Read` in v0.7 — see Section 16. All 6 mirrored identically to `.agents/skills/` per the existing dual-location convention; Codex will likely ignore the unrecognized frontmatter fields, not verified either way, and not blocking.)

## 16. Path-scoped Read, and a correction on Write/Edit (v0.7)

Follow-up user question, again explicitly for exam-prep accuracy: the bare `Read` on 4 of the 6 skills (all but the two using `Bash(python3 tools/query_deterministic_rule.py *)`) was unscoped — "can read any file," not limited to what that skill actually needs. Verified via a second research-agent pass against Claude Code's docs before changing anything:

- Bare `Read` (no parentheses) is confirmed to pre-approve reading **any** file — documented explicitly.
- Path-scoped `Read(pattern)` (e.g. `Read(data/**)`) is **not shown with an explicit example inside `allowed-tools` in the skill docs.** It's architecturally implied — the `allowed-tools` docs state it uses the same rule format as `.claude/settings.json` permission rules, and `Read(path)`/`Edit(path)` patterns *are* documented there — but there's no skills-specific confirmation. Applied it anyway as best-effort scoping (`Read(data/**)`, `Read(rules/**)` per skill, matching what each actually reads), with an explicit "not confirmed, treat as best-effort" caveat added directly in `intradialytic-hypotension-review/SKILL.md` (the skill this matters most for, since it's the one meant to be tightly scoped).
- **Correction to an earlier claim in this PRD/conversation:** Read, Write, and Edit are *not* three independently-permissioned tools the way it was previously described. Only `Read(path)` and `Edit(path)` are real permission-rule namespaces; `Write` and `NotebookEdit` have no rule type of their own and are governed by `Edit(path)` rules. It remains true that granting `Read` does not grant write/edit capability — that part was correct — but "three separate rule types" was not.

Recommendation carried into `docs/testing-guide.md`-style guidance: if the user wants to know for certain whether `Read(pattern)` scoping is actually enforced inside a skill (vs. silently falling back to unrestricted), the reliable way is an empirical test — try to get the skill to read a file outside its declared pattern and see whether it's blocked — rather than trusting the architectural inference. Not run in this session.

## 17. Part 1 conclusion

Per the user's judgment: **Part 1 is done.** Both tracks have been exercised end to end with a real positive and a real negative case each:

- Deterministic: `2026-01-14` triggers `SYN-ICHD-01` (35 min short), `2026-01-28`/`2026-02-04` don't — verified by 9 automated tests (`tools/test_query_deterministic_rule.py`) and manually via `deterministic-rule-audit`.
- Non-deterministic: `2026-01-28` (positive, clean) vs. `2026-02-04` (negative, 2 evidence gaps) — walked manually through `intradialytic-hypotension-review` in-session, matching the worked examples in `outputs/`.
- Tool usage is real, not decorative: `tools/query_deterministic_rule.py` is invoked via Bash by skill instructions (never on its own), and is now allowlist-scoped per skill.
- All 6 skills standardized, sharply described, and tool-scoped; `.claude/` and `.agents/` mirrors verified identical throughout.

Not yet done, and explicitly out of scope for Part 1: Claude Agent SDK migration (Part 2) — see Section 10 for the (intentionally undesigned) preview.
