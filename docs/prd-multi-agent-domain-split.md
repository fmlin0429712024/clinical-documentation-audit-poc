# PRD: Multi-Agent Domain Split (Phase 1.5)

Status: **v0.3 — built and tested; see Section 10**
Owner: Forest Lin
Depends on: Phase 1 (`docs/prd-agentic-audit-tracks.md`), concluded, not re-litigated here. This document is Phase 1.5 — same implementation substrate as Phase 1 (Claude Code Skills only), extended to a multi-domain split. It is **not** part of Phase 2's lineage.
Runs alongside: Phase 3 (`docs/prd-github-headless-ci.md`, in progress) — orthogonal track, no dependency either direction, does not block or get blocked by it.
Pairs with (future, not designed here): **Phase 2.5** — the same 3-role design, ported to a real multi-agent Claude Agent SDK implementation, the way Phase 2 ported Phase 1's logic to the plain `anthropic` SDK. Previewed as a placeholder in Section 9 only.

**Naming/numbering note (resolved after initial drafting as "Phase 3.5"):** this work was first drafted under a "Phase 3.5" label, positioned after Phase 3 (CI) in the roadmap. Renumbered to **Phase 1.5** on the user's explicit call: Phase 3 (CI/deployment) is an orthogonal concern, unrelated to this work's actual content. The axis that matters is **implementation substrate**, which is exactly how Phase 1 vs. Phase 2 were already numbered — `1`↔`1.5` are both Skills-only; `2`↔`2.5` (future) are both SDK-based. All in-repo references (this file, `README.md`, `docs/testing-guide.md`, skill files, the multi-domain data file's `phase_notice`) were updated to match.

## 1. Purpose

Phase 1 and Phase 2 both implicitly targeted **one agent** resolving the whole pipeline (a single Claude Code session walking through 6 skills; a single Python process calling the API once per judgment). The next goal is to practice the Claude Agent SDK's **multi-agent** pattern — a collaboration/orchestrator role dispatching to domain-specific subagents — because that is the certification-relevant skill still unpracticed. That real multi-agent work is Phase 2.5, deliberately not started yet.

Jumping straight to Claude Agent SDK code would conflate two different learning curves at once: (a) designing a genuine two-domain audit split with a use case that needs real LLM judgment, and (b) learning the SDK's subagent mechanics. Phase 1.5 isolates (a): reuse the cheap, fast Claude Code Skill iteration loop (as in Phase 1) to design and validate the domain split and the new patient-level use case, before touching any SDK code. Phase 2.5 will then be a comparatively mechanical port of an already-validated design — isolating (b).

## 2. Goals

1. Design a **patient-domain audit use case** that requires genuine LLM judgment (evidence extraction + interpretation across two free-text sources), not a deterministic field lookup — see Section 4.
2. Reorganize the existing skill set's *conceptual* roles into exactly three, matching what Phase 2.5 will later become three real subagents for: **collaboration/orchestrator**, **patient-domain**, **treatment-domain** — see Section 5.
3. Validate the whole thing end-to-end inside Claude Code, using only the Skill mechanism already in use since Phase 1 — no new Claude Code feature (no native subagents, no Claude Agent SDK import anywhere in this phase).
4. Produce a design contract (role → responsibilities → evidence in/out) precise enough that Phase 2.5 can port it into real Claude Agent SDK subagents mechanically, without re-deciding the domain split.

## 3. Non-goals

- **No Claude Code native subagents (`.claude/agents/*.md`) in Phase 1.5.** Considered and deliberately rejected: this phase's only job is validating content/logic, not agent-architecture mechanics. Introducing a second new mechanism here would blur what's being tested at each stage. Real separate-context multi-agent practice is Phase 2.5's entire point.
- **No Claude Agent SDK work of any kind in Phase 1.5.** (One narrow, deliberate exception: `tools/query_deterministic_rule.py`, already Python since Phase 1, gained a `lt` operator and an optional `--db` flag — extending existing Phase 1 infrastructure, not introducing a new mechanism. See Section 10.1.)
- **No changes to `claude-sdk-audit/`.** It stays frozen as Phase 2's concluded artifact — not archived, not extended, not re-synced. `claude-sdk-audit/skills/` is a static one-time copy (confirmed missing `treatment-refusal-review`, since Phase 2 was intentionally scoped to only 3 rules) and stays that way.
- **No interruption of Phase 3 (CI).** This phase is independent; Phase 3's in-progress work continues unaffected.
- **No re-attempt at `SYN-ICHD-03`** — still an inherited placeholder from the original scaffold, out of scope here same as it was in Phase 1.

## 4. Patient-domain use case: nursing-note ↔ treatment continuity

### 4.1 Why not simpler options

Two simpler designs were considered and rejected as too shallow for genuine LLM judgment:

- **Auditing the existing `patient` object directly** — it only has 4 flat scalar fields (`synthetic_patient_id`, `age_band`, `care_modality`, `primary_condition_label`). No free text, no ambiguity, nothing to interpret.
- **A flat `known_allergies` list cross-checked against treatment notes by name-matching** — this reduces to a substring/keyword search; an LLM doing it adds no judgment value over a script.

### 4.2 Chosen design

New field: `patient.nursing_notes` — an array of `{note_date, note}` entries. Unlike `treatment_note`/`follow_up_note` (bound to one `clinical_treatments[]` entry), these are **patient-level, cross-encounter** notes: medication changes, allergy-history updates, lab follow-ups, care-plan discussions — maintained by the care team independent of any single treatment session.

**New rule `SYN-ICHD-05`** (Method: non-deterministic; Domain: **cross-domain** — needs both patient- and treatment-level evidence):

> A `nursing_notes` entry documents a care-plan-relevant change (e.g. a medication adjustment). Judge whether the patient's documentation shows continuity: was the change itself adequately described; does the *next relevant* treatment record reflect awareness of it; was its effect followed up; was the physician looped in if escalation was warranted. No fixed checklist — matching every other non-deterministic skill's convention (`intradialytic-hypotension-review`, `treatment-refusal-review`), this is a narrative use-case description, not a keyword rule, and any point the notes are silent or ambiguous on is an evidence gap, never an assumption.

Four judgment points (same shape as the two existing non-deterministic skills, for consistency):

1. Change adequately documented (what changed, when) in the `nursing_notes` entry.
2. The next relevant treatment record's `treatment_note`/`follow_up_note` reflects awareness of the change — this itself requires judgment (which treatment is "the next relevant one," and what counts as "reflects awareness" — no fixed phrase to match).
3. Follow-up/effect of the change is documented.
4. Physician notified/escalation documented, if the situation called for it.

**Guardrails (same as existing rules):** never judge whether the change itself was clinically correct — only whether the documentation shows continuity; cite exact source fields (`nursing_notes[i]` + the specific treatment's `treatment_note`/`follow_up_note`); label `insufficient_evidence` rather than inferring.

### 4.3 Data plan (positive + negative, matching repo convention) — built as follows

**Resolved: a new, dedicated data file, not an edit to the original gold set.** `data/synthetic-ichd-patient-goldset.json` is referenced (not copied) by Phase 2 (`claude-sdk-audit/`), whose regression tests are pinned to that file's exact shape and content — adding `patient.nursing_notes` or new `clinical_treatments[]` entries to it would risk silently breaking Phase 2. Built instead: `data/synthetic-ichd-patient-goldset-multi-domain.json` — a self-contained file carrying the original 5 `clinical_treatments[]` entries verbatim (so `SYN-ICHD-01/02/04/09` trigger identically there), plus `patient.nursing_notes` (2 entries) and 2 new treatments (`2026-03-04` positive, `2026-03-18` negative) for `SYN-ICHD-05`. See that file's own `phase_notice` field for the same rationale, kept in-band.

## 5. Skill-layer role mapping (Phase 1.5) — as built

Three logical roles, each mapping to one or more of the 8 skills. This table **is** the design contract Phase 2.5 will port.

| Role (Domain tag used in each skill) | Skills it comprises | Responsibility |
| --- | --- | --- |
| **collaboration** | `clinical-audit-orchestrator`, `clinical-record-normalization`, `audit-rule-evaluation` | Sequencing, a shared domain-agnostic normalization pass, and dispatch by Method **and** Domain. Owns no evidence of its own — it routes to whichever skill does, and drafts nothing itself. |
| **patient** | `patient-continuity-review` (new, non-deterministic), `deterministic-rule-audit` (patient-domain check, new — Section 10.1) | Owns `SYN-ICHD-05` end to end — reads both the triggering `nursing_notes` entry *and* the one relevant treatment record, walks all four judgment points, and drafts the full finding itself. Also owns the one-off `SYN-ICHD-06` deterministic check. |
| **treatment** | `documentation-evidence-review`, `deterministic-rule-audit` (treatment-domain rules), `intradialytic-hypotension-review`, `treatment-refusal-review` | Unchanged from Phase 1 — owns `SYN-ICHD-01/02/04/09` entirely. |

**Revised design decision (supersedes the draft-stage plan above the line):** the original draft proposed a stricter split — both domain skills only extract evidence, with a separate synthesis step elsewhere combining them. Built simpler instead, once the existing non-deterministic skills were re-read closely: `intradialytic-hypotension-review` and `treatment-refusal-review` **already** own their full judgment end-to-end (walk all four points, draft the finding) rather than handing raw evidence to `audit-rule-evaluation` for synthesis — `audit-rule-evaluation` only dispatches, per its own Workflow ("don't judge inline"). `patient-continuity-review` follows that exact same, already-proven pattern: it's a single self-contained non-deterministic skill whose only difference from the other two is that its two input sources (`nursing_notes` + one treatment record) span two data locations instead of one. No new synthesis mechanism was needed — this also directly answers Open Question 3 (Section 8).

## 6. File changes — built (all items below are done)

- `data/synthetic-ichd-patient-goldset-multi-domain.json` (new) — original `data/synthetic-ichd-patient-goldset.json` untouched.
- `data/audit_rules-multi-domain.sql` / `.db` (new, Section 10.1) — original `data/audit_rules.db` untouched.
- `rules/synthetic-audit-rules.md` — added a `Domain` column (`patient` / `treatment`); added the `SYN-ICHD-05` and `SYN-ICHD-06` rows with inline notes on which data file/store each requires.
- New skill: `.claude/skills/patient-continuity-review/SKILL.md` + mirrored `.agents/skills/patient-continuity-review/SKILL.md` + `agents/openai.yaml` sidecar. Follows the standard template (Purpose → Use Case → Workflow → Output Contract → Guardrails), `allowed-tools: Read(data/**) Read(rules/**)` + `disallowed-tools: Bash`, matching the other two non-deterministic skills exactly.
- All 8 skills (both `.claude/skills/` and `.agents/skills/`) — added a one-line **Domain** tag under each title (`collaboration` / `patient` / `treatment`); `clinical-record-normalization/SKILL.md` also updated to enumerate `nursing_notes` in its evidence-inventory step; `audit-rule-evaluation/SKILL.md` gained a dispatch branch (`SYN-ICHD-05` → `patient-continuity-review`); `clinical-audit-orchestrator/SKILL.md` gained a note on which data file to use for patient-domain rules; `deterministic-rule-audit/SKILL.md` gained the patient-level one-off check step (Section 10.1). `.claude/` and `.agents/` verified byte-identical (`diff -rq`, excluding the `agents/openai.yaml` sidecars, which have no Claude Code equivalent by design).
- New sample outputs: `outputs/sample-patient-continuity-finding-positive.md`, `-negative.md`, and `outputs/sample-patient-continuity-deterministic-finding.md` (`SYN-ICHD-06`).
- `README.md` — Phase 1.5 roadmap row (inserted next to Phase 1, not Phase 3), a full "How Phase 1.5 Works" section positioned directly after "How Phase 1 Works" (diagram + Domain table), updated Repository Map, and the `claude-sdk-audit` vs. future `claude-agent-sdk-audit` naming-distinction callout.
- `docs/testing-guide.md` — added a "Track C — patient domain" section (positive/negative prompts) and a third "both tracks together" prompt exercising all three roles against the new data file in one run.

## 7. Success criteria

- Running `clinical-audit-orchestrator` against the gold set produces the correct trigger/no-trigger for both the `SYN-ICHD-05` positive and negative cases, with evidence cited from both a `nursing_notes` entry and the relevant treatment record.
- All existing rules (`SYN-ICHD-01/02/04/09`) produce unchanged verdicts on unchanged data — this phase must be regression-safe on Phase 1's existing behavior.
- A reader of the repo can identify, without asking, which skill(s) map to which of the three roles (Section 5) — since that mapping is the literal contract Phase 2.5 ports.
- `.claude/skills/` and `.agents/skills/` remain identical mirrors throughout.
- `claude-sdk-audit/` untouched; its existing tests still pass unmodified.

All of the above are met — see Section 10.2.

## 8. Open questions from the draft — resolved as built

1. **Skill name: `patient-continuity-review`** — built as proposed.
2. **Rule ID: `SYN-ICHD-05`** — built as proposed; `SYN-ICHD-03` left untouched as the pre-existing placeholder, not reused.
3. **Cross-domain synthesis location — resolved differently than either draft option.** Neither "inside the orchestrator" nor "a separate synthesis skill": once the two existing non-deterministic skills were re-read closely, they already own their full judgment end-to-end rather than handing evidence up for synthesis. `patient-continuity-review` follows that same pattern instead of inventing a new one — see Section 5's revised design decision.
4. **`nursing_notes` text content** — drafted during build (not reviewed as a separate step first), matching how Phase 1's positive/negative data was handled. Content: Section 4.3 / the data file's own entries. Flag now if the specific wording needs revision.

## 9. Phase 2.5 preview (placeholder only — not designed here)

Once Phase 1.5 is built and validated in Claude Code, Phase 2.5 ports the three roles in Section 5 into a real multi-agent implementation using the Claude Agent SDK, in a new root-level folder **`claude-agent-sdk-audit/`** (sibling to `claude-sdk-audit/`) — the same relationship Phase 2 has to Phase 1. Rough intended mapping, directional only:

- Collaboration/orchestrator role → the SDK's top-level agent, dispatching to two subagents and synthesizing their returned evidence.
- Patient-domain and treatment-domain roles → two real Claude Agent SDK subagents, each with their own context and tool access, mirroring Section 5's responsibility split.

**Naming risk flagged for when Phase 2.5 starts:** `claude-sdk-audit` (Phase 2, single agent, direct API, no agentic loop) and `claude-agent-sdk-audit` (Phase 2.5, multi-agent, real Agent SDK) are one word apart. Both READMEs will need an explicit, mutual cross-reference banner stating single-agent vs. multi-agent up front, so a reader doesn't conflate the two.

No file structure, subagent tool signatures, or SDK project setup is decided here — that's Phase 2.5's job, after Phase 1.5 is validated.

## 10. What got built and tested (Phase 1.5, v0.3)

Everything in Sections 4–8 above is implemented and live-tested, per the user's explicit go-ahead to build directly from this PRD's design.

### 10.1 Addition beyond the original scope: `SYN-ICHD-06` (deterministic, patient domain)

The user asked for patient-domain feature parity with treatment domain — deterministic *and* non-deterministic, not just the latter. Added `SYN-ICHD-06`: "`patient.nursing_notes` has fewer than 3 entries" (`nursing_notes_count < 3`), resolved by `tools/query_deterministic_rule.py` with zero LLM judgment, same guarantee as `SYN-ICHD-01`/`09`.

**Same isolation principle as Section 4.3, applied to the SQLite store:** `data/audit_rules.db` is referenced (not copied) by Phase 2, whose `deterministic.py` loops every rule in the store × every treatment in the *original* gold set unconditionally — adding a row there would make Phase 2 try to evaluate `SYN-ICHD-06` against treatments that don't have a `nursing_notes_count` field, crashing frozen, previously-pushed code. Built instead: a **separate** store, `data/audit_rules-multi-domain.db` (from `data/audit_rules-multi-domain.sql`), selected via a new optional `--db` flag on `tools/query_deterministic_rule.py` (defaults to the original path — fully backward compatible, verified by rerunning the existing 10-test suite unchanged). Also added one new operator, `lt` (the existing two, `a_minus_b_gte`/`eq`, couldn't express "fewer than N").

New test file `tools/test_query_deterministic_rule_patient_domain.py` (5 tests, separate from Phase 1's frozen suite) covers both branches of the threshold via hand-built `{"nursing_notes_count": N}` payloads (0/2 trigger, 3/5 don't) plus a guardrail test asserting `SYN-ICHD-06` is absent from the original store. All 15 tests (10 original + 5 new) pass.

`deterministic-rule-audit/SKILL.md` (both mirrors) gained a step 4: when auditing the multi-domain gold set, also run one patient-level check (count `nursing_notes`, query the separate store) — not looped, since there's one patient per record, not an array to iterate.

### 10.2 Test results — verified live, in a running Claude Code session

Run via the `Skill` tool, in-session (see 10.3 for what this does and doesn't prove):

| Test | Expected | Result |
| --- | --- | --- |
| `SYN-ICHD-05` positive (`nursing_notes` 2026-03-02 → treatment 2026-03-04) | All 4 points `documented` | ✅ Matched `outputs/sample-patient-continuity-finding-positive.md` exactly |
| `SYN-ICHD-05` negative (`nursing_notes` 2026-03-16 → treatment 2026-03-18) | 1 `documented`, 3 `evidence_gap` | ✅ Matched `outputs/sample-patient-continuity-finding-negative.md` exactly |
| `SYN-ICHD-04` regression (hypotension, `2026-02-04`, original gold set) | 2 `documented`, 2 `evidence_gap` | ✅ Matched `outputs/sample-hypotension-finding-negative.md` exactly — treatment domain unaffected by the patient-domain build |
| `SYN-ICHD-02` regression (refusal, `2026-02-11`, original gold set) | All 4 `documented` | ✅ Matched `outputs/sample-treatment-refusal-finding-positive.md` exactly |
| `SYN-ICHD-06` deterministic (both branches) | trigger at 0/2, no-trigger at 3/5 | ✅ Verified via direct tool calls + the automated test suite (10.1) |
| Full `clinical-audit-orchestrator` run, multi-domain gold set, all 6 rules × 7 treatments + 2 nursing notes | All three Domain-tagged roles participate; success/deficiency split correctly | ✅ See 10.2b |

Section 7's success criteria are met.

### 10.2b Full-pipeline run — all three roles in one pass, success vs. deficiency

Run via `clinical-audit-orchestrator` against `data/synthetic-ichd-patient-goldset-multi-domain.json`, asked explicitly to separate clean findings from deficiency findings, to directly address the question of whether all three Domain roles visibly participate in one run (not just individually, as in 10.2):

| Rule | Domain | Method | Skill | Result |
| --- | --- | --- | --- | --- |
| `SYN-ICHD-01` | treatment | deterministic | `deterministic-rule-audit` | Triggered 3× (`2026-01-14` 35min short, `2026-02-11` 75min, `2026-02-18` 80min) |
| `SYN-ICHD-09` | treatment | deterministic | `deterministic-rule-audit` | 0 triggers (no `"missed"` status in this file) |
| `SYN-ICHD-04` | treatment | non-deterministic | `intradialytic-hypotension-review` | `2026-01-28` clean; `2026-02-04` 2 gaps |
| `SYN-ICHD-02` | treatment | non-deterministic | `treatment-refusal-review` | `2026-02-11` clean; `2026-02-18` 3 gaps |
| `SYN-ICHD-05` | **patient** | non-deterministic | `patient-continuity-review` | `2026-03-02→03-04` clean; `2026-03-16→03-18` 3 gaps |
| `SYN-ICHD-06` | **patient** | deterministic | `deterministic-rule-audit` | Triggered (`nursing_notes_count` = 2 < 3) |

**Clean/success** (3): `SYN-ICHD-04` (`2026-01-28`), `SYN-ICHD-02` (`2026-02-11`), **`SYN-ICHD-05`** (`2026-03-02→03-04`) — spans both domains in the same run.
**Deficiency** (3): `SYN-ICHD-04` (`2026-02-04`), `SYN-ICHD-02` (`2026-02-18`), **`SYN-ICHD-05`** (`2026-03-16→03-18`) — same.
**Deterministic, zero LLM, not clean/deficiency by nature** (4): the `SYN-ICHD-01` × 3 and `SYN-ICHD-06` × 1 triggers above.

An honest edge case surfaced, not avoided: `2026-01-14`'s note ("treatment ended early; fictional symptoms were addressed") is vague enough that neither `SYN-ICHD-02` nor `SYN-ICHD-04` was judged to trigger — no explicit refusal or hypotension language, matching `docs/testing-guide.md`'s own flagged ambiguity on this record.

All three Domain roles (collaboration = normalization + dispatch; treatment = 4 skills, 6 judgments; patient = 2 skills, 2 judgments) visibly participated in this single run — the closest thing to "three roles collaborating" that the Skill mechanism can demonstrate. See 10.4 for what this does and doesn't prove about multi-agent topology.

### 10.3 Empirical findings surfaced by actually running this, not just designing it

Two things Phase 1 had flagged as "documented intent, not verified" (Section 14 of `docs/prd-agentic-audit-tracks.md`) got real evidence this session:

1. **`disallowed-tools: Bash` is a real hard block, not just declared intent.** Invoking `patient-continuity-review` (which sets `disallowed-tools: Bash`) and then attempting a Bash call inside that turn was refused outright ("Permission to use Bash has been denied"), forcing a fallback to `Read`. This resolves Phase 1's open uncertainty on this point, at least for this session's permission configuration.
2. **`allowed-tools` scoping did not visibly grant anything beyond the session's own permission state.** Invoking `deterministic-rule-audit` (which declares `allowed-tools: ... Bash(python3 tools/query_deterministic_rule.py *)`) and then running exactly that allowlisted command was still denied in that turn. Consistent with Phase 1's standing caveat that `allowed-tools` is "a friction-reduction/declared-intent mechanism, not a sandbox" — it doesn't itself force approval either. Does not undermine 10.1's correctness (the same tool calls were independently verified via direct subprocess calls and the automated test suite outside any skill's turn).

### 10.4 Directly answers the "is Phase 1.5 real multi-agent" question

The live runs in 10.2 all executed as `Skill` tool calls inside this single, continuous session — no separate agent was spawned, no independent context was created, and nothing "reported back" across a context boundary, because Phase 1.5 has none of that by design (Section 3). This was asked about explicitly and is worth stating plainly: **verifying independent subagent execution is not possible against what Phase 1.5 is** — that check only becomes meaningful once Phase 2.5 exists. What Phase 1.5 *can* and does demonstrate: all three Domain-tagged roles (collaboration, patient, treatment) participating correctly in one full pipeline run, dispatched by `audit-rule-evaluation` reading Method+Domain — the logic Phase 2.5 will port, not the runtime topology it will add.
