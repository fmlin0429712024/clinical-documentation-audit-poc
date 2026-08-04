# Testing Guide — Run This Yourself

This walks through verifying both tracks by hand: the deterministic layer
with real automated tests, the non-deterministic layer by running the skill
in Claude Code and comparing against the worked examples in `outputs/`. Test
each track alone first, then together — see the last section.

Run all of this in a fresh Claude Code session opened at this repo's root
(not a session that predates these skills — newly added `.claude/skills/`
files need a fresh session to be picked up).

## Where Python comes in

`tools/query_deterministic_rule.py` is a plain stdlib script — no venv, no
pip install, no packaging. Claude Code (the agent) only ever runs it because
a skill's Workflow tells it to, via the Bash tool it already has — the same
way it might run `git` or `sqlite3`. It never runs on its own, and nothing
about using Claude Code *requires* Python; this project just chose Python
for the one piece that has to be genuinely deterministic. If there were no
script, the only way to get a verdict would be the LLM reading the rule
and doing the comparison itself — which reintroduces the LLM into a
decision that's supposed to have zero LLM involvement. The non-deterministic
track uses no code at all — it's pure model judgment against the narrative
use case in `intradialytic-hypotension-review/SKILL.md`.

## Track A — deterministic (automated, no LLM)

Run the test suite:

```bash
python3 tools/test_query_deterministic_rule.py -v
```

Expect `OK` with 9 tests passing. To see a single evaluation by hand:

```bash
python3 -c "
import json
data = json.load(open('data/synthetic-ichd-patient-goldset.json'))
print(json.dumps(data['clinical_treatments'][0]))
" | python3 tools/query_deterministic_rule.py SYN-ICHD-01 -
```

Swap `clinical_treatments[0]` for `[1]` or `[2]` and compare `"triggered"`:

| Index | Date | Expect `triggered` |
| --- | --- | --- |
| `[0]` | 2026-01-14 | `true` (35 min short) |
| `[1]` | 2026-01-28 | `false` (4 min short) |
| `[2]` | 2026-02-04 | `false` (2 min short) |
| `[3]` | 2026-02-11 | `true` (75 min short — treatment refused) |
| `[4]` | 2026-02-18 | `true` (80 min short — treatment refused) |

The tool only ever checks one rule against one treatment — it does not
loop. To audit the whole patient (every treatment × every deterministic
rule), the loop is agent behavior, invoked through a skill:

> Use the `deterministic-rule-audit` skill to audit every treatment for the
> patient in `data/synthetic-ichd-patient-goldset.json` against every
> deterministic rule. Show every (rule, treatment) pair it checked, not just
> the ones that triggered.

Expect 10 pairs checked (2 rules × 5 treatments), 3 triggered — `SYN-ICHD-01`
on `2026-01-14`, `2026-02-11`, and `2026-02-18` — 7 not, and each verdict
traceable to a `tools/query_deterministic_rule.py` call, not to the
model's own reasoning. If you watch the transcript, you should see the
tool actually invoked 10 times.

## Track B — non-deterministic (run the skill yourself)

Open this repo in Claude Code (the actual CLI, not this session) and try
each prompt below. Compare the output against the linked worked example —
you're checking whether the LLM's judgment lands on the same four points,
not whether the wording matches exactly.

**1. Positive case — expect a clean finding**

> Use the `intradialytic-hypotension-review` skill to review the treatment
> dated `2026-01-28` in `data/synthetic-ichd-patient-goldset.json` for rule
> `SYN-ICHD-04`. Show the four judgment points and the draft finding.

Compare against [`outputs/sample-hypotension-finding-positive.md`](../outputs/sample-hypotension-finding-positive.md)
— expect all four points `documented`, no evidence gaps.

**2. Negative case — expect two evidence gaps**

> Use the `intradialytic-hypotension-review` skill to review the treatment
> dated `2026-02-04` in `data/synthetic-ichd-patient-goldset.json` for rule
> `SYN-ICHD-04`. Show the four judgment points and the draft finding.

