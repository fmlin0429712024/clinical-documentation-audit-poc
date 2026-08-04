# PRD: GitHub + Headless CI (Phase 3)

Status: **Draft v0.1 — under review, nothing built yet**
Owner: Forest Lin
Depends on: Phase 1 (`docs/prd-agentic-audit-tracks.md`) and Phase 2 (`docs/prd-claude-sdk-migration.md`), both concluded.
Scope: branch/PR workflow, GitHub Actions CI (test suites + headless Claude Code PR review), branch protection gating merge on a passing check + human approval. **No self-hosted VM** — decided against (see Section 3). No auto-merge, no "implementer" role for Claude Code in CI yet.

## 1. Purpose

Practice the standard branch → PR → CI → gated-merge flow, and extend this project's core thesis — **AI drafts, a human decides** — to the development process itself: headless Claude Code reviews a PR and produces evidence, but nothing merges without a human approving based on that evidence. Same shape as every audit finding in Phase 1/2, applied one level up.

## 2. Goals

1. Standard git branch + PR workflow, exercised with one real new audit use case as the test vehicle (not a throwaway commit).
2. A GitHub Actions workflow that runs both existing test suites on every PR.
3. A second job using headless Claude Code (via the official `anthropics/claude-code-action@v1`) to review the PR diff against this repo's own conventions (`CLAUDE.md`, the skill template, the deterministic/non-deterministic split) and post its findings as visible evidence on the PR.
4. Branch protection on `main`: merge blocked unless the test check passes and a human has approved.

## 3. Non-goals, and the runner decision

- **No self-hosted VM.** The repo is public (verified: `private: false` via the GitHub API). GitHub's own guidance is that self-hosted runners on public repositories are a security anti-pattern — anyone can open a PR, and a malicious PR's workflow can execute code on whatever runner picks it up. On a GitHub-hosted runner that's a throwaway VM; on a self-hosted one, it's a machine you actually own, potentially exposing any credentials installed on it (e.g. an `ANTHROPIC_API_KEY`). GitHub-hosted runners are also free and unlimited for public repos, so there's no cost tradeoff pushing toward self-hosted either. Decided with the user: GitHub-hosted.
- **No auto-merge.** Human approval is always required — this isn't a limitation to work around, it's the point (mirrors the whole project's human-review-gate thesis).
- **No "implementer" role for Claude Code in CI** — reviewer/evidence-generator only, decided with the user. An implementer role (Claude Code writing the use-case code itself as part of automation) is a plausible future iteration, not this phase.
- **No pluggable "add any domain" meta-system.** One concrete new use case, exercised through the real pipeline — not a generic domain-generator.

## 4. Design

### 4.1 Headless Claude Code in CI — verified mechanics

Confirmed via Anthropic's docs (not guessed):

- Official action: **`anthropics/claude-code-action@v1`** (github.com/anthropics/claude-code-action) — the standard, Anthropic-maintained way to run Claude Code against a PR in Actions. Prefer this over hand-rolling `npm install -g @anthropic-ai/claude-code` + raw `claude -p` calls, unless there's a specific reason to practice the raw CLI mechanics instead (see open question 2).
- Headless invocation, if hand-rolled: `claude -p "prompt"`, with `--output-format text|json|stream-json`.
- Auth in CI: `ANTHROPIC_API_KEY` (a Console API key), passed as a GitHub Actions secret. `--bare` mode (recommended for CI, no interactive startup overhead) specifically requires `ANTHROPIC_API_KEY` — the alternative `CLAUDE_CODE_OAUTH_TOKEN` does **not** work with `--bare`.
- Read-only restriction for this job: `--allowedTools Read` (or `--permission-mode dontAsk`) — consistent with this project's existing pattern of declaring an explicit tool allowlist per skill (Phase 1). This job reviews, it never edits.

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    prompt: |
      Review this PR's diff against CLAUDE.md's conventions and this
      repo's established patterns (skill template, deterministic vs.
      non-deterministic split, allowed-tools scoping). Flag violations.
    claude_args: |
      --allowedTools Read
      --output-format json
      --bare
```

**Important secret-hygiene note given the earlier incident:** this `ANTHROPIC_API_KEY` GitHub Actions secret is a separate, repo-level credential store — not the same thing as `claude-sdk-audit/.env`. Set it directly through GitHub's Settings → Secrets UI when the time comes; don't copy-paste a key between files as an intermediate step.

### 4.2 Test job

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - name: Phase 1 tests
        run: python3 tools/test_query_deterministic_rule.py -v
      - uses: astral-sh/setup-uv@v3
      - name: Phase 2 tests
        working-directory: claude-sdk-audit
        run: |
          uv sync
          uv run pytest -v
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

Phase 2's two live-API tests already `skipif` automatically when no usable key is present (built into `test_nondeterministic.py` in Phase 2) — so whether this job actually exercises them or not is purely a function of whether the secret is wired in here. See open question 1.

### 4.3 Branch protection

Configured in GitHub's Settings → Branches (not a YAML file): require the `test` status check to pass, require at least one approving review, before the merge button is enabled. This is a one-time manual setup step in the GitHub UI, not something scriptable from this repo's files.

### 4.4 Proving it end-to-end

Add one real new audit use case on a feature branch (candidate: pre-dialysis or post-dialysis documentation adequacy, non-deterministic, following the same skill template as `intradialytic-hypotension-review` — or finally fleshing out the long-deferred `SYN-ICHD-02`/`03` placeholders from Phase 1). Open the PR, watch both jobs run, review the evidence, approve, merge. This is the actual deliverable of this phase — a working example of the pipeline, not just the workflow file sitting unused.

## 5. What I can't do from here

No `gh` CLI is installed/authenticated in this environment, so branch protection rules and the `ANTHROPIC_API_KEY` repo secret will need to be set up by the user through the GitHub web UI — I can give exact click-by-click steps when we get there, or the user can install and authenticate `gh` CLI here if they'd rather I do more of it directly (open question 5).

## 6. Open questions for review

1. Should `ANTHROPIC_API_KEY` be wired into the `test` job too (spends real API cost on every PR, exercises Phase 2's live tests for real) or left out there (free, those 2 tests just auto-skip in CI, less coverage)? The `claude-review` job needs the secret regardless — this question is specifically about the `test` job.
2. Confirm using the official `anthropics/claude-code-action@v1` rather than hand-rolling the npm-install + raw CLI approach — any reason to prefer hand-rolling (e.g. wanting the raw CLI mechanics as a distinct learning point)?
3. What should the new use case/rule actually be — pre/post-dialysis documentation (new), or finally fleshing out `SYN-ICHD-02`/`03` (existing placeholders), or something else?
4. Branch naming convention preference (e.g. `feature/<name>`)?
5. `gh` CLI setup here, or web-UI steps handed to the user for the parts I can't reach (secrets, branch protection)?
