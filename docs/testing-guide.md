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

The tool only ever checks one rule against one treatment — it does not
loop. To audit the whole patient (every treatment × every deterministic
rule), the loop is agent behavior, invoked through a skill:

> Use the `deterministic-rule-audit` skill to audit every treatment for the
> patient in `data/synthetic-ichd-patient-goldset.json` against every
> deterministic rule. Show every (rule, treatment) pair it checked, not just
> the ones that triggered.

Expect 6 pairs checked (2 rules × 3 treatments), 1 triggered (`SYN-ICHD-01`
on the `2026-01-14` treatment), 5 not — and each verdict traceable to a
`tools/query_deterministic_rule.py` call, not to the model's own reasoning.
If you watch the transcript, you should see the tool actually invoked 6
times.

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

## Both tracks together

Testing each track alone tells you the skill itself works. Testing them
together tells you `audit-rule-evaluation`'s **dispatch** works — that it
correctly reads each rule's Method and routes deterministic rules one way,
non-deterministic rules another, without you specifying which is which.

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
> workflow across all three treatments in the gold set, covering both
> deterministic and non-deterministic rules. Show each stage's output.

Expect: normalization → evidence review → dispatch → both tracks resolved
per treatment → everything routed to `requires_human_review`. Across all
three treatments this should surface exactly 2 findings worth a human's
attention — the `2026-01-14` early-termination finding (deterministic) and
the `2026-02-04` hypotension documentation-gap finding (non-deterministic)
— with the `2026-01-28` treatment coming back clean on both tracks.

## What "passing" means here

Track A is pass/fail against a fixed threshold — the test suite is the
source of truth. Track B has no fixed answer key; "passing" means the
model's citations and gap/no-gap calls match the reasoning in the worked
examples, not that the wording is identical. If a run disagrees with the
worked example, that's a signal to sharpen the skill's use-case
description (see `intradialytic-hypotension-review/SKILL.md`), not a bug
to silently patch around.