Compare against [`outputs/sample-hypotension-finding-negative.md`](../outputs/sample-hypotension-finding-negative.md)
— expect reassessment and physician notification flagged as `evidence_gap`.

**3. Treatment refusal, positive case — expect a clean finding**

> Use the `treatment-refusal-review` skill to review the treatment dated
> `2026-02-11` in `data/synthetic-ichd-patient-goldset.json` for rule
> `SYN-ICHD-02`. Show the four judgment points and the draft finding.

Compare against [`outputs/sample-treatment-refusal-finding-positive.md`](../outputs/sample-treatment-refusal-finding-positive.md)
— expect all four points `documented`. Note this treatment also triggers
`SYN-ICHD-01` deterministically (75 min short) — a real, independently-
designed second example of combined dispatch, not the same one reused.

**4. Treatment refusal, negative case — expect three evidence gaps**

> Use the `treatment-refusal-review` skill to review the treatment dated
> `2026-02-18` in `data/synthetic-ichd-patient-goldset.json` for rule
> `SYN-ICHD-02`. Show the four judgment points and the draft finding.

Compare against [`outputs/sample-treatment-refusal-finding-negative.md`](../outputs/sample-treatment-refusal-finding-negative.md)
— expect only "refusal recognized" as `documented`; risk discussion,
physician notification, and the follow-up plan all flagged as
`evidence_gap`.

## Track C — patient domain (Phase 1.5, `SYN-ICHD-05`)

This track needs a **different data file** —
`data/synthetic-ichd-patient-goldset-multi-domain.json` — because it's the
only one with `patient.nursing_notes`. The original
`data/synthetic-ichd-patient-goldset.json` cannot trigger `SYN-ICHD-05` at
all; if a prompt below is run against it by mistake, expect the skill to
correctly report the rule doesn't apply (no `nursing_notes` field), not a
false trigger.

**1. Positive case — expect a clean finding**

> Use the `patient-continuity-review` skill to review the nursing note
> dated `2026-03-02` in
> `data/synthetic-ichd-patient-goldset-multi-domain.json` for rule
> `SYN-ICHD-05`. Show the four judgment points and the draft finding.

Compare against [`outputs/sample-patient-continuity-finding-positive.md`](../outputs/sample-patient-continuity-finding-positive.md)
— expect all four points `documented`, cross-referencing the treatment
dated `2026-03-04`.

**2. Negative case — expect three evidence gaps**

> Use the `patient-continuity-review` skill to review the nursing note
> dated `2026-03-16` in
> `data/synthetic-ichd-patient-goldset-multi-domain.json` for rule
> `SYN-ICHD-05`. Show the four judgment points and the draft finding.

Compare against [`outputs/sample-patient-continuity-finding-negative.md`](../outputs/sample-patient-continuity-finding-negative.md)
— expect only "change adequately described" as `documented`; awareness in
the next treatment, follow-up, and physician notification all flagged as
`evidence_gap`. The treatment cross-referenced (`2026-03-18`) is
deliberately silent on the change — that silence is the point of the test.

**3. `SYN-ICHD-06` — patient-domain deterministic, zero LLM**

```bash
python3 -m unittest discover -s tools -p "test_*.py" -v
```

Expect the 5 `SynIchd06SparseNursingNotes`/`OriginalStoreUnaffected` tests
to pass alongside the original 10. To see it resolved through the skill
layer instead of the raw test file:

> Use the `deterministic-rule-audit` skill to audit the patient in
> `data/synthetic-ichd-patient-goldset-multi-domain.json`, including the
> patient-domain check (`SYN-ICHD-06`).

This fixture's `patient.nursing_notes` has 2 entries — below the
illustrative threshold of 3 — so expect `SYN-ICHD-06` to **trigger**,
resolved via `--db data/audit_rules-multi-domain.db`, verbatim from the
tool, same zero-judgment guarantee as `SYN-ICHD-01`/`09`.

## Both tracks together

Testing each track alone tells you the skill itself works. Testing them
together tells you `audit-rule-evaluation`'s **dispatch** works — that it
correctly reads each rule's Method (and, since Phase 1.5, Domain) and
routes deterministic rules one way, non-deterministic rules another —
including routing `SYN-ICHD-05` to `patient-continuity-review` instead of
one of the treatment-domain skills — without you specifying which is
which.

**1. One treatment, both tracks, dispatch not specified**

> Audit the treatment dated `2026-02-04` in
> `data/synthetic-ichd-patient-goldset.json` against all applicable rules
> and give me the findings.

Nothing in this prompt says "deterministic" or "non-deterministic." Expect
the agent to read `rules/synthetic-audit-rules.md`, route `SYN-ICHD-01`/`09`
to `deterministic-rule-audit` (tool-resolved, `triggered: false` for this
date) and `SYN-ICHD-04` to `intradialytic-hypotension-review`
(judgment-resolved, 2 evidence gaps) — and hand back both results. If it
answers only one track, or reasons about the deterministic threshold itself
instead of routing to the tool, that's the dispatch instructions needing
sharpening in `audit-rule-evaluation/SKILL.md`.

**2. Full pipeline, full orchestrator, all treatments**

> Use the `clinical-audit-orchestrator` skill to run the full audit
> workflow across all five treatments in the gold set, covering both
> deterministic and non-deterministic rules. Show each stage's output.

Expect: normalization → evidence review → dispatch → both tracks resolved
per treatment → everything routed to `requires_human_review`. Per record:

| Date | `SYN-ICHD-01` (deterministic) | Non-deterministic |
| --- | --- | --- |
| `2026-01-14` | triggers (35 min short) | ambiguous — see note below |
| `2026-01-28` | clean | `SYN-ICHD-04` clean |
| `2026-02-04` | clean | `SYN-ICHD-04` flags 2 gaps |
| `2026-02-11` | triggers (75 min short — refused) | `SYN-ICHD-02` clean |
| `2026-02-18` | triggers (80 min short — refused) | `SYN-ICHD-02` flags 3 gaps |

**A genuine edge case worth watching:** `2026-01-14`'s note ("treatment
ended early; fictional symptoms were addressed") predates the
`treatment-refusal-review` skill and doesn't explicitly describe a
refusal. Whether the skill also fires `SYN-ICHD-02` on this vague wording
is a good real test of whether it over-triggers on ambiguous language —
if it does, that's a signal to sharpen the skill's use-case description,
not something to silently accept.

**3. Full pipeline including the patient domain (Phase 1.5)**

> Use the `clinical-audit-orchestrator` skill to run the full audit
> workflow against `data/synthetic-ichd-patient-goldset-multi-domain.json`,
> covering deterministic, treatment-domain non-deterministic, and
> patient-domain rules. Show each stage's output, including which skill
> resolved each rule.

Expect all of Track A/B's results on the first five (unchanged, verbatim
copies of the original treatments) *plus* `SYN-ICHD-05` resolved by
`patient-continuity-review` for both nursing-note entries — one clean, one
flagged — *plus* `SYN-ICHD-06` triggering once at the patient level
(`nursing_notes_count` = 2, below the threshold of 3). This is the
end-to-end check that Method+Domain dispatch works across all three roles
(collaboration, treatment, patient) in one run, not just each in
isolation.

## What "passing" means here

Track A is pass/fail against a fixed threshold — the test suite is the
source of truth. Track B has no fixed answer key; "passing" means the
model's citations and gap/no-gap calls match the reasoning in the worked
examples, not that the wording is identical. If a run disagrees with the
worked example, that's a signal to sharpen the skill's use-case
description (see `intradialytic-hypotension-review/SKILL.md`), not a bug
to silently patch around.
